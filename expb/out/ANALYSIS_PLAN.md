# Experiment B and the main-run replay: analysis plan (pre-registered)

Written by `expb.py --step select` on 2026-10-03 16:54 UTC, before any run. The analysis code is
`expb.py`, SHA-256 `1ee1d1435955ed95c779910348aabe88c1700ea1f0686431648b8191474dd48f`; its `step_analyze` produces every number below. This plan's own SHA-256 is in
`ANALYSIS_PLAN.sha256`. Commit all three before launching; the reports state whether plan and code still match.
Any deviation is reported with the results.

## Scope, fixed in advance by the compute available
The design was sized to about 15-20 hours on a 2-core machine. Fixed in the code: 50 tasks; arms
B0, B0b, k3, k3aware; B0's intermediate states scored: False; failed main runs replayed in addition to the
sample: 40. Analyses that need more are named below as not run, with what replaces them.

## The main run (the paper's DeepSeek run)
Trajectory files: {'Submitted': 413, 'no exit status': 14, 'LimitsExceeded': 5, 'unreadable': 1} (0 files whose image does not match the dataset row of the same index).
Finished runs (Submitted or LimitsExceeded): 418; harness outcome among them: {True: 305, False: 111, None: 2} (None: no report).
The main run's model, DeepSeek-V4-Flash preview served through the legacy name `deepseek-chat` in non-thinking mode,
has been retired by DeepSeek, so it can only be studied through its recorded trajectories.

## Part 1: replay of the main run (no API calls)
- **Which runs:** the 50 sampled tasks, plus 40 other failed main runs drawn with seed
  1. Each is replayed command by command in its own recorded task image and environment settings. Commands
  that hit the main run's 60 s limit get 60 s again; all others get 300 s. After every command the
  repository is snapshotted through a private git index.
- **Faithfulness:** a replay of a submitted run is faithful when its own submit command reproduces the recorded
  submission byte for byte. Only faithful replays (and replays of runs that ended at a limit, reported separately as
  uncertified) enter outcome analyses. Output similarity per command is reported but certifies nothing.
- **Scored by the harness** (swebench 5.0.2, clean containers): every distinct source state of every replayed run.
  The run's own outcome is the main run's harness result.
- **Analyses (all reported):**
  R1. Faithfulness: replayed, faithful, unfaithful, uncertified, infrastructure failures; output similarity.
  R2. GBvi 1 and the paper's figures: the paper's DeepSeek detector (`is_real_edit`, cell 40) against the recorded
      source edits, precision and recall per command; the true share of model calls with a source edit and the
      median number of source edits per run, against the paper's 5.2%, 2 and 48.
  R3. LiyU 1: failed main runs with a source state that resolves, before the final edit (a stop could rescue them)
      and only at the final state (how the patch was built, no stop needed); Wilson 95% interval.
  R4. LiyU 7: step caps N = 15, 25, 50, 75, 100, 150. Resolutions kept when a capped run submits nothing
      (mini-swe-agent's behaviour), over all 418 finished runs from their recorded call counts; and when a capped
      run submits its current changes, over the sampled tasks, scored.
  R5. The paper's stopping metric against the harness on the sampled tasks, two ways: the paper's own definition
      (edits found by `is_real_edit`, labels from the error keywords in each edit's recorded output) and true source
      edits; stop after edit k for k = 1, 2, 3, 5, 10, 15, stop-and-submit and stop-and-revert.
  R6. LiyU 4: each scored source state's label (error keyword in its recorded output; and the next execution's)
      against "the code at this state resolves the task", Cohen's kappa with a run-level bootstrap interval.
  R7. Patch construction: new source files present at submission but absent from the submitted patch.

## Part 2: Experiment B (on-policy)
- **Agent:** mini-swe-agent 2.3.0 (the released wheel the main run used), the main run's configuration (built-in
  `swebench.yaml`: templates, temperature 0, parallel tool calls, 250 steps, $3, 60 s command limit), model
  `deepseek/deepseek-flash` (DeepSeek-V4.1-Flash) with thinking disabled. The non-interactive `DefaultAgent` replaces the main
  run's `InteractiveAgent` (yolo); the main run's only extra user messages were format-error notices, which DefaultAgent
  sends too. Costs are computed from recorded tokens at DeepSeek's peak prices; the served fingerprint is fixed by a
  pre-flight call, and a change stops the experiment.
- **Tasks:** 50 of the 418 finished main runs, stratified by repository with proportional allocation,
  seed 0: {'django/django': 26, 'sympy/sympy': 6, 'sphinx-doc/sphinx': 5, 'astropy/astropy': 3, 'scikit-learn/scikit-learn': 3, 'pydata/xarray': 2, 'pytest-dev/pytest': 2, 'matplotlib/matplotlib': 1, 'psf/requests': 1, 'pylint-dev/pylint': 1, 'mwaskom/seaborn': 0, 'pallets/flask': 0}. The same tasks in every arm; all arms run together.
- **Arms:**

| Arm | Edit budget k | What changes |
|---|---|---|
| B0 | - | unchanged agent |
| B0b | - | unchanged agent, second run (noise floor) |
| k3 | 3 | silent stop after the 3rd source edit |
| k3aware | 3 | told of a 3-edit budget, stopped after the 3rd source edit |

  k3aware's note is appended to the end of the task prompt, verbatim: "## Edit budget  This task has an edit budget. After your 3rd command that changes the repository's source files (tests, configuration files and new scripts in the repository root do not count), your current changes are submitted automatically as your final answer and the task ends. Plan your changes accordingly."
- **Source edit:** a command after which the content of the repository's source files differs from the previous
  snapshot. Source files: files tracked at the start, except tests (`test/`, `tests/`, `testing/` at the top level, any
  `tests/` folder, `test_*.py`, `*_test(s).py`, `tests.py`, `conftest.py`), configuration (`setup.py`, `setup.cfg`,
  `pyproject.toml`, `tox.ini`, `requirements*`, dotfiles and similar) and build output; plus files created during the
  run below the repository root with a code extension and a non-scratch name. Binary changes never count. Reverting
  is an edit too.
- **Stopping:** right after the command that makes the 3rd source edit, the run ends and its source changes are
  submitted as a rule-built patch (other commands of the same model turn are not run).
- **Outcome.** Primary, in every arm: the harness result for the rule-built patch of the state at which the run
  submitted (its own submission or a budget stop); a run that submits nothing is unresolved. Secondary: the harness
  result for the patch actually submitted. Both are reported.
- **Scored:** every arm's submission and code at submission; B0's and B0b's states at their 3rd source edit and B0's
  stop-and-revert target there; each budget stop's stop-and-revert target. Empty patches are unresolved.
- **Infrastructure failures** (exits other than ['BudgetStop', 'ContextWindowExceededError', 'LimitsExceeded', 'Submitted', 'TimeExceeded']) are rerun up to 3 attempts; a
  run that still fails counts as unresolved. An API key or balance error stops the step instead of using attempts.
- **Primary analysis:** k3 against B0 on the same tasks: difference in resolution with a 95% bootstrap interval
  over tasks and the exact McNemar test. Decision rules, fixed now: (a) the interval is compared with the gain the
  paper's own metric predicts for k = 3 on B0's runs (computed from B0's edit labels and outcomes, the paper's variant
  and the variant without final-edit stops): the prediction is refuted if the interval excludes it; (b) stopping
  changes resolution if the interval excludes zero. Results are reported whatever they show.
- **Secondary analyses (all reported):**
  B1. GBvi 2, on-policy against off-policy at k = 3: discordance between k3 and B0's own state at its 3rd edit,
      against the discordance between B0b's and B0's states there (the like-for-like noise floor). The off-policy
      estimate counts as biased if the 95% interval of the difference excludes zero; otherwise that interval bounds
      the bias. Byte-identity of the compared patches is reported.
  B2. Stop-and-revert at k = 3, on-policy (k3, k3aware) and off-policy (B0); how often the revert target differs.
  B3. How often each budget fires; calls, tokens processed and cost per arm against B0.
  B7. GBvi 1 on B0: the paper's detector against the recorded states (needs no scoring).
  B9. Patch construction (B0's own patch against its code at submission), and B0 against the main run on the same
      tasks, which compares two models (V4.1 Flash against the retired V4-Flash preview), not drift.
  B10. LiyU 2: k3aware against k3 and B0 (does a budget-aware agent adapt: edits used, own submissions, resolution).
- **Not run in this design**, with what replaces them: B0's rescue ceiling, the paper's metric against the harness,
  step caps and label agreement on V4.1 Flash (R3-R6 do these on the paper's own runs); the k1 and k10 arms (R5
  evaluates stopping at every k on the paper's own runs); the norepeat and reward arms (9VzP 1 and F32e 2 get
  descriptive measurements from the replay and the main run's trajectories, not a causal test).
