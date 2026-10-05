#!/usr/bin/env python3
"""
expb_audit.py: checks on the harness verdicts behind EXPB_REPORT.md and REPLAY_REPORT.md (AgentHazard rebuttal).

It never edits the experiment's scores, summaries, plan or reports. It writes only under expb/out/audit/, plus the
harness's own logs for the runs that `rescore` starts.

Run from /workspaces/mini-swe-agent/expb with .venv-expb active:
  python expb_audit.py audit               no Docker, a few minutes: writes out/audit/AUDIT_REPORT.md and suspects.json
  python expb_audit.py rescore --dry-run   what would be rescored, with a rough time estimate
  python expb_audit.py rescore             Docker: rescores every suspect in fresh containers under new run IDs. A
                                           verdict counts as changed only when two clean rescorings agree. Resumable:
                                           rerun the same command. `touch out/audit/STOP` stops it after the current
                                           harness run
  python expb_audit.py reports             no Docker: rebuilds both reports with expb.py's own code from the recorded
                                           and the corrected verdicts, under the plan's byte-for-byte rule and the
                                           reclassified one, and recomputes 9VzP 1a
"""
import argparse
import collections
import datetime
import difflib
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
import expb  # noqa: E402  the pre-registered analysis code, in the same folder

AUDIT = expb.OUT / "audit"
SCORES = {"expb": ("scores.json", "expb"), "replay": ("replay/scores.json", "replay")}  # file in out/, harness tag
TAG = "audit"  # harness tag (model_name_or_path) of the rescoring runs
MAX_TRIES = 4  # harness attempts per suspect, clean or not
DISK_RE = re.compile(rb"no space left on device|errno 28|enospc", re.I)
FM_NO_RESOLVING = ["django__django-14752", "django__django-16139", "django__django-16595", "pydata__xarray-4094",
                   "pytest-dev__pytest-7432", "scikit-learn__scikit-learn-13142", "sphinx-doc__sphinx-8721",
                   "sympy__sympy-11618"]  # FINAL_MEASURES.txt, 9VzP 1a: resolved runs with no resolving state
COMMITS = ["d6a95a2", "ef34ac8", "c2e7d3f", "5650ae8", "6ce1030", "5404951", "4484a7b", "5c286e9", "HEAD"]
LINES = []


def out(s=""):
    print(s, flush=True)
    LINES.append(s)


def utc(t):
    if not t:
        return "-"
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def frac(k, n):
    if not n:
        return f"{k}/0"
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.1f}%, 95% CI {100 * lo:.1f}-{100 * hi:.1f})"


# ============================================================================ the data, read through expb.py
def load_scores(exp, root=None):
    return expb.read_json((root or expb.OUT) / SCORES[exp][0], {}) or {}


def summaries():
    res = {}
    for p in sorted((expb.OUT / "replay" / "runs").glob("*.summary.json")):
        s = expb.read_json(p)
        if s and s.get("instance_id"):
            res[s["instance_id"]] = s
    return res


def main_info():
    idx = expb.main_run_index()
    fin = {e["iid"]: e for e in idx.values() if e.get("status") in expb.FINISHED and e.get("iid")}
    outs = expb.main_outcomes(list(fin))
    return fin, {i: expb.main_outcome(e, outs) for i, e in fin.items()}


def sample_ids():
    return {t["instance_id"] for t in (expb.read_json(expb.OUT / "tasks.json") or [])}


def inspect_report(rp, iid):
    """What a harness report directory says: report present and readable, its verdict and test counts, and whether
    its logs mention a full disk."""
    st = dict(exists=rp.exists(), parses=False, logs=False, disk=False, f2p=None, p2p=None, resolved=None,
              applied=None)
    if st["exists"]:
        try:
            rj = json.loads(rp.read_text())[iid]
            st.update(parses=True, resolved=rj.get("resolved"), applied=rj.get("patch_successfully_applied"))
            ts = rj.get("tests_status") or {}
            for key, name in (("FAIL_TO_PASS", "f2p"), ("PASS_TO_PASS", "p2p")):
                v = ts.get(key)
                if isinstance(v, dict):
                    st[name] = (len(v.get("success") or []), len(v.get("failure") or []))
        except Exception:
            pass
    for name in ("run_instance.log", "test_output.txt"):
        p = rp.parent / name
        if p.exists():
            st["logs"] = True
            try:
                if DISK_RE.search(p.read_bytes()):
                    st["disk"] = True
            except OSError:
                pass
    return st


def record_report(exp, iid, rec):
    rid = rec.get("run_id")
    if rid:
        st = inspect_report(expb.report_path(rid, SCORES[exp][1], iid), iid)
    else:
        st = dict(exists=False, parses=False, logs=False, disk=False, f2p=None, p2p=None, resolved=None, applied=None)
    st["run_id"] = rid
    return st


def crash_runs(prior):
    """Harness runs in flight when expb.py stopped on a full disk (read from out/all.log), plus the `prior` runs
    logged before each. Returns (run IDs, [(log line, run IDs, last batch line)])."""
    p = expb.OUT / "all.log"
    if not p.exists():
        return set(), []
    recent, batch, ids, events = [], "", set(), []
    for no, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
        m = re.search(r"score: (\S+): \d+ patches", line)
        if m:
            recent = (recent + [m.group(1)])[-(prior + 1):]
            continue
        b = re.search(r"((?:replay )?batch \d+/\d+): (\[.*\])", line)
        if b:
            batch = f"{b.group(1)}: {b.group(2)}"
            continue
        if "No space left on device" in line or "Errno 28" in line:
            events.append((no, list(recent), batch))
            ids.update(recent)
            recent = []
    return ids, events


# ============================================================================ faithfulness, from content
def chunks(patch):
    res = {}
    for c in re.split(r"(?m)^(?=diff --git a/)", patch or ""):
        m = re.match(r"diff --git a/(\S+) b/", c)
        if m:
            res[m.group(1)] = c.strip("\n").splitlines()
    return res


def index_hashes(lines):
    return [m.groups() for m in (re.match(r"index (\w+)\.\.(\w+)", ln) for ln in lines) if m]


def prefix_equal(a, b):
    return len(a) == len(b) and all(x.startswith(y) or y.startswith(x) for p, q in zip(a, b) for x, y in zip(p, q))


def code_identical(final, recorded):
    """The reclassification's test: same files, every non-index line equal, each index hash a prefix of the other."""
    rc, fc = chunks(recorded), chunks(final)
    return bool(rc) and set(rc) == set(fc) and all(
        [ln for ln in rc[f] if not ln.startswith("index ")] == [ln for ln in fc[f] if not ln.startswith("index ")]
        and prefix_equal(index_hashes(rc[f]), index_hashes(fc[f])) for f in rc)


def is_byte(s):
    return bool(s.get("submission_sha")) and s.get("submission_sha") == s.get("recorded_submission_sha")


def recount(s, fin):
    """'limit', 'byte', 'code only', 'differs' or 'unknown', recomputed from content rather than from the flags."""
    if s.get("main_status") == "LimitsExceeded":
        return "limit"
    if is_byte(s):
        return "byte"
    e, sts = fin.get(s.get("instance_id")), s.get("states") or []
    if not e or not sts:
        return "unknown"
    rec = ((expb.read_json(e["file"], {}) or {}).get("info") or {}).get("submission") or ""
    final = (s.get("patches") or {}).get(sts[-1].get("patch_id") or "", "")
    return "code only" if code_identical(final, rec) else "differs"


# ============================================================================ git, read-only
def git(*args, data=None):
    try:
        r = subprocess.run(["git", *args], cwd=expb.REPO_ROOT, input=data, capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def git_text(*args):
    o = git(*args)
    return o.decode(errors="replace").strip() if o is not None else None


def tree_blobs(commit, path):
    res = {}
    for line in (git_text("ls-tree", "-r", commit, "--", path) or "").splitlines():
        meta, _, name = line.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob":
            res[name] = parts[2]
    return res


def cat_blobs(shas):
    res, o, i = {}, (git("cat-file", "--batch", data=("\n".join(shas) + "\n").encode()) or b"") if shas else b"", 0
    while i < len(o):
        j = o.find(b"\n", i)
        if j < 0:
            break
        head = o[i:j].decode(errors="replace").split()
        i = j + 1
        if len(head) < 3 or head[-1] == "missing":
            continue
        size = int(head[2])
        res[head[0]] = o[i:i + size]
        i += size + 1
    return res


# ============================================================================ the seeded draw of extra failed runs
def outcomes_at(fin, cutoff=None, original_only=False):
    """The main run's outcome per finished run, as expb.main_outcome gives it, optionally ignoring 5.0.2 re-score
    reports written after `cutoff` (a Unix time), or ignoring the re-score altogether."""
    res = {}
    for iid, e in fin.items():
        if e.get("status") == "LimitsExceeded":
            res[iid] = False
            continue
        v = None
        for name in (() if original_only else ("rescore_v502",)) + ("original",):
            d = expb.MAIN_RUN_REPORTS.get(name)
            p = d / iid / "report.json" if d else None
            if p is None or not p.exists():
                continue
            if name == "rescore_v502" and cutoff is not None and p.stat().st_mtime > cutoff:
                continue
            v = bool(((expb.read_json(p, {}) or {}).get(iid) or {}).get("resolved"))
            break
        res[iid] = v
    return res


def draw(fin, samp, oc):
    """expb.replay_units('design'): the extra failed runs, drawn with seed SEED + 1 from the sorted pool."""
    pool = sorted(i for i in fin if i not in samp and oc.get(i) is False)
    return random.Random(expb.SEED + 1).sample(pool, min(expb.REPLAY_EXTRA_FAILED, len(pool))), len(pool)


# ============================================================================ audit
def cmd_audit(args):
    code_hash = expb.file_sha256(Path(expb.__file__).resolve())[:16]
    out("# Audit of the verdicts behind EXPB_REPORT.md and REPLAY_REPORT.md")
    out("")
    out(f"Written {utc(time.time())} by `expb_audit.py audit` (read-only). expb.py SHA-256 {code_hash} (the "
        "pre-registered code is 1ee1d1435955ed95).")
    fin, mres = main_info()
    samp, R, rsc = sample_ids(), summaries(), load_scores("replay")
    sus = {exp: collections.defaultdict(dict) for exp in SCORES}

    def flag(exp, iid, pid, why):
        whys = sus[exp][iid].setdefault(pid, [])
        if why not in whys:
            whys.append(why)

    def res(iid, pid):
        if not pid:
            return False
        r = (rsc.get(iid) or {}).get(pid)
        return None if r is None else r.get("resolved")

    # ------------------------------------------------------------------ 1
    out("")
    out("## 1. Every recorded verdict against its harness report and logs")
    out("")
    crash_ids, events = crash_runs(args.prior_runs)
    for no, ids, batch in events:
        out(f"- all.log line {no}: expb.py stopped on a full disk. Harness runs in flight or just before: "
            f"{', '.join(ids) or 'none logged'}" + (f". Last batch line: {batch}" if batch else ""))
    if not events:
        out("- all.log records no disk-full stop (or is missing).")
    for exp in SCORES:
        sc = load_scores(exp)
        recs = [(iid, pid, rec, record_report(exp, iid, rec)) for iid in sorted(sc) for pid, rec in sorted(sc[iid].items())]
        c, ex, n, whys_of, bad_runs = collections.Counter(), collections.defaultdict(list), len(recs), {}, set()
        for iid, pid, rec, st in recs:
                whys = []
                if not st["run_id"]:
                    whys.append("no run ID recorded")
                elif not st["exists"]:
                    whys.append("report.json missing")
                elif not st["parses"]:
                    whys.append("report.json unreadable")
                if rec.get("applied") is None:
                    whys.append("applied unknown (an empty or unreadable report is recorded as unresolved)")
                if st["disk"]:
                    whys.append("disk-full error in the harness logs")
                if st["run_id"] in crash_ids:
                    whys.append("scored around a disk-full stop")
                if st["parses"] and st["resolved"] is not None and bool(st["resolved"]) != bool(rec.get("resolved")):
                    whys.append("recorded verdict disagrees with its report")
                whys_of[(iid, pid)] = whys
                if whys:
                    bad_runs.add(st["run_id"])
        for iid, pid, rec, st in recs:
                whys = whys_of[(iid, pid)]
                if st["exists"] and not st["logs"]:
                    c["(report without harness logs)"] += 1
                if st["p2p"] and st["p2p"][0] == 0 and st["p2p"][1] > 0:
                    c["(every PASS_TO_PASS test failed)"] += 1
                    if not st["logs"]:
                        whys.append("every PASS_TO_PASS test failed, and no logs to check why")
                    elif not whys and st["run_id"] in bad_runs:
                        whys.append("every PASS_TO_PASS test failed, in a harness run with other problems")
                for w in whys:
                    c[w] += 1
                    flag(exp, iid, pid, w)
                    if len(ex[w]) < 12:
                        ex[w].append(f"{iid} {pid} (run {st['run_id']}, recorded {rec.get('resolved')})")
        out(f"- {exp} ({SCORES[exp][0]}): {n} verdicts. " +
            ("; ".join(f"{w}: {k}" for w, k in sorted(c.items())) if c else "No problem found."))
        for w, items in ex.items():
            out(f"  - {w}: " + "; ".join(items) + (" ..." if c[w] > len(items) else ""))

    # ------------------------------------------------------------------ 2
    out("")
    out("## 2. Resolved sampled runs whose replay never shows a resolving state")
    out("")
    out("Each run's final code is what the main run submitted (byte for byte, or code-identical), and the main run "
        "resolved the task, so scored correctly its final state should resolve.")
    found = []
    for iid in sorted(samp):
        s = R.get(iid)
        if not s or s.get("faithful") is not True or mres.get(iid) is not True:
            continue
        eds = expb.source_edits(s.get("states") or [])
        vals = [res(iid, st["patch_id"]) for st in eds]
        if True in vals:
            continue
        found.append(iid)
        fpid = eds[-1]["patch_id"] if eds else ""
        rec = (rsc.get(iid) or {}).get(fpid) or {}
        st = record_report("replay", iid, rec) if rec else None
        rep = ("no verdict recorded" if not rec else
               f"run {st['run_id']}, recorded {rec.get('resolved')}, applied {rec.get('applied')}, report "
               f"{'readable' if st['parses'] else 'missing or unreadable'}, PASS_TO_PASS (passed, failed) "
               f"{st['p2p']}, disk error in logs {st['disk']}")
        out(f"- {iid}: {recount(s, fin)}; flags faithful={s.get('faithful')}, faithful_strict="
            f"{s.get('faithful_strict', 'absent')}; verdicts at its source edits {vals}; final state: {rep}")
        for pid, txt in (s.get("patches") or {}).items():
            if pid and (txt or "").strip():
                flag("replay", iid, pid, "resolved run with no resolving state")
    both = set(found) & set(FM_NO_RESOLVING)
    out(f"- Found {len(found)}; FINAL_MEASURES listed {len(FM_NO_RESOLVING)}; in both {len(both)}; only here "
        f"{sorted(set(found) - both)}; only in FINAL_MEASURES {sorted(set(FM_NO_RESOLVING) - both)}.")

    # ------------------------------------------------------------------ 3
    out("")
    out("## 3. Faithfulness recounted from the replays' content, not their flags")
    out("")
    cls = {iid: recount(s, fin) for iid, s in R.items()}
    cnt = collections.Counter(cls.values())
    out(f"- {len(R)} replays. Byte for byte {cnt['byte']}; code-identical only {cnt['code only']}; code differs "
        f"{cnt['differs']}; ended at a limit {cnt['limit']}; could not check {cnt['unknown']}.")
    out(f"- Flags: faithful {sum(s.get('faithful') is True for s in R.values())}, of which flagged as reclassified "
        f"{sum(s.get('faithful') is True and s.get('faithful_strict') is False for s in R.values())}. The handout "
        "says 75 byte for byte + 12 reclassified = 87.")
    bad = 0
    for iid, s in sorted(R.items()):
        k, f, fs = cls[iid], s.get("faithful"), s.get("faithful_strict", "absent")
        why = None
        if k == "byte" and (f is not True or fs is False):
            why = "byte for byte, but the flags say otherwise"
        elif k == "code only" and not (f is True and fs is False):
            why = ("counted as byte for byte (no faithful_strict flag) but is not" if f is True
                   else "code-identical but not counted as faithful")
        elif k == "differs" and f is True:
            why = "counted as faithful but its code differs"
        elif k == "limit" and f is not None:
            why = "ended at a limit but carries a faithfulness verdict"
        if why:
            bad += 1
            out(f"  - {iid}: {why}. faithful={f}, faithful_strict={fs}, attempt {s.get('attempt')}, replay started "
                f"{utc(s.get('started'))}, main run {'resolved' if mres.get(iid) else 'failed'}, "
                f"{'sampled' if iid in samp else 'extra'}")
    if not bad:
        out("- The flags agree with the content for every replay.")
    for label, keep in (("as flagged (faithful = true)", lambda i, s: s.get("faithful") is True),
                        ("byte for byte only (the plan's rule)", lambda i, s: cls[i] == "byte")):
        failed = [i for i, s in R.items() if keep(i, s) and mres.get(i) is False]
        early = [i for i in failed if any(res(i, st["patch_id"])
                                          for st in expb.source_edits(R[i].get("states") or [])[:-1])]
        out(f"- R3 from the recorded verdicts, {label}: {frac(len(early), len(failed))}: {sorted(early)}")
    for iid, s in R.items():
        if cls[iid] == "code only" and mres.get(iid) is False:
            for pid, txt in (s.get("patches") or {}).items():
                if pid and (txt or "").strip():
                    flag("replay", iid, pid, "reclassified failed run (a rescue could hide here)")

    # ------------------------------------------------------------------ 4
    out("")
    out("## 4. The replay summaries in each commit")
    out("")
    if git_text("rev-parse", "--git-dir") is None:
        out("- git is not available here; skipped.")
    else:
        now = {i: (s.get("faithful"), s.get("faithful_strict", "absent")) for i, s in R.items()}
        cache = {}
        out("| Commit | Date (UTC) | Parents | Summaries | Faithful | Flagged reclassified | Byte for byte | "
            "Flags differ from the working tree | Message |")
        out("|---|---|---|---|---|---|---|---|---|")
        for c in args.commits:
            full = git_text("rev-parse", "--verify", "--quiet", c + "^{commit}")
            if not full:
                out(f"| {c} | not in this repository | | | | | | | |")
                continue
            meta = (git_text("log", "-1", "--format=%ct%x09%P%x09%s", full) or "").split("\t")
            files = {p: b for p, b in tree_blobs(full, "expb/out/replay/runs").items() if p.endswith(".summary.json")}
            for b, raw in cat_blobs([b for b in set(files.values()) if b not in cache]).items():
                try:
                    s = json.loads(raw)
                    cache[b] = (s.get("instance_id"), s.get("faithful"), s.get("faithful_strict", "absent"), is_byte(s))
                except ValueError:
                    cache[b] = None
            rows = [cache[b] for b in files.values() if cache.get(b)]
            diff = sorted(r[0] for r in rows if now.get(r[0]) != (r[1], r[2]))
            when = utc(int(meta[0])) if meta and meta[0].isdigit() else "-"
            parents = " ".join(x[:7] for x in meta[1].split()) if len(meta) > 1 else ""
            label = full[:7] if full.startswith(c) else f"{c} ({full[:7]})"
            out(f"| {label} | {when} | {parents} | {len(rows)} | {sum(r[1] is True for r in rows)} | "
                f"{sum(r[1] is True and r[2] is False for r in rows)} | {sum(r[3] for r in rows)} | "
                f"{', '.join(diff) if diff else '-'} | {meta[2][:60] if len(meta) > 2 else ''} |")
        parents = (git_text("log", "-1", "--format=%P", args.merge) or "").split()
        out("")
        if len(parents) == 2:
            for side, par in (("its first parent (the Codespace's side)", parents[0]),
                              ("its second parent (GitHub's side)", parents[1])):
                ns = [ln for ln in (git_text("diff", "--name-status", par, args.merge, "--", "expb/out") or "")
                      .splitlines() if ln.strip()]
                out(f"- Merge {args.merge} changed {len(ns)} file(s) under expb/out relative to {side}"
                    + (": " + "; ".join(ns[:12]) + (" ..." if len(ns) > 12 else "") if ns else "."))
            for name in ("expb/out/scores.json", "expb/out/replay/scores.json"):
                a, b = tree_blobs(parents[0], name).get(name), tree_blobs(args.merge, name).get(name)
                if a and b and a != b:
                    bl = cat_blobs([a, b])
                    A, B = json.loads(bl[a]), json.loads(bl[b])
                    ch = sorted((i, p) for i in set(A) | set(B) for p in set(A.get(i, {})) | set(B.get(i, {}))
                                if (A.get(i, {}).get(p) or {}).get("resolved") != (B.get(i, {}).get(p) or {}).get("resolved"))
                    out(f"- {name}: the merge changed {len(ch)} verdict(s) relative to the first parent: {ch[:12]}")
                elif a and b:
                    out(f"- {name}: unchanged by the merge.")
        else:
            out(f"- {args.merge} is not a merge commit in this repository; merge check skipped.")

    # ------------------------------------------------------------------ 5
    out("")
    out("## 5. The extra failed runs: is the seeded draw reproducible?")
    out("")
    extras = sorted(set(R) - samp)
    t_pre = git_text("log", "-1", "--format=%ct", args.prereg)
    T = int(t_pre) if t_pre and t_pre.isdigit() else None
    rdir = expb.MAIN_RUN_REPORTS.get("rescore_v502")
    mts = sorted(p.stat().st_mtime for p in rdir.glob("*/report.json")) if rdir and rdir.exists() else []
    out(f"- Replayed {len(R)} runs, {len(extras)} outside the sample (the plan: {expb.REPLAY_EXTRA_FAILED}).")
    out(f"- 5.0.2 re-score reports on disk: {len(mts)}" + (f", file times {utc(mts[0])} to {utc(mts[-1])}" if mts else "")
        + (f"; written after the pre-registration commit ({utc(T)}): {sum(m > T for m in mts)}" if T else
           "; the pre-registration commit was not found") + ". File times hold only if the files were never copied.")
    for label, cutoff, orig in (("outcomes as they are now (how the replay drew them)", None, False),
                                ("outcomes as of the pre-registration commit", T, False),
                                ("the original harness's outcomes only", None, True)):
        if cutoff is None and label.startswith("outcomes as of"):
            continue
        oc = outcomes_at(fin, cutoff, orig)
        drawn, n = draw(fin, samp, oc)
        same = set(drawn) == set(extras)
        out(f"- {label}: pool of {n} failed runs; the seeded draw {'matches the replayed set' if same else 'DIFFERS'}"
            + ("" if same else f" (drawn, not replayed: {sorted(set(drawn) - set(extras))[:8]}; replayed, not "
                                f"drawn: {sorted(set(extras) - set(drawn))[:8]})"))

    # ------------------------------------------------------------------ 6
    out("")
    out("## 6. Suspects to rescore")
    out("")
    why = collections.Counter(w for exp in sus for v in sus[exp].values() for ws in v.values() for w in ws)
    for exp in SCORES:
        out(f"- {exp}: {sum(len(v) for v in sus[exp].values())} patches in {len(sus[exp])} tasks")
    out("- By reason, both experiments (a patch can have several):")
    for w, k in why.most_common():
        out(f"  - {w}: {k}")
    expb.write_json(AUDIT / "suspects.json", {"written": time.time(), "suspects": {e: dict(d) for e, d in sus.items()}})
    (AUDIT / "AUDIT_REPORT.md").write_text("\n".join(LINES) + "\n")
    print(f"\nwrote {AUDIT / 'AUDIT_REPORT.md'} and {AUDIT / 'suspects.json'}. Next: python expb_audit.py rescore --dry-run")


# ============================================================================ rescore
def patch_texts():
    T = {exp: collections.defaultdict(dict) for exp in SCORES}
    for arm in expb.ARMS:
        for p in (expb.OUT / "runs" / arm).glob("*.summary.json"):
            s = expb.read_json(p) or {}
            iid = s.get("instance_id")
            if not iid:
                continue
            for pid, txt in (s.get("patches") or {}).items():
                if pid and (txt or "").strip():
                    T["expb"][iid][pid] = txt
            if s.get("submission_id") and (s.get("submission") or "").strip():
                T["expb"][iid][s["submission_id"]] = s["submission"]
    for iid, s in summaries().items():
        for pid, txt in (s.get("patches") or {}).items():
            if pid and (txt or "").strip():
                T["replay"][iid][pid] = txt
    return T


def verdict(it):
    """(verdict or None, status) from an item's clean rescorings (a report that parsed, with no disk error)."""
    good = [a["resolved"] for a in it["attempts"] if a["ok"] and not a["disk"]]
    if not good:
        return None, ("unscored" if len(it["attempts"]) < MAX_TRIES else "could not be scored")
    if good[0] == it["old"]:
        return it["old"], "confirmed"
    if len(good) == 1:
        return None, "needs a second scoring"
    v, n = collections.Counter(good).most_common(1)[0]
    if n < 2:
        return None, "needs a third scoring"
    return v, ("changed" if v != it["old"] else "confirmed") + (" (flaky)" if len(set(good)) > 1 else "")


def needs_work(it):
    return verdict(it)[1] in ("unscored", "needs a second scoring", "needs a third scoring") and \
        len(it["attempts"]) < MAX_TRIES


def plan_runs(todo, per_run):
    """Harness runs of at most per_run tasks, a task at most once per run. Each group of tasks is finished before the
    next starts, so their images are still cached for their later patches."""
    by = collections.defaultdict(list)
    for it in sorted(todo, key=lambda x: (x["iid"], x["exp"], x["pid"])):
        by[it["iid"]].append(it)
    iids, runs = sorted(by), []
    for i in range(0, len(iids), per_run):
        chunk = iids[i:i + per_run]
        for r in range(max(len(by[x]) for x in chunk)):
            runs.append([by[x][r] for x in chunk if len(by[x]) > r])
    return runs


def ensure_disk(min_gb):
    if expb.free_gb() >= min_gb:
        return True
    expb.docker("container", "prune", "-f")
    expb.docker("image", "prune", "-af", timeout=1800)
    for _ in range(40):
        if expb.free_gb() >= min_gb:
            return True
        time.sleep(15)
    return False


def summarize(state):
    c, rows = collections.Counter(), []
    for it in sorted(state.values(), key=lambda x: (x["exp"], x["iid"], x["pid"])):
        v, st = verdict(it)
        c[(it["exp"], st)] += 1
        if st != "confirmed":
            scored = [a["resolved"] if a["ok"] and not a["disk"] else "no clean result" for a in it["attempts"]]
            rows.append(f"- {it['exp']} {it['iid']} {it['pid']}: recorded {it['old']}; {st}"
                        f"{'' if v is None else ' to ' + str(v)}; rescorings {scored}; suspect because: "
                        f"{'; '.join(it['reasons'])}")
    L = ["# Rescoring of the suspect verdicts", "", f"Written {utc(time.time())} by `expb_audit.py rescore`.", ""]
    for exp in SCORES:
        L.append(f"- {exp}: " + (", ".join(f"{st} {n}" for (e, st), n in sorted(c.items()) if e == exp) or "none"))
    L += ["", "Every item not listed below was confirmed: its first clean rescoring gave the recorded verdict.", ""]
    L += rows or ["- none"]
    text = "\n".join(L) + "\n"
    (AUDIT / "RESCORE_SUMMARY.md").write_text(text)
    print(text)
    print(f"wrote {AUDIT / 'RESCORE_SUMMARY.md'}. Next: python expb_audit.py reports")


def cmd_rescore(args):
    data = expb.read_json(AUDIT / "suspects.json")
    if not data:
        raise SystemExit("out/audit/suspects.json not found: run `python expb_audit.py audit` first")
    texts, path = patch_texts(), AUDIT / "rescore.json"
    state = expb.read_json(path, {}) or {}
    rec = {exp: load_scores(exp) for exp in SCORES}
    no_text = []
    for exp, by in data["suspects"].items():
        for iid, pids in by.items():
            for pid, whys in pids.items():
                key = f"{exp}|{iid}|{pid}"
                if key in state:
                    state[key]["reasons"] = whys
                elif texts[exp].get(iid, {}).get(pid):
                    state[key] = dict(exp=exp, iid=iid, pid=pid, reasons=whys, attempts=[],
                                      old=((rec[exp].get(iid) or {}).get(pid) or {}).get("resolved"))
                else:
                    no_text.append(key)

    def pending():
        return [it for it in state.values() if (not args.only or it["exp"] == args.only) and needs_work(it)]

    per_exp = collections.Counter(it["exp"] for it in state.values())
    out(f"{len(state)} suspects ({', '.join(f'{e} {per_exp[e]}' for e in SCORES)}); {len(pending())} still to score"
        + (f"; {len(no_text)} have no patch text and cannot be rescored: {no_text[:6]}" if no_text else ""))
    if args.dry_run:
        todo = pending()
        mins = len(todo) * args.sec_per_patch / max(1, args.workers) / 60
        out(f"First pass: {len(todo)} patches in {len(plan_runs(todo, args.per_run))} harness runs, roughly "
            f"{mins:.0f}-{2 * mins:.0f} minutes. A changed verdict costs one more scoring to confirm.")
        for w, k in collections.Counter(w for it in todo for w in it["reasons"]).most_common():
            out(f"  - {w}: {k}")
        return
    expb.write_json(path, state)
    stop, work, n_run = AUDIT / "STOP", AUDIT / "work", 0
    with expb.Lock("audit/rescore.lock"):
        while True:
            todo = pending()
            if not todo:
                break
            runs = plan_runs(todo, args.per_run)
            out(f"{time.strftime('%H:%M:%S')} {len(todo)} patch(es) to score in {len(runs)} harness run(s); "
                f"{expb.free_gb():.1f} GB free")
            for group in runs:
                if stop.exists():
                    out("out/audit/STOP found: stopping. Delete it and rerun the same command to resume.")
                    return summarize(state)
                if not ensure_disk(args.min_free_gb):
                    out(f"only {expb.free_gb():.1f} GB free after pruning Docker: stopping. Free space and rerun.")
                    return summarize(state)
                n_run += 1
                run_id = f"aud{time.strftime('%m%d%H%M%S')}x{n_run:03d}"
                preds = [{"instance_id": it["iid"], "model_name_or_path": TAG,
                          "model_patch": texts[it["exp"]][it["iid"]][it["pid"]]} for it in group]
                expb.run_harness(preds, run_id, work, args.workers)
                for it in group:
                    st = inspect_report(expb.report_path(run_id, TAG, it["iid"]), it["iid"])
                    ok = st["parses"] and st["resolved"] is not None
                    it["attempts"].append(dict(run_id=run_id, resolved=bool(st["resolved"]) if ok else None,
                                               applied=st["applied"], ok=ok, disk=st["disk"], p2p=st["p2p"],
                                               time=round(time.time())))
                expb.write_json(path, state)
    summarize(state)


# ============================================================================ reports
def corrected(original):
    sc, changes = json.loads(json.dumps(original)), []
    for it in (expb.read_json(AUDIT / "rescore.json", {}) or {}).values():
        v, st = verdict(it)
        if st.startswith("changed"):
            sc[it["exp"]].setdefault(it["iid"], {}).setdefault(it["pid"], {}).update(resolved=v, audit=st)
            changes.append((it["exp"], it["iid"], it["pid"], it["old"], v, st))
    return sc, changes


def mirror(name, sc, demote):
    """A stand-in for out/ made of symlinks, with both score files replaced and, under the plan's rule, the replays
    that are not byte for byte marked unfaithful. The real out/ is only read."""
    real, root = expb.OUT, AUDIT / "roots" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for p in real.iterdir():
        if p.name not in ("audit", "scores.json", "replay"):
            os.symlink(p, root / p.name)
    expb.write_json(root / "scores.json", sc["expb"])
    rr = root / "replay"
    rr.mkdir()
    for p in (real / "replay").iterdir():
        if p.name not in ("scores.json", "runs"):
            os.symlink(p, rr / p.name)
    expb.write_json(rr / "scores.json", sc["replay"])
    (rr / "runs").mkdir()
    for p in (real / "replay" / "runs").iterdir():
        iid = p.name[:-len(".summary.json")] if p.name.endswith(".summary.json") else None
        if iid in demote:
            s = expb.read_json(p)
            s.update(faithful=False, audit_note="not byte for byte: unfaithful under the plan's rule")
            expb.write_json(rr / "runs" / p.name, s)
        else:
            os.symlink(p, rr / "runs" / p.name)
    return root


def build_reports(root, with_b=True):
    saved = expb.OUT
    expb.OUT = root
    try:
        b, r = [], []
        if with_b:
            expb.report_b(b)
        expb.report_replay(r)
    finally:
        expb.OUT = saved
    return "\n".join(b) + "\n", "\n".join(r) + "\n"


def u4(scores_r, keep):
    """9VzP 1a exactly as FINAL_MEASURES computed it, for a given set of verdicts and faithfulness rule."""
    fl = [e for e in expb.main_run_index().values() if e.get("status") in expb.FINISHED and e.get("iid")]
    outs, samp = expb.main_outcomes([e["iid"] for e in fl]), sample_ids()
    after, calls, none = [], [], []
    for e in fl:
        iid = e["iid"]
        if iid not in samp or expb.main_outcome(e, outs) is not True:
            continue
        s = expb.read_json(expb.replay_paths(iid, expb.OUT / "replay"))
        if not s or not keep(s):
            continue
        d = expb.read_json(e["file"], {}) or {}
        cmds = [x for _, acts in expb.recorded_calls(d) for x in acts
                if not (x["not_executed"] and expb.MAGIC not in x["command"])]
        sts = s.get("states") or []
        if len(sts) != len(cmds):
            continue
        first = next((t for t in sts if t.get("edit") and
                      ((scores_r.get(iid) or {}).get(t["patch_id"]) or {}).get("resolved")), None)
        if first is None:
            none.append(iid)
        else:
            after.append((len(sts) - 1 - first["a"], len(sts)))
            calls.append((s["n_calls"] - first["step"], s["n_calls"]))

    def share(v):
        if not v:
            return "n/a"
        return (f"{100 * sum(a for a, _ in v) / sum(n for _, n in v):.1f}% of all, median per run "
                f"{100 * statistics.median(a / n for a, n in v):.1f}%")

    return (f"{len(after)} of {len(after) + len(none)} runs have a resolving state; commands after it {share(after)}; "
            f"model calls after it {share(calls)}; no resolving state: {sorted(none)}")


def cmd_reports(args):
    fin, _ = main_info()
    R = summaries()
    demote = {i for i, s in R.items() if s.get("faithful") is True and recount(s, fin) != "byte"}
    original = {exp: load_scores(exp) for exp in SCORES}
    fixed, changes = corrected(original)
    variants = [("recorded", original, set()), ("recorded-strict", original, demote)]
    if (AUDIT / "rescore.json").exists():
        variants += [("corrected", fixed, set()), ("corrected-strict", fixed, demote)]
    L = ["# Reports rebuilt from the recorded and the corrected verdicts", "",
         f"Written {utc(time.time())} by `expb_audit.py reports`, with expb.py's own report code. 'strict': the plan's "
         f"byte-for-byte rule, so {len(demote)} replays count as unfaithful: {sorted(demote)}. 'corrected': "
         f"{len(changes)} verdict(s) replaced after two agreeing clean rescorings" + (":" if changes else "."), ""]
    L += [f"- {e} {i} {p}: {o} -> {v} ({st})" for e, i, p, o, v, st in changes] + ([""] if changes else [])
    texts = {}
    for name, sc, dem in variants:
        b, r = build_reports(mirror(name, sc, dem), with_b=not dem)
        texts[name] = (b, r)
        if not dem:
            (AUDIT / f"EXPB_REPORT.{name}.md").write_text(b)
        (AUDIT / f"REPLAY_REPORT.{name}.md").write_text(r)

    def read(p):
        return p.read_text() if p.exists() else ""

    pairs = [("EXPB_REPORT.md as committed", read(expb.OUT / "EXPB_REPORT.md"), "recorded", texts["recorded"][0]),
             ("REPLAY_REPORT.md as committed", read(expb.OUT / "REPLAY_REPORT.md"), "recorded", texts["recorded"][1]),
             ("REPLAY_REPORT recorded", texts["recorded"][1], "recorded-strict", texts["recorded-strict"][1])]
    if "corrected" in texts:
        pairs += [("EXPB_REPORT recorded", texts["recorded"][0], "corrected", texts["corrected"][0]),
                  ("REPLAY_REPORT recorded", texts["recorded"][1], "corrected", texts["corrected"][1]),
                  ("REPLAY_REPORT corrected", texts["corrected"][1], "corrected-strict", texts["corrected-strict"][1])]
    for la, a, lb, b in pairs:
        A = [ln for ln in a.splitlines() if not ln.startswith("Generated ")]
        B = [ln for ln in b.splitlines() if not ln.startswith("Generated ")]
        d = [ln for ln in difflib.unified_diff(A, B, la, lb, n=0, lineterm="") if not ln.startswith(("@@", "---", "+++"))]
        L.append(f"## {la} -> {lb}: " + ("no change" if not d else f"{len(d)} changed line(s)"))
        if d:
            L += ["```"] + [x[:400] for x in d[:80]] + (["..."] if len(d) > 80 else []) + ["```"]
        L.append("")
    L.append("## 9VzP 1a, recomputed as in FINAL_MEASURES")
    for name, sc, dem in variants:
        L.append(f"- {name}: " + u4(sc["replay"], lambda s, dem=dem: s.get("faithful") is True and s["instance_id"] not in dem))
    shutil.rmtree(AUDIT / "roots", ignore_errors=True)  # symlink folders only; the real files are never followed
    text = "\n".join(L) + "\n"
    (AUDIT / "REPORTS_SUMMARY.md").write_text(text)
    print(text)
    print(f"wrote {AUDIT / 'REPORTS_SUMMARY.md'} and the rebuilt reports in {AUDIT}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="no Docker: check every verdict, recount faithfulness, list suspects")
    a.add_argument("--prior-runs", type=int, default=2, help="harness runs logged before a disk-full stop that "
                                                             "also count as suspect (default 2)")
    a.add_argument("--commits", nargs="*", default=COMMITS, help="commits whose replay summaries to compare")
    a.add_argument("--prereg", default="d6a95a2", help="the pre-registration commit")
    a.add_argument("--merge", default="5404951", help="the merge commit to inspect")
    r = sub.add_parser("rescore", help="Docker: rescore the suspects in fresh containers")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--only", choices=list(SCORES), help="rescore only this experiment's suspects")
    r.add_argument("--workers", type=int, default=2, help="harness workers (default 2)")
    r.add_argument("--per-run", type=int, default=4, help="tasks per harness run, to bound disk use (default 4)")
    r.add_argument("--min-free-gb", type=float, default=15.0, help="free disk needed before each harness run")
    r.add_argument("--sec-per-patch", type=float, default=60.0, help="for the dry-run estimate only")
    sub.add_parser("reports", help="no Docker: rebuild the reports from the recorded and corrected verdicts")
    args = ap.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    {"audit": cmd_audit, "rescore": cmd_rescore, "reports": cmd_reports}[args.cmd](args)


if __name__ == "__main__":
    main()
