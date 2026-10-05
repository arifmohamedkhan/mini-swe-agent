# Replay Analyze

```text

==============================================================================
ANALYZE: replay fidelity, label validation, and harness-verified stopping
==============================================================================
  58 runs replayed; faithful on every check: 44 (22 resolved, 22 failed); of all replayed runs, 30 resolved
    runs failing a check on final: 14
    runs failing a check on start: 10
    runs failing a check on editor outcomes reproduced only 50%: 1
  (only faithful runs enter the tables below; --step diagnose lists the reasons per run)
  replayed execution outputs: median similarity to the recorded output 1.00; 91% at least 0.8

==============================================================================
next_exec against objective ground truth (tested source edits in faithful runs)
==============================================================================
  edits the agent never tested: 97; the task's failing tests pass after 5% of them
  161 edits from 44 runs

  truth = the next command's exit code (replayed; outputs reproduced >= 0.8)
    strict agreement 93.0% [87.7, 97.6], kappa 0.85 [0.73, 0.95]; label fail & true fail 48, label fail & true pass 10, label pass & true fail 0, both pass 85 (n=143, 41 runs)
    loose  agreement 73.4% [59.3, 86.1], kappa 0.50 [0.29, 0.72]; label fail & true fail 48, label fail & true pass 38, label pass & true fail 0, both pass 57 (n=143, 41 runs)

  truth = the task's own failing tests after the edit
    strict agreement 58.4% [45.2, 71.5], kappa 0.27 [0.13, 0.44]; label fail & true fail 58, label fail & true pass 2, label pass & true fail 65, both pass 36 (n=161, 44 runs)
    loose  agreement 75.2% [66.4, 82.6], kappa 0.47 [0.31, 0.62]; label fail & true fail 86, label fail & true pass 3, label pass & true fail 37, both pass 35 (n=161, 44 runs)

  in failed runs whose code never passed the task's tests (22 of 22), the agent's own next check passed after 49/90 tested edits (strict) and 28/90 (loose); each such pass is false
  failed runs whose last tested edit's check passed (the agent stopped on a passing check of code that does not work): 18 of 22

  the blind spot (strict pass, loose fail): 29 edits; truly failing by exit code 0/28, by the task's tests 28/29

==============================================================================
EXPERIMENT A on these runs: stopping after the k-th source edit, scored by the task's tests
==============================================================================
  'paper metric' = the submission's rescue rule on the old labels (a failed run counts as rescued if any
  earlier old-style edit looked clean); 'tests' = the code as it stood at the stop, run against the task's
  failing tests and a sample of its passing tests.
  k=1: paper metric net -6.8% (rescued 19, harmed 22); tests net -36.4% (rescued 0, harmed 16); n=44
  k=2: paper metric net -2.3% (rescued 21, harmed 22); tests net -22.7% (rescued 0, harmed 10); n=44
  k=3: paper metric net +0.0% (rescued 22, harmed 22); tests net -18.2% (rescued 0, harmed 8); n=44
  k=5: paper metric net +2.3% (rescued 20, harmed 19); tests net -15.9% (rescued 0, harmed 7); n=44

==============================================================================
THE TASK'S TESTS AFTER EVERY SOURCE EDIT (objective progress, faithful runs)
==============================================================================
  after source edit 1: tests pass in 6/44 runs (14%)
  after source edit 2: tests pass in 7/37 runs (19%)
  after source edit 3: tests pass in 6/30 runs (20%)
  after source edit 4: tests pass in 3/24 runs (12%)
  after source edit 5: tests pass in 3/21 runs (14%)
  after source edit 6: tests pass in 4/17 runs (24%)
  after source edit 7: tests pass in 2/15 runs (13%)
  after source edit 8: tests pass in 5/15 runs (33%)
  resolved runs: first edit after which the tests pass, median 2 (range 1-11; 21 runs)
  runs whose tests passed at some edit and failed again at a later one (a working fix broken): 1 of 21
  failed runs whose code passed the task's tests at some edit (the most any stopping rule could rescue): 0 of 22
```
