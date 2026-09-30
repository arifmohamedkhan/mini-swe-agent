#!/usr/bin/env python3
"""
Replay SWE-smith trajectories in their task environments and check the rebuilt labels against objective ground truth.

For a sample of runs from the rebuild, this starts each task's Docker image, puts it in the task's starting
state, and re-executes the agent's actions in order: shell commands in a shell that keeps the working directory
and exported variables between commands, and editor calls through an editor that mirrors SWE-agent's. After every
tested source edit it runs the task's own tests (FAIL_TO_PASS plus a sample of PASS_TO_PASS). That yields:
  * the exit code of each edit's next execution, to check next_exec's failure patterns;
  * whether the task's failing tests pass at each edit, to check what next_exec means;
  * Experiment A for SWE-smith: stopping after the k-th edit, scored by the task's tests.
Every run is checked for fidelity first (starting files match the agent's first views, editor outcomes match the
recorded ones, the failing tests fail at the start, the final state reproduces the recorded resolved label), and
only faithful runs enter the tables.

Run in the Codespace (it needs Docker), one step at a time:
  python replay_swesmith.py --step select    # candidates from runs.jsonl.gz (copy it from Drive: rebuild_v2/)
  python replay_swesmith.py --step fetch     # raw trajectories + task instances for the sample
  python replay_swesmith.py --step probe     # checks the environment setup on a few runs; share the report
  python replay_swesmith.py --step replay    # the long step; resumable
  python replay_swesmith.py --step analyze
Each step writes REPLAY_<STEP>.md to OUT_DIR. The parser code is copied verbatim from rebuild_swesmith.py.
"""
import gzip
import hashlib
import itertools
import json
import os
import random
import re
import statistics
import subprocess
import time
from collections import Counter, defaultdict

# ============================================================================ CONFIG
OUT_DIR = "replay_out"
RUNS_PATH = "runs.jsonl.gz"  # the rebuild's output, copied into the Codespace
HF_DATASET = "SWE-bench/SWE-smith-trajectories"
HF_REVISION = "08e109b4a59eaeebf80e4675cd125d42e7ac99a4"
INSTANCES_DATASET = "SWE-bench/SWE-smith"  # task instances: tests, image, bug patch (the probe prints the fields)
INSTANCES_SPLIT = "train"
IMAGE_FIELD = "image_name"
IMAGE_TEMPLATE = "swebench/swesmith.x86_64.{slug}"  # only if instances lack IMAGE_FIELD
STRATEGIES = ["as_is", "checkout_branch", "apply_patch", "apply_patch_reverse"]  # tried by the probe
# Ties go to the task's own branch: it also hides the failing tests, as the agent's environment did.
PREFERENCE = ["checkout_branch", "apply_patch", "as_is", "apply_patch_reverse"]
N_REPOS, PER_REPO, MAX_ACTIONS = 6, 10, 60  # sample: up to 10 runs from each of the 6 largest repositories
# MONAI's image does not fit on a 32 GB Codespace; pandas rebuilds its C extensions in every run (~10 min).
# Changing this list means rerunning select and fetch.
EXCLUDE_REPOS = ["Project-MONAI__MONAI", "pandas-dev__pandas"]
PROBE_RUNS = 3  # one run from each of the first repositories in the sample
CMD_TIMEOUT, TEST_TIMEOUT, RUN_BUDGET = 120, 300, 1800  # seconds
P2P_PER_EDIT, P2P_FINAL = 20, 200  # PASS_TO_PASS tests sampled after each edit / at the end
F2P_PER_EDIT, F2P_FINAL = 50, 300  # FAIL_TO_PASS tests sampled likewise (some tasks list thousands)
# Test ids go through a file: thousands of ids on one command line exceed the kernel's argument limit.
TEST_CMD = ("python -c \"import sys, pytest; sys.exit(pytest.main([t for t in open('{tests_file}').read()"
            ".split(chr(10)) if t] + ['-rA', '-p', 'no:cacheprovider', '--tb=no', '-q', '--color=no']))\"")
# Repositories with compiled extensions (pandas, via meson) rebuild on the first import after a checkout,
# which takes minutes; one warm-up import per container keeps that out of the test timings.
WARMUP_TIMEOUT = 3600
WARMUP_IMPORTS = {}  # repository name -> module to import, when it differs from the repository name
ACTIVATE = "source /opt/miniconda3/bin/activate testbed 2>/dev/null || true"
PY_CANDIDATES = ["python3", "/opt/miniconda3/envs/testbed/bin/python", "/opt/miniconda3/bin/python", "python"]
CLEAN_IMAGES = True  # remove each repository's image after its runs (and after probing it), to save disk
MIN_FREE_GB = 12  # before pulling an image, clear unused Docker data if less than this is free
SEED = 0
BACKEND = "docker"  # "local" is for testing without Docker
RAW_LOCAL_FILES, INSTANCES_LOCAL, LOCAL_REPOS = {}, None, {}
# ===================================================================================

LINES = []


def out(s=""):
    print(s)
    LINES.append(s)


def header(t):
    out()
    out("=" * 78)
    out(t)
    out("=" * 78)


# ============================================================================ PARSER (verbatim from rebuild_swesmith.py)
# ------------------------------------------------------------------ row helpers
K_INSTANCE = ["instance_id", "instance", "task_id"]
K_MODEL = ["model", "model_name", "model_name_or_path"]
K_RESOLVED = ["resolved", "is_resolved", "success"]
K_PATCH = ["patch", "model_patch", "submission"]
K_ID = ["traj_id", "id", "trajectory_id"]


def get_field(rec, keys):
    if not isinstance(rec, dict):
        return None
    low = {str(k).lower(): k for k in rec}
    for key in keys:
        k = low.get(key)
        if k is not None and rec[k] is not None and rec[k] != "":
            return rec[k]
    return None


def as_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and v in (0, 1):
        return bool(v)
    if isinstance(v, str) and v.strip().lower() in ("true", "false", "1", "0"):
        return v.strip().lower() in ("true", "1")
    return None


def content_text(c):
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(content_text(x) for x in c)
    if isinstance(c, dict):
        for k in ("text", "content", "output"):
            if k in c:
                return content_text(c[k])
        return ""
    return str(c)


def raw_messages(row):
    v = row.get("messages") if isinstance(row, dict) else None
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except (json.JSONDecodeError, TypeError):
            return None
    return v if isinstance(v, list) and v else None


def short_hash(s):
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()[:12]


# ------------------------------------------------------------------ run fingerprint
# Identical to the audit's fingerprint (validated there: 23,816 runs, no run in only one format).
WRAPPER_RE = re.compile(r"(?i)</?[a-z_][a-z0-9_]{0,30}>|\b(observation|output|returncode|stdout|stderr)\b\s*:?")
OBS_ROLES = {"tool", "user", "function", "observation", "ipython", "environment"}


def obs_and_turns(msgs):
    obs, turns, skipped_task = [], 0, False
    for m in msgs:
        if not isinstance(m, dict):
            continue
        if "role" not in m and "observation" in m:
            turns += 1
            obs.append(content_text(m.get("observation")))
            continue
        role = str(m.get("role", "")).lower()
        if role == "assistant":
            turns += 1
        elif role in OBS_ROLES:
            if not skipped_task:
                skipped_task = True
                continue
            obs.append(content_text(m.get("content")))
    return obs, turns


def obs_hash(text):
    t = re.sub(r"[^a-z0-9]+", "", WRAPPER_RE.sub(" ", text).lower())
    return int(hashlib.sha1(t.encode()).hexdigest()[:15], 16) if len(t) >= 40 else None


def fingerprint(row, msgs):
    obs, turns = obs_and_turns(msgs)
    hashes = tuple(h for h in (obs_hash(o) for o in obs) if h is not None)[:25]
    patch = get_field(row, K_PATCH)
    ph = short_hash(patch) if isinstance(patch, str) and patch.strip() else ""
    inst = str(get_field(row, K_INSTANCE))
    return hashlib.sha1(repr((inst, turns, hashes, ph)).encode()).hexdigest()[:16]


# ------------------------------------------------------------------ new action extraction
XML_FUNC_RE = re.compile(r"<function=([\w\-.]+)>(.*?)</function>", re.S)
XML_PARAM_RE = re.compile(r"<parameter=([\w\-]+)>(.*?)</parameter>", re.S)
TICKS_RE = re.compile(r"```[^\n`]*\n(.*?)```", re.S)
EDITOR_RE = re.compile(r"^\s*str_replace_editor\s+(\w+)\s+(\S+)")
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1[^\n]*\n.*?^\s*\2\s*$", re.S | re.M)
EXEC_RE = re.compile(
    r"(?:^|&&|\|\||;|\||\(|\n)\s*"  # at a command position
    r"(?:(?:[A-Za-z_]\w*=\S*|env|time|nohup|sudo|timeout\s+\S+)\s+)*"  # env assignments and wrappers
    r"(?:\S*/)?(?:python\d?(?:\.\d+)?(?!\s+-m\s+pip\b)|pytest|py\.test|tox|nosetests|coverage)(?=\s|$|;|\))")
WRITE_RULES = [
    ("sed -i", re.compile(r"\bsed\s+(?:-[a-zA-Z]*i\b|--in-place)")),
    ("perl -i", re.compile(r"\bperl\s+-[a-zA-Z]*i")),
    ("redirect", re.compile(r"(?<![0-9&<>])>>?\s*(?!&|/dev/null)[\w./~\"'-]")),
    ("tee", re.compile(r"\btee\s")),
    ("mv/cp", re.compile(r"(?:^|[\s;&|])(?:mv|cp)\s")),
    ("git/patch", re.compile(r"(?:^|[\s;&|])(?:patch\s|git\s+(?:apply|checkout|restore|stash))")),
    ("rm", re.compile(r"(?:^|[\s;&|])rm\s")),  # last: a command that also writes gets the stronger rule
]
SCAN_CONTINUES_PAST = {"rm"}  # shell writes that do not end the search for an edit's next execution
READ_RE = re.compile(r"(?:^|[\s;&|])(?:cat|head|tail|less|more|grep|egrep|rg|find|ls|tree|wc|nl|awk|sed\s+-n|pwd|cd)\b")
SCRATCH_RE = re.compile(r"(^/tmp/)|(/|^)(repro\w*|reproduce\w*|debug\w*|scratch\w*|check_\w*|verify\w*|test_\w*)\.py$")

EDIT_OK_RES = [re.compile(p, re.I) for p in (r"has been edited", r"created successfully", r"File created",
                                               r"undone successfully")]
EDIT_REJECT_RES = [re.compile(p, re.I) for p in (r"No replacement was performed", r"did not appear verbatim",
                                                   r"Multiple occurrences", r"does not exist", r"already exists",
                                                   r"Cannot overwrite", r"Invalid `?insert_line",
                                                   r"not an absolute path", r"Unrecognized command",
                                                   r"No edit history", r"Parameter `?\w+`? is required",
                                                   r"Traceback \(most recent call last\)",
                                                   r"EXITCODESTART[1-9]\d*EXITCODEEND", r"Ran into \[Errno",
                                                   r"usage: str_replace_editor", r"bash: .*syntax error")]
EXEC_FAIL_RES = [
    ("traceback", re.compile(r"Traceback \(most recent call last\)")),
    ("syntax/import", re.compile(r"^\s*(?:SyntaxError|IndentationError|TabError|ModuleNotFoundError|ImportError)\b",
                                 re.M)),
    ("tests failed", re.compile(r"\b[1-9]\d* (?:failed|errors?)\b")),
    ("FAILED/ERROR line", re.compile(r"^(?:FAILED|ERROR)\b", re.M)),
    ("pytest assertion", re.compile(r"^E\s{3}", re.M)),
    ("cannot run", re.compile(r"can't open file")),
]
# A looser failure rule, for a sensitivity bound: scripts often catch an exception and print it
# ("Error: NameError: ...") instead of crashing, which the strict rule reads as a pass.
LOOSE_FAIL_RES = [re.compile(r"\b\w*(?:Error|Exception)\s*:"), re.compile(r"^\s*(?:FAIL|FAILED|Failed)\b", re.M),
                  re.compile("\u274c|\u2717")]


def from_call(name, args, src):
    name = str(name or "").strip()
    if name == "str_replace_editor":
        sub, path = args.get("command"), args.get("path")
        return ("str_replace_editor", str(sub) if sub else None, str(path) if path else None,
                f"str_replace_editor {sub} {path}", src)
    if name in ("bash", "execute_bash", "run_command"):
        return ("bash", None, None, str(args.get("command", args.get("_raw", ""))), src)
    if name == "submit":
        return ("submit", None, None, "submit", src)
    return (name or "unknown", None, None, f"{name} {json.dumps(args)[:200]}", src)


def from_string(s, src):
    s = s.strip()
    m = EDITOR_RE.match(s)
    if m:
        return ("str_replace_editor", m.group(1), m.group(2), s, src)
    if re.match(r"^submit\b", s):
        return ("submit", None, None, s, src)
    return ("bash", None, None, s, src)


def extract_actions(msg):
    """Actions in one assistant message, from the most reliable source available."""
    tcs = msg.get("tool_calls") or []
    acts = []
    if isinstance(tcs, list):
        for tc in tcs:
            f = tc.get("function", {}) if isinstance(tc, dict) else {}
            args = f.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, TypeError):
                    args = {"_raw": args}
            acts.append(from_call(f.get("name"), args if isinstance(args, dict) else {}, "tool_calls"))
    if acts:
        return acts
    action = msg.get("action")
    if isinstance(action, str) and action.strip():
        return [from_string(action, "action field")]
    content = content_text(msg.get("content"))
    funcs = list(XML_FUNC_RE.finditer(content))
    if funcs:
        return [from_call(m.group(1), {k: v.strip() for k, v in XML_PARAM_RE.findall(m.group(2))}, "xml tags")
                for m in funcs]
    blocks = TICKS_RE.findall(content)
    if blocks:
        return [from_string(blocks[-1], "code block")]
    if content.strip().startswith("Exit due to"):
        reason = content.strip().splitlines()[0][len("Exit due to"):].strip()[:60]
        return [("exit", reason, None, content.strip()[:200], "exit message")]
    return []


def classify(tool, sub, text):
    """(kind, rule). E editor edit, V editor view, X code execution, B shell file write,
    S read/search, U submit, O other."""
    if tool == "str_replace_editor":
        if sub in ("create", "str_replace", "insert", "undo_edit"):
            return "E", sub
        return ("V", "view") if sub == "view" else ("O", f"editor:{sub}")
    if tool == "submit":
        return "U", "submit"
    if tool == "exit":
        return "T", sub
    if tool == "bash":
        cmd = HEREDOC_RE.sub(lambda m: m.group(0).split("\n", 1)[0] + "\n", text)
        if EXEC_RE.search(cmd):
            return "X", "exec"
        for rule, rx in WRITE_RULES:
            if rx.search(cmd):
                return "B", rule
        return ("S", "read") if READ_RE.search(cmd) else ("O", "bash")
    return "O", f"tool:{tool}"


def editor_applied(out_text):
    head = out_text[:400]
    if any(p.search(head[:250]) for p in EDIT_OK_RES):
        return True
    if any(p.search(head) for p in EDIT_REJECT_RES):
        return False
    return None


def exec_state(out_text):
    for name, rx in EXEC_FAIL_RES:
        if rx.search(out_text):
            return "fail", name
    return "pass", None


def exec_state_loose(out_text):
    if exec_state(out_text)[0] == "fail" or any(rx.search(out_text) for rx in LOOSE_FAIL_RES):
        return "fail"
    return "pass"


def parse_run(msgs):
    """Flattened actions with kinds and outputs, and labelled edits."""
    turns = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role", "")).lower()
        if role == "assistant":
            turns.append({"actions": extract_actions(m), "outs": []})
        elif turns and role in OBS_ROLES:
            turns[-1]["outs"].append(content_text(m.get("content")))
    actions = []
    for ti, t in enumerate(turns):
        if not t["actions"]:
            actions.append(dict(turn=ti, kind="?", rule="no action", tool="", sub=None, path=None, text="",
                                out=t["outs"][0] if t["outs"] else "", src="none"))
            continue
        for j, (tool, sub, path, text, src) in enumerate(t["actions"]):
            o = t["outs"][j] if j < len(t["outs"]) else (t["outs"][-1] if t["outs"] else "")
            kind, rule = classify(tool, sub, text)
            actions.append(dict(turn=ti, kind=kind, rule=rule, tool=tool, sub=sub, path=path, text=text, out=o,
                                src=src))
    edits = []
    for a_i, a in enumerate(actions):
        if a["kind"] != "E":
            continue
        nxt, gap, nxt_i, pat, stop_rule = "untested", None, None, None, "end of run"
        for b_i in range(a_i + 1, len(actions)):
            k = actions[b_i]["kind"]
            if k == "E" or (k == "B" and actions[b_i]["rule"] not in SCAN_CONTINUES_PAST):
                stop_rule = "editor edit" if k == "E" else actions[b_i]["rule"]
                break
            if k == "X":
                nxt, pat = exec_state(actions[b_i]["out"])
                gap, nxt_i, stop_rule = b_i - a_i, b_i, "execution"
                break
        path = a["path"] or ""
        edits.append(dict(a=a_i, op=a["sub"], path=path, applied=editor_applied(a["out"]), next_exec=nxt,
                          next_exec_loose=exec_state_loose(actions[nxt_i]["out"]) if nxt_i is not None else "untested",
                          gap=gap, pattern=pat, scan_ended=stop_rule,
                          scratch=bool(a["sub"] == "create" and SCRATCH_RE.search(path) or path.startswith("/tmp/")),
                          _next=nxt_i))
    return turns, actions, edits




# ============================================================================ REPLAY: editor arguments
def parse_editor_string(s):
    """Arguments of 'str_replace_editor <command> <path> --key value ...' written as one string."""
    import shlex
    try:
        toks = shlex.split(s, posix=True)
    except ValueError:
        m = EDITOR_RE.match(s)
        return {"command": m.group(1), "path": m.group(2), "_unparsed": True} if m else {"_unparsed": True}
    if len(toks) < 3 or toks[0] != "str_replace_editor":
        return {"_unparsed": True}
    args = {"command": toks[1], "path": toks[2]}
    i = 3
    while i < len(toks):
        if toks[i].startswith("--"):
            key = toks[i][2:]
            vals = []
            i += 1
            while i < len(toks) and not toks[i].startswith("--"):
                vals.append(toks[i])
                i += 1
            args[key] = vals[0] if len(vals) == 1 else vals
        else:
            i += 1
    return args


def calls_for(msg):
    """(action tuple, replay arguments) for each action extract_actions finds in one message, in order."""
    tcs = msg.get("tool_calls") or []
    out_calls = []
    if isinstance(tcs, list):
        for tc in tcs:
            f = tc.get("function", {}) if isinstance(tc, dict) else {}
            args = f.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, TypeError):
                    args = {"_raw": args}
            args = args if isinstance(args, dict) else {}
            out_calls.append((from_call(f.get("name"), args, "tool_calls"), dict(args)))
    if out_calls:
        return out_calls
    action = msg.get("action")
    if isinstance(action, str) and action.strip():
        act = from_string(action, "action field")
        return [(act, parse_editor_string(action.strip()) if act[0] == "str_replace_editor" else {"command": act[3]})]
    content = content_text(msg.get("content"))
    funcs = list(XML_FUNC_RE.finditer(content))
    if funcs:
        res = []
        for m in funcs:
            raw = {k: v for k, v in XML_PARAM_RE.findall(m.group(2))}
            res.append((from_call(m.group(1), {k: v.strip() for k, v in raw.items()}, "xml tags"), raw))
        return res
    blocks = TICKS_RE.findall(content)
    if blocks:
        act = from_string(blocks[-1], "code block")
        return [(act, parse_editor_string(blocks[-1].strip()) if act[0] == "str_replace_editor" else {"command": act[3]})]
    if content.strip().startswith("Exit due to"):
        return [(extract_actions(msg)[0], {})]
    return []


def replay_plan(msgs):
    """parse_run's actions and edits, plus the replay arguments of every action (same order)."""
    turns, actions, edits = parse_run(msgs)
    calls = []
    for m in msgs:
        if isinstance(m, dict) and str(m.get("role", "")).lower() == "assistant":
            c = calls_for(m)
            if len(c) != len(extract_actions(m)):
                return None
            calls.extend(c if c else [(None, {})])
    if len(calls) != len(actions):
        return None
    for a, (act, args) in zip(actions, calls):
        a["args"] = args
    return actions, edits


# ============================================================================ REPLAY: execution backends
class DockerExec:
    """Commands run inside a container started from the task's image."""

    def __init__(self, image, name):
        self.image, self.name = image, name

    def start(self):
        subprocess.run(["docker", "rm", "-f", self.name], capture_output=True)
        r = subprocess.run(["docker", "run", "-d", "--name", self.name, "--entrypoint", "", self.image,
                            "sleep", "infinity"], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"docker run failed: {r.stderr.strip()[:300]}")

    def sh(self, script, timeout=120, stdin=None):
        try:
            r = subprocess.run(["docker", "exec", "-i", self.name, "bash", "-c", script], input=stdin,
                               capture_output=True, text=True, timeout=timeout, errors="replace")
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            return 124, "__REPLAY_TIMEOUT__"

    def put(self, path, text):
        return self.sh(f"mkdir -p \"$(dirname '{path}')\" && cat > '{path}'", stdin=text)

    def untranslate(self, text):
        return text

    def stop(self):
        subprocess.run(["docker", "rm", "-f", self.name], capture_output=True)


class LocalExec(DockerExec):
    """Same interface on the local machine, for testing: /testbed and /tmp/_replay map to local folders."""

    def __init__(self, root, tmp):
        self.root, self.tmp = root, tmp

    def tr(self, s):
        return s.replace("/testbed", self.root).replace("/tmp/_replay", os.path.join(self.tmp, "_replay"))

    def start(self):
        os.makedirs(self.tmp, exist_ok=True)

    def sh(self, script, timeout=120, stdin=None):
        try:
            r = subprocess.run(["bash", "-c", self.tr(script)], input=self.tr(stdin) if stdin else None,
                               capture_output=True, text=True, timeout=timeout, errors="replace")
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            return 124, "__REPLAY_TIMEOUT__"

    def put(self, path, text):
        p = self.tr(path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(self.tr(text))
        return 0, ""

    def untranslate(self, text):
        return text.replace(self.root, "/testbed")

    def stop(self):
        pass


# ============================================================================ REPLAY: the editor, inside the task environment
EDITOR_HELPER = r'''
import json, os, sys
op = json.load(open("/tmp/_replay_op.json"))
H = "/tmp/_replay_editor_history.json"
hist = json.load(open(H)) if os.path.exists(H) else {}
def drop_pyc(p):
    d, name = os.path.split(p)
    cache = os.path.join(d, "__pycache__")
    if os.path.isdir(cache):
        for f in os.listdir(cache):
            if f.startswith(os.path.splitext(name)[0] + ".") and f.endswith(".pyc"):
                os.remove(os.path.join(cache, f))
def done(ok, msg, variant=None):
    if ok and op.get("command") != "view" and op.get("path"):
        drop_pyc(op["path"])
    json.dump(hist, open(H, "w"))
    print("__REPLAY__" + json.dumps({"ok": ok, "msg": msg, "variant": variant}))
    sys.exit(0)
cmd, path = op.get("command"), op.get("path")
if not path or not os.path.isabs(path):
    done(False, "not an absolute path")
if cmd == "view":
    done(True, "view")
if cmd == "create":
    if os.path.exists(path):
        done(False, "already exists")
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        done(False, "parent directory does not exist")
    with open(path, "w") as f:
        f.write(op.get("file_text") or "")
    hist.setdefault(path, []).append(None)
    done(True, "created")
if not os.path.exists(path):
    done(False, "does not exist")
if os.path.isdir(path):
    done(False, "is a directory")
with open(path, errors="surrogateescape") as f:
    text = f.read()
if cmd == "str_replace":
    old = op.get("old_str")
    if old is None:
        done(False, "old_str required")
    new = op.get("new_str") or ""
    variants = [(old, new, "exact")]
    if op.get("_try_stripped"):
        variants.append((old.strip("\n"), new.strip("\n"), "stripped newlines"))
    content = text.expandtabs()
    for o, n, name in variants:
        o2, n2 = o.expandtabs(), n.expandtabs()
        if o2 == n2:
            done(False, "same as new_str", name)
        if content.count(o2) == 1:
            hist.setdefault(path, []).append(text)
            with open(path, "w", errors="surrogateescape") as f:
                f.write(content.replace(o2, n2))
            done(True, "edited", name)
    done(False, "occurrences %d" % content.count(old.expandtabs()))
if cmd == "insert":
    try:
        line = int(op.get("insert_line"))
    except (TypeError, ValueError):
        done(False, "insert_line required")
    lines = text.expandtabs().split("\n")
    if line < 0 or line > len(lines):
        done(False, "invalid insert_line")
    hist.setdefault(path, []).append(text)
    with open(path, "w", errors="surrogateescape") as f:
        f.write("\n".join(lines[:line] + (op.get("new_str") or "").expandtabs().split("\n") + lines[line:]))
    done(True, "inserted")
if cmd == "undo_edit":
    if not hist.get(path):
        done(False, "no edit history")
    prev = hist[path].pop()
    if prev is None:
        os.remove(path)
    else:
        with open(path, "w", errors="surrogateescape") as f:
            f.write(prev)
    done(True, "undone")
done(False, "unrecognized command %s" % cmd)
'''

# One persistent-looking shell: each command runs in a fresh bash that restores the previous
# command's working directory and exported variables, like SWE-agent's long-lived session.
WRAP = ('source /tmp/_replay_env.sh 2>/dev/null; cd "$(cat /tmp/_replay_cwd 2>/dev/null || echo /testbed)"; '
        'source /tmp/_replay_cmd.sh; __rc=$?; export -p > /tmp/_replay_env.sh; pwd > /tmp/_replay_cwd; exit $__rc')
BACKGROUND_RE = re.compile(r"(?<![&>|])&(?![&>])\s*(?:$|\n|;)|\bnohup\b|\bdisown\b")
TEST_LINE_RE = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(.+?)(?:\s+-\s+.*)?\s*$", re.M)
VIEW_LINE_RE = re.compile(r"^\s*(\d+)\t(.*)$", re.M)


def run_bash(ex, cmd, timeout):
    ex.put("/tmp/_replay_cmd.sh", cmd + "\n")
    rc, out_text = ex.sh(f"timeout {timeout} bash -c '{WRAP}' 2>&1", timeout=timeout + 30)
    return rc, ex.untranslate(out_text)


def editor_op(ex, py, args, recorded_applied):
    op = {k: v for k, v in args.items() if not k.startswith("_")}
    op["_try_stripped"] = recorded_applied is True  # only to reproduce a recorded success
    ex.put("/tmp/_replay_op.json", json.dumps(op))
    rc, text = ex.sh(f"{py} /tmp/_replay_editor.py", timeout=60)
    m = re.search(r"__REPLAY__(\{.*\})", text)
    return json.loads(m.group(1)) if m else {"ok": None, "msg": text[-200:], "variant": None}


def norm_output(t):
    t = re.sub(r"^\s*OBSERVATION:\s*", "", t or "")
    t = re.sub(r"\x1b\[[0-9;]*m", "", t)
    t = re.sub(r"0x[0-9a-f]{6,}", "0x", t)
    t = re.sub(r"\b\d+(?:\.\d+)?s\b", "<t>s", t)
    t = re.sub(r"/tmp/[\w./-]+", "/tmp/<p>", t)
    return re.sub(r"\s+", " ", t).strip()[:3000]


def similarity(a, b):
    import difflib
    a, b = norm_output(a), norm_output(b)
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def view_score(ex, actions):
    """How well the container's files match what the agent saw in its first views (before any change)."""
    matched = compared = 0
    for a in actions:
        if a["kind"] in ("E", "B"):
            break
        if a["kind"] != "V" or not a.get("path"):
            continue
        seen = {int(n): c.rstrip("\r").rstrip() for n, c in VIEW_LINE_RE.findall(a["out"])}
        if not seen:
            continue
        rc, text = ex.sh(f"cat '{a['path']}'", timeout=30)
        if rc:
            continue
        lines = [ln.expandtabs().rstrip() for ln in ex.untranslate(text).split("\n")]
        for n, c in list(seen.items())[:40]:
            compared += 1
            matched += (1 <= n <= len(lines) and lines[n - 1] == c)
        if compared >= 80:
            break
    return (matched / compared) if compared else None


def test_files(tests):
    return sorted({t.split("::")[0] for t in tests if t.split("::")[0].endswith(".py")})


def run_tests(ex, tests, refs, timeout):
    """Run the task's tests on the current code, with test files restored to their original versions
    (as a harness does), then put the agent's versions back. SWE-smith removes the failing tests' files
    from the agent's working tree, so the originals come from the refs (HEAD~1 for SWE-smith branches)."""
    if not tests:
        return {"ran": False}
    files = test_files(tests)
    swap, restore = [], []
    for i, f in enumerate(files):
        keep = f"/tmp/_replay_keep_{i}"
        get = " || ".join(f"git show {r}:'{f}' > /tmp/_replay_orig 2>/dev/null" for r in refs)
        swap.append(f"if [ -e '{f}' ]; then cp '{f}' {keep}; echo 1 > {keep}.had; else rm -f {keep}.had; fi; "
                    f"if {{ {get}; }}; then mkdir -p \"$(dirname '{f}')\"; cp /tmp/_replay_orig '{f}'; fi")
        restore.append(f"if [ -e {keep}.had ]; then cp {keep} '{f}'; else rm -f '{f}'; fi")
    ex.put("/tmp/_replay_swap.sh", "cd /testbed\n" + "\n".join(swap) + "\n")
    ex.put("/tmp/_replay_restore.sh", "cd /testbed\n" + "\n".join(restore) + "\n")
    ex.put("/tmp/_replay_tests.txt", "\n".join(tests) + "\n")
    ex.sh("bash /tmp/_replay_swap.sh", timeout=120)
    rc, text = ex.sh(f"source /tmp/_replay_env.sh 2>/dev/null; cd /testbed && timeout {timeout} "
                     f"{TEST_CMD.format(tests_file='/tmp/_replay_tests.txt')} 2>&1", timeout=timeout + 60)
    ex.sh("bash /tmp/_replay_restore.sh", timeout=120)
    status = {}
    for st, node in TEST_LINE_RE.findall(re.sub(r"\x1b\[[0-9;]*[A-Za-z]|\r", "", ex.untranslate(text))):
        status[node.strip()] = st
    return {"ran": True, "rc": rc, "status": status, "tail": text[-400:]}


def warmup(ex, inst):
    """Import the repository's package once, with a long timeout, so a compiled-extension rebuild
    triggered by the checkout happens here and not inside a test run."""
    repo = inst["instance_id"].split(".")[0]
    mod = WARMUP_IMPORTS.get(repo) or repo.split("__")[-1].replace("-", "_").lower()
    t = time.time()
    rc, text = ex.sh(f"source /tmp/_replay_env.sh 2>/dev/null; cd /testbed && timeout {WARMUP_TIMEOUT} "
                     f"python -c 'import {mod}' 2>&1", timeout=WARMUP_TIMEOUT + 60)
    return {"module": mod, "rc": rc, "seconds": round(time.time() - t), "tail": text.strip()[-160:]}


def shlex_quote(s):
    import shlex
    return shlex.quote(s)


def summarize_tests(res, f2p, p2p):
    if not res.get("ran"):
        return None
    st = res["status"]
    f_pass = sum(st.get(t) == "PASSED" for t in f2p)
    p_fail = sum(st.get(t) in ("FAILED", "ERROR") for t in p2p)
    return {"f2p_pass": f_pass, "f2p_total": len(f2p), "p2p_fail": p_fail, "p2p_total": len(p2p),
            "p2p_seen": sum(t in st for t in p2p), "fixed": f_pass == len(f2p) and len(f2p) > 0,
            "parsed": bool(st)}


# ============================================================================ STEPS
def load_jsonl(path):
    """Read JSON lines, skipping a line cut off by an interruption (that run is simply redone)."""
    op = gzip.open if path.endswith(".gz") else open
    rows = []
    with op(path, "rt") as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def as_list(v):
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            v = [v]
    return list(v or [])


def tested_source_edits(r):
    return [e for e in r["edits"] if e["applied"] is not False and not e["scratch"] and e["next_exec"] != "untested"]


def step_select():
    header("SELECT: candidate runs from the rebuild")
    recs = load_jsonl(RUNS_PATH)
    elig = [r for r in recs if tested_source_edits(r) and r["n_actions"] <= MAX_ACTIONS and r["resolved"] is not None
            and r["repo"] not in EXCLUDE_REPOS]
    if EXCLUDE_REPOS:
        out(f"  excluded repositories: {', '.join(EXCLUDE_REPOS)}")
    by_repo = defaultdict(list)
    for r in elig:
        by_repo[r["repo"]].append(r)
    repos = sorted(by_repo, key=lambda k: -len(by_repo[k]))[:N_REPOS]
    cands = []
    for repo in repos:
        rs = sorted(by_repo[repo], key=lambda r: hashlib.sha1(f"{r['run_id']}{SEED}".encode()).hexdigest())
        seen, res_q, unres_q = set(), [], []
        for r in rs:
            if r["instance_id"] in seen:
                continue
            seen.add(r["instance_id"])
            (res_q if r["resolved"] else unres_q).append(r)
        order = [x for pair in itertools.zip_longest(res_q, unres_q) for x in pair if x][:PER_REPO * 3]
        for rank, r in enumerate(order):
            cands.append({k: r[k] for k in ("run_id", "instance_id", "repo", "model", "resolved", "source_format",
                                            "source_row", "n_actions")} | {"rank": rank,
                                                                          "legacy_eo": r["legacy"]["edit_outcomes"]})
        out(f"  {repo}: {len(by_repo[repo]):,} eligible runs; {len(order)} candidates "
            f"({sum(r['resolved'] for r in order)} resolved)")
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(cands, open(os.path.join(OUT_DIR, "candidates.json"), "w"))
    out(f"  {len(cands)} candidates from {len(repos)} repositories; eligible = at least one tested source edit, "
        f"at most {MAX_ACTIONS} actions")


def iter_split(fmt):
    if BACKEND == "local":
        with open(RAW_LOCAL_FILES[fmt]) as f:
            for i, line in enumerate(f):
                yield i, json.loads(line)
        return
    from datasets import load_dataset
    for i, row in enumerate(load_dataset(HF_DATASET, split=fmt, streaming=True, revision=HF_REVISION)):
        yield i, row


def iter_instances():
    if BACKEND == "local":
        yield from json.load(open(INSTANCES_LOCAL))
        return
    from datasets import load_dataset
    yield from load_dataset(INSTANCES_DATASET, split=INSTANCES_SPLIT, streaming=True)


def step_fetch():
    header("FETCH: raw trajectories and task instances for the sample")
    cands = json.load(open(os.path.join(OUT_DIR, "candidates.json")))
    want = defaultdict(dict)
    for c in cands:
        want[c["source_format"]][c["source_row"]] = c
    got, skipped = {}, Counter()
    for fmt, rows in want.items():
        last = max(rows)
        for i, row in iter_split(fmt):
            if i > last:
                break
            c = rows.get(i)
            if c is None:
                continue
            msgs = raw_messages(row)
            if not msgs or fingerprint(row, msgs) != c["run_id"]:
                skipped["row does not match the rebuild's fingerprint"] += 1
                continue
            plan = replay_plan(msgs)
            if plan is None:
                skipped["replay arguments not aligned with parsed actions"] += 1
                continue
            if any(a["tool"] == "bash" and BACKGROUND_RE.search(a["text"]) for a in plan[0]):
                skipped["starts a background process"] += 1
                continue
            got[c["run_id"]] = {"cand": c, "row": {k: row[k] for k in row}}
    sample = []
    for repo in dict.fromkeys(c["repo"] for c in cands):
        ok = sorted((g for g in got.values() if g["cand"]["repo"] == repo), key=lambda g: g["cand"]["rank"])
        sample += ok[:PER_REPO]
    need = {g["cand"]["instance_id"] for g in sample}
    inst = {}
    for row in iter_instances():
        if row["instance_id"] in need:
            inst[row["instance_id"]] = {k: row[k] for k in row}
            if len(inst) == len(need):
                break
    missing = need - set(inst)
    sample = [g for g in sample if g["cand"]["instance_id"] in inst]
    with open(os.path.join(OUT_DIR, "sample_rows.jsonl"), "w") as f:
        for g in sample:
            f.write(json.dumps(g, default=str) + "\n")
    json.dump(inst, open(os.path.join(OUT_DIR, "instances.json"), "w"), default=str)
    out(f"  sample: {len(sample)} runs from {len(set(g['cand']['repo'] for g in sample))} repositories; "
        f"{sum(g['cand']['resolved'] for g in sample)} resolved")
    for k, v in skipped.items():
        out(f"  skipped {v}: {k}")
    if missing:
        out(f"  {len(missing)} task instances not found in {INSTANCES_DATASET}; their runs were dropped")


def free_gb(path="/"):
    import shutil
    return shutil.disk_usage(path).free / 2 ** 30


def pull(image):
    """Pull an image after making room; returns (ok, message)."""
    if free_gb() < MIN_FREE_GB:
        subprocess.run(["docker", "system", "prune", "-af"], capture_output=True)
    t = time.time()
    r = subprocess.run(["docker", "pull", image], capture_output=True, text=True)
    if r.returncode:
        subprocess.run(["docker", "system", "prune", "-af"], capture_output=True)
        err = r.stderr.strip()
        reason = "the image does not fit on this disk" if "no space left" in err else err[-200:]
        return False, f"{reason} ({time.time() - t:.0f}s; cleaned up, {free_gb():.0f} GB free now)"
    return True, f"{time.time() - t:.0f}s, {free_gb():.0f} GB free after"


def drop_image(image):
    subprocess.run(["docker", "rmi", "-f", image], capture_output=True)
    subprocess.run(["docker", "system", "prune", "-f"], capture_output=True)


def image_for(inst):
    if inst.get(IMAGE_FIELD):
        return inst[IMAGE_FIELD]
    slug = inst["instance_id"].rsplit(".", 1)[0].replace("__", "_1776_")
    return IMAGE_TEMPLATE.format(slug=slug)


def make_exec(image, name, iid=None):
    if BACKEND == "local":
        return LocalExec(LOCAL_REPOS[iid], os.path.join(OUT_DIR, "local_tmp", name))
    return DockerExec(image, name)


def setup(ex, inst, strategy):
    """Put the environment in the task's starting state; returns (ok, message, start ref)."""
    iid = inst["instance_id"]
    if strategy in ("apply_patch", "apply_patch_reverse"):
        ex.put("/tmp/_replay_bug.patch", inst.get("patch") or "")
    cmds = {"as_is": [],
            "checkout_branch": [f"cd /testbed && (git checkout -q -f '{iid}' 2>&1 || "
                                f"(git fetch -q origin '{iid}' && git checkout -q -f FETCH_HEAD) 2>&1)"],
            "apply_patch": ["cd /testbed && git apply --whitespace=nowarn /tmp/_replay_bug.patch 2>&1"],
            "apply_patch_reverse": ["cd /testbed && git apply -R --whitespace=nowarn /tmp/_replay_bug.patch 2>&1"]}
    if BACKEND == "local" and strategy != "as_is":
        return False, "local backend only supports as_is", None
    for c in cmds[strategy]:
        rc, text = ex.sh(c, timeout=300)
        if rc:
            return False, text.strip()[-300:], None
    ex.sh(f"{ACTIVATE}; export PYTHONDONTWRITEBYTECODE=1; export -p > /tmp/_replay_env.sh; "
          "echo /testbed > /tmp/_replay_cwd", timeout=60)
    ex.put("/tmp/_replay_editor.py", EDITOR_HELPER)
    rc, start = ex.sh('cd /testbed && s=$(git stash create); if [ -n "$s" ]; then echo "$s"; '
                      'else git rev-parse HEAD; fi', timeout=60)
    return rc == 0, "ok", start.strip().splitlines()[-1] if start.strip() else None


def load_sample():
    sample = load_jsonl(os.path.join(OUT_DIR, "sample_rows.jsonl"))
    inst = json.load(open(os.path.join(OUT_DIR, "instances.json")))
    return sample, inst


def step_probe():
    header("PROBE: can the task environments reproduce what the agents saw?")
    sample, instances = load_sample()
    if BACKEND == "docker":
        rc = subprocess.run(["docker", "info"], capture_output=True).returncode
        out(f"  docker available: {rc == 0}")
        out("  " + subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.strip().replace("\n", "\n  "))
    first_inst = instances[sample[0]["cand"]["instance_id"]]
    out(f"  task instance fields: {sorted(first_inst)}")
    wins, pys, refs_used = Counter(), Counter(), Counter()
    all_scores = defaultdict(list)
    probe_runs = list({g["cand"]["repo"]: g for g in reversed(sample)}.values())[::-1][:PROBE_RUNS]
    for g in probe_runs:
        c, inst = g["cand"], instances[g["cand"]["instance_id"]]
        image = image_for(inst)
        out(f"\n  run {c['run_id']} ({c['instance_id']}), resolved={c['resolved']}, image {image}")
        f2p, p2p = as_list(inst.get("FAIL_TO_PASS")), as_list(inst.get("PASS_TO_PASS"))
        out(f"    FAIL_TO_PASS {len(f2p)} tests, e.g. {f2p[:2]}; PASS_TO_PASS {len(p2p)}; "
            f"bug patch {len(inst.get('patch') or '')} chars")
        if BACKEND == "docker":
            ok_pull, msg = pull(image)
            out(f"    docker pull: {'ok' if ok_pull else 'FAILED'} ({msg})")
            if not ok_pull:
                continue
        actions, edits = replay_plan(raw_messages(g["row"]))
        scores = {}
        for strat in STRATEGIES:
            ex = make_exec(image, f"probe_{c['run_id'][:8]}_{strat}", c["instance_id"])
            ex.start()
            try:
                ok, msg, start = setup(ex, inst, strat)
                scores[strat] = view_score(ex, actions) if ok else None
                out(f"    strategy {strat:<20} setup {'ok' if ok else 'failed: ' + msg[:90]}; "
                    f"match with the agent's first views: "
                    f"{'n/a' if scores[strat] is None else f'{100 * scores[strat]:.0f}%'}")
                if strat == "as_is":
                    _, state = ex.sh("cd /testbed && git status --short | head -5; git log -2 --oneline; "
                                     f"git branch -a 2>/dev/null | grep -c . ; {ACTIVATE}; which python; python --version",
                                     timeout=60)
                    out("      " + state.strip().replace("\n", "\n      ")[:600])
            finally:
                ex.stop()
        for strat in STRATEGIES:
            all_scores[strat].append(scores.get(strat) if scores.get(strat) is not None else -1.0)
        ranked = sorted((s for s in scores.items() if s[1] is not None),
                        key=lambda kv: (-kv[1], PREFERENCE.index(kv[0]) if kv[0] in PREFERENCE else 99))
        if not ranked:
            out("    no strategy reproduced the starting state")
            continue
        best = ranked[0][0]
        wins[best] += 1
        ex = make_exec(image, f"probe_{c['run_id'][:8]}_best", c["instance_id"])
        ex.start()
        try:
            ok, msg, start = setup(ex, inst, best)
            py = next((p for p in PY_CANDIDATES if ex.sh(f"{p} -c 'import json, os, sys'", timeout=60)[0] == 0), None)
            pys[py] += 1
            refs = [start] + [r for r in (inst.get("base_commit"), "HEAD", "HEAD~1") if r]
            w = warmup(ex, inst)
            out(f"    warm-up import of {w['module']}: exit {w['rc']} after {w['seconds']}s"
                + ("" if w["rc"] == 0 else f"; output tail: {w['tail']!r}"))
            for f in test_files(f2p)[:3]:
                found = [r for r in refs if ex.sh(f"cd /testbed && git cat-file -e {r}:'{f}' 2>/dev/null", timeout=30)[0] == 0]
                out(f"    test file {f}: in the working tree "
                    f"{ex.sh(f'test -e /testbed/{f}', timeout=30)[0] == 0}; available from refs {found or 'none'}")
                if found:
                    refs_used[found[0] == start] += 1
            f2p_s = random.Random(0).sample(f2p, min(len(f2p), F2P_PER_EDIT))
            t = time.time()
            res = run_tests(ex, f2p_s + p2p[:10], refs, TEST_TIMEOUT)
            s = summarize_tests(res, f2p_s, p2p[:10])
            out(f"    test run took {time.time() - t:.0f}s ({len(f2p_s)} of {len(f2p)} failing tests, "
                f"{len(p2p[:10])} passing)")
            out(f"    tests at the starting state: {s}")
            if not (s and s["parsed"]):
                out("      test output tail: " + res.get("tail", "")[-300:].replace("\n", " | "))
            elif s["fixed"]:
                out("      WARNING: the failing tests already pass, so this is not the task's starting state")
        finally:
            ex.stop()
            if BACKEND == "docker" and CLEAN_IMAGES:
                drop_image(image)
    if not wins:
        out("\n  No strategy worked; the replay cannot run. Share this report.")
        return
    # the strategy that works on every probed run (highest worst-case score); ties go to the order below,
    # which prefers the task's own branch because it also hides the failing tests, as the agent saw it
    chosen = max(STRATEGIES, key=lambda st: (min(all_scores[st]) if all_scores[st] else -1.0,
                                             -PREFERENCE.index(st) if st in PREFERENCE else -99))
    probe = {"strategy": chosen, "py": pys.most_common(1)[0][0]}
    with open(os.path.join(OUT_DIR, "probe.json"), "w") as f:
        json.dump(probe, f)
    out("\n  worst-case match with the agent's views across probed runs: " + ", ".join(
        f"{st} {'failed' if min(v) < 0 else f'{100 * min(v):.0f}%'}" for st, v in all_scores.items()))
    out(f"  chosen: strategy {chosen}, editor python {probe['py']}")


def replay_run(g, inst, image, probe):
    t0 = time.time()
    c = g["cand"]
    actions, edits = replay_plan(raw_messages(g["row"]))
    f2p, p2p = as_list(inst.get("FAIL_TO_PASS")), as_list(inst.get("PASS_TO_PASS"))
    rng = random.Random(int(c["run_id"], 16) % 10 ** 9)
    p2p_edit = rng.sample(p2p, min(len(p2p), P2P_PER_EDIT))
    p2p_final = rng.sample(p2p, min(len(p2p), P2P_FINAL))
    f2p_edit = rng.sample(f2p, min(len(f2p), F2P_PER_EDIT))
    f2p_final = rng.sample(f2p, min(len(f2p), F2P_FINAL))
    res = {k: c[k] for k in ("run_id", "instance_id", "repo", "model", "resolved", "legacy_eo")}
    res.update(strategy=probe["strategy"], image=image)
    ex = make_exec(image, f"replay_{c['run_id']}", c["instance_id"])
    ex.start()
    try:
        ok, msg, start = setup(ex, inst, probe["strategy"])
        res["setup_ok"] = ok
        if not ok:
            res["setup_error"] = msg
            return res
        refs = [start] + [r for r in (inst.get("base_commit"), "HEAD", "HEAD~1") if r]
        res["view_score"] = view_score(ex, actions)
        res["warmup"] = warmup(ex, inst)
        res["f2p_sampled"] = [len(f2p_edit), len(f2p_final), len(f2p)]
        res["start_tests"] = summarize_tests(run_tests(ex, f2p_edit + p2p_edit, refs, TEST_TIMEOUT), f2p_edit,
                                             p2p_edit)
        by_a = {e["a"]: e for e in edits}
        next_of = {e["_next"]: e["a"] for e in edits if e["_next"] is not None}
        execs, eds = [], []
        for i, a in enumerate(actions):
            if time.time() - t0 > RUN_BUDGET:
                res["stopped"] = "time budget"
                break
            if a["kind"] in ("U", "T"):
                break
            if a["kind"] == "E":
                e = by_a[i]
                r = editor_op(ex, probe["py"], a["args"], e["applied"])
                rec = dict(a=i, op=e["op"], scratch=e["scratch"], recorded_applied=e["applied"], replay_ok=r["ok"],
                           variant=r["variant"], msg=r["msg"][:80], next_exec=e["next_exec"],
                           next_exec_loose=e["next_exec_loose"], next_i=e["_next"])
                if r["ok"] and e["applied"] and not e["scratch"]:
                    rec["tests"] = summarize_tests(run_tests(ex, f2p_edit + p2p_edit, refs, TEST_TIMEOUT),
                                                   f2p_edit, p2p_edit)
                eds.append(rec)
            elif a["tool"] == "bash":
                rc, o = run_bash(ex, a["text"], CMD_TIMEOUT)
                if a["kind"] == "X" and i in next_of:
                    execs.append(dict(a=i, edit=next_of[i], rc=rc, timeout=rc == 124 or "__REPLAY_TIMEOUT__" in o,
                                      sim=round(similarity(a["out"], o), 3), recorded_strict=exec_state(a["out"])[0],
                                      replay_strict=exec_state(o)[0], replay_loose=exec_state_loose(o),
                                      replay_head=norm_output(o)[:160]))
        res["final_tests"] = summarize_tests(run_tests(ex, f2p_final + p2p_final, refs, TEST_TIMEOUT), f2p_final,
                                             p2p_final)
        res.update(execs=execs, edits=eds, seconds=round(time.time() - t0))
        return res
    finally:
        ex.stop()


def step_replay():
    header("REPLAY")
    probe = json.load(open(os.path.join(OUT_DIR, "probe.json")))
    sample, instances = load_sample()
    path = os.path.join(OUT_DIR, "results.jsonl")
    done = {r["run_id"] for r in load_jsonl(path)} if os.path.exists(path) else set()
    out(f"  {len(done & {g['cand']['run_id'] for g in sample})} of {len(sample)} runs already done; "
        f"continuing with the rest")
    groups = defaultdict(list)
    for g in sample:
        groups[image_for(instances[g["cand"]["instance_id"]])].append(g)
    for image, gs in groups.items():
        todo = [g for g in gs if g["cand"]["run_id"] not in done]
        if not todo:
            continue
        if BACKEND == "docker":
            ok_pull, msg = pull(image)
            if not ok_pull:
                out(f"  could not pull {image}: {msg}; its {len(todo)} runs are skipped and retried on the next resume")
                continue
        for g in todo:
            r = replay_run(g, instances[g["cand"]["instance_id"]], image, probe)
            with open(path, "a+") as f:  # start on a fresh line if an interruption cut the last one short
                f.seek(0, 2)
                if f.tell():
                    f.seek(f.tell() - 1)
                    if f.read(1) != "\n":
                        f.write("\n")
                f.write(json.dumps(r) + "\n")
            out(f"  {g['cand']['run_id']} {g['cand']['instance_id'][:50]}: setup {r.get('setup_ok')}, "
                f"views {r.get('view_score')}, {len(r.get('edits', []))} edits, {r.get('seconds')}s")
        if BACKEND == "docker" and CLEAN_IMAGES:
            drop_image(image)


def kappa(tp, fp, fn, tn):
    n = tp + fp + fn + tn
    if not n:
        return float("nan")
    po = (tp + tn) / n
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def agreement(rows, label, truth, rng):
    rows = [r for r in rows if r[truth] is not None]
    if not rows:
        return None
    def stats(rs):
        tp = sum(r[label] and r[truth] for r in rs)
        fp = sum(r[label] and not r[truth] for r in rs)
        fn = sum(not r[label] and r[truth] for r in rs)
        tn = sum(not r[label] and not r[truth] for r in rs)
        return tp, fp, fn, tn
    tp, fp, fn, tn = stats(rows)
    runs = sorted({r["run"] for r in rows})
    by_run = defaultdict(list)
    for r in rows:
        by_run[r["run"]].append(r)
    accs, ks = [], []
    for _ in range(1000):
        pick = [x for rid in rng.choices(runs, k=len(runs)) for x in by_run[rid]]
        a, b, c_, d = stats(pick)
        accs.append((a + d) / max(a + b + c_ + d, 1))
        ks.append(kappa(a, b, c_, d))
    accs.sort()
    ks = sorted(k for k in ks if k == k)
    ci = lambda v: (v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]) if v else (float("nan"), float("nan"))
    return dict(n=len(rows), runs=len(runs), tp=tp, fp=fp, fn=fn, tn=tn, acc=(tp + tn) / len(rows),
                acc_ci=ci(accs), kappa=kappa(tp, fp, fn, tn), kappa_ci=ci(ks))


def step_analyze():
    header("ANALYZE: replay fidelity, label validation, and harness-verified stopping")
    res = load_jsonl(os.path.join(OUT_DIR, "results.jsonl"))
    rng = random.Random(SEED)
    fid = Counter()
    faithful = []
    for r in res:
        fid["runs"] += 1
        if not r.get("setup_ok"):
            fid["setup failed"] += 1
            continue
        vs = r.get("view_score")
        ed = [e for e in r["edits"] if e["recorded_applied"] is not None and e["replay_ok"] is not None]
        ed_agree = sum(e["recorded_applied"] == e["replay_ok"] for e in ed) / len(ed) if ed else None
        ft, st = r.get("final_tests"), r.get("start_tests")
        final_res = bool(ft and ft["parsed"] and ft["fixed"] and ft["p2p_fail"] == 0) if ft and ft["parsed"] else None
        r["_final_res"] = final_res
        checks = {"starting files match the agent's views (>= 90%)": vs is None or vs >= 0.9,
                  "editor outcomes reproduce the recorded ones (>= 90%)": ed_agree is None or ed_agree >= 0.9,
                  "failing tests fail at the start": bool(st and st["parsed"] and not st["fixed"]),
                  "final tests reproduce the recorded resolved label": final_res is not None and final_res == r["resolved"]}
        for k, v in checks.items():
            fid[k] += v
        if all(checks.values()):
            faithful.append(r)
    out(f"  {fid['runs']} runs replayed; setup failed {fid['setup failed']}")
    for k in ("starting files match the agent's views (>= 90%)", "editor outcomes reproduce the recorded ones (>= 90%)",
              "failing tests fail at the start", "final tests reproduce the recorded resolved label"):
        out(f"    {k}: {fid[k]}")
    out(f"  faithful on every check: {len(faithful)} runs (only these enter the tables below)")
    sims = [x["sim"] for r in faithful for x in r["execs"]]
    if sims:
        out(f"  replayed execution outputs: median similarity to the recorded output {statistics.median(sims):.2f}; "
            f"{100 * sum(s >= 0.8 for s in sims) / len(sims):.0f}% at least 0.8")

    header("next_exec against objective ground truth (tested source edits in faithful runs)")
    untested = [(k, e["tests"]["fixed"]) for r in faithful for k, e in enumerate(
        [x for x in r["edits"] if x.get("tests") and x["tests"]["parsed"]]) if e["next_exec"] == "untested"]
    if untested:
        out(f"  edits the agent never tested: {len(untested)}; the task's failing tests pass after "
            f"{100 * sum(f for _, f in untested) / len(untested):.0f}% of them")
    rows = []
    for r in faithful:
        xs = {x["edit"]: x for x in r["execs"]}
        for e in r["edits"]:
            if e.get("tests") and e["tests"]["parsed"] and e["next_exec"] in ("pass", "fail"):
                x = xs.get(e["a"])
                rows.append(dict(run=r["run_id"], strict=e["next_exec"] == "fail", loose=e["next_exec_loose"] == "fail",
                                 exit_fail=(x["rc"] != 0) if x and not x["timeout"] and x["sim"] >= 0.8 else None,
                                 tests_fail=not e["tests"]["fixed"]))
    out(f"  {len(rows)} edits from {len({r['run'] for r in rows})} runs")
    names = {"exit_fail": "the next command's exit code (replayed; outputs reproduced >= 0.8)",
             "tests_fail": "the task's own failing tests after the edit"}
    for truth in ("exit_fail", "tests_fail"):
        out(f"\n  truth = {names[truth]}")
        for label in ("strict", "loose"):
            a = agreement(rows, label, truth, rng)
            if not a:
                out(f"    {label}: no rows")
                continue
            out(f"    {label:<6} agreement {100 * a['acc']:.1f}% [{100 * a['acc_ci'][0]:.1f}, {100 * a['acc_ci'][1]:.1f}], "
                f"kappa {a['kappa']:.2f} [{a['kappa_ci'][0]:.2f}, {a['kappa_ci'][1]:.2f}]; label fail & true fail "
                f"{a['tp']}, label fail & true pass {a['fp']}, label pass & true fail {a['fn']}, both pass {a['tn']} "
                f"(n={a['n']}, {a['runs']} runs)")
    gap = [r for r in rows if not r["strict"] and r["loose"]]
    if gap:
        ef = [r["exit_fail"] for r in gap if r["exit_fail"] is not None]
        out(f"\n  the blind spot (strict pass, loose fail): {len(gap)} edits; truly failing by exit code "
            f"{sum(ef)}/{len(ef)}, by the task's tests {sum(r['tests_fail'] for r in gap)}/{len(gap)}")

    header("EXPERIMENT A on these runs: stopping after the k-th source edit, scored by the task's tests")
    out("  'paper metric' = the submission's rescue rule on the old labels (a failed run counts as rescued if any")
    out("  earlier old-style edit looked clean); 'tests' = the code as it stood at the stop, run against the task's")
    out("  failing tests and a sample of its passing tests.")
    for k in (1, 2, 3, 5):
        n = resc = harm = resc_old = harm_old = 0
        for r in faithful:
            src = [e for e in r["edits"] if e.get("tests") and e["tests"]["parsed"]]
            n += 1
            if len(src) > k:
                t = src[k - 1]["tests"]
                fixed_k = t["fixed"] and t["p2p_fail"] == 0
                resc += (not r["resolved"]) and fixed_k
                harm += r["resolved"] and not fixed_k
            eo = r["legacy_eo"]
            if len(eo) > k:
                resc_old += (not r["resolved"]) and any(not x for x in eo[:k + 1])
                harm_old += bool(r["resolved"])
        if n:
            out(f"  k={k}: paper metric net {100 * (resc_old - harm_old) / n:+.1f}% "
                f"(rescued {resc_old}, harmed {harm_old}); tests net {100 * (resc - harm) / n:+.1f}% "
                f"(rescued {resc}, harmed {harm}); n={n}")
    any_fix = sum((not r["resolved"]) and any(e.get("tests") and e["tests"]["fixed"] and e["tests"]["p2p_fail"] == 0
                                              for e in r["edits"]) for r in faithful)
    out(f"  failed runs whose code passed the task's tests at some edit (the most any stopping rule could rescue): "
        f"{any_fix} of {sum(not r['resolved'] for r in faithful)}")


def save_report(name):
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(os.path.join(OUT_DIR, name), "w") as f:
            f.write("# " + name[:-3].replace("_", " ").title() + "\n\n```text\n" + "\n".join(LINES) + "\n```\n")
        print(f"\nwrote {os.path.join(OUT_DIR, name)}")
    except OSError as e:
        print(f"\ncould not write {name} ({e}); the report is the output above")


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--step", required=True, choices=["select", "fetch", "probe", "replay", "analyze"])
    step = p.parse_args(argv).step
    LINES.clear()
    {"select": step_select, "fetch": step_fetch, "probe": step_probe, "replay": step_replay,
     "analyze": step_analyze}[step]()
    save_report(f"REPLAY_{step.upper()}.md")


if __name__ == "__main__":
    main()
