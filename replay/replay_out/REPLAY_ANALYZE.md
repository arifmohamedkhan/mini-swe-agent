# Replay Analyze

```text

==============================================================================
ANALYZE: replay fidelity, label validation, and harness-verified stopping
==============================================================================
  58 runs replayed; setup failed 0
    starting files match the agent's views (>= 90%): 58
    editor outcomes reproduce the recorded ones (>= 90%): 57
    failing tests fail at the start: 41
    final tests reproduce the recorded resolved label: 37
  faithful on every check: 37 runs (only these enter the tables below)
  replayed execution outputs: median similarity to the recorded output 1.00; 91% at least 0.8

==============================================================================
next_exec against objective ground truth (tested source edits in faithful runs)
==============================================================================
  edits the agent never tested: 87; the task's failing tests pass after 3% of them
  133 edits from 37 runs

  truth = the next command's exit code (replayed; outputs reproduced >= 0.8)
    strict agreement 91.5% [84.8, 97.0], kappa 0.83 [0.69, 0.94]; label fail & true fail 46, label fail & true pass 10, label pass & true fail 0, both pass 62 (n=118, 36 runs)
    loose  agreement 73.7% [58.4, 86.7], kappa 0.51 [0.29, 0.73]; label fail & true fail 46, label fail & true pass 31, label pass & true fail 0, both pass 41 (n=118, 36 runs)

  truth = the task's own failing tests after the edit
    strict agreement 64.7% [51.3, 77.0], kappa 0.34 [0.17, 0.53]; label fail & true fail 55, label fail & true pass 2, label pass & true fail 45, both pass 31 (n=133, 37 runs)
    loose  agreement 79.7% [71.5, 86.7], kappa 0.55 [0.39, 0.70]; label fail & true fail 76, label fail & true pass 3, label pass & true fail 24, both pass 30 (n=133, 37 runs)

  the blind spot (strict pass, loose fail): 22 edits; truly failing by exit code 0/21, by the task's tests 21/22

==============================================================================
EXPERIMENT A on these runs: stopping after the k-th source edit, scored by the task's tests
==============================================================================
  'paper metric' = the submission's rescue rule on the old labels (a failed run counts as rescued if any
  earlier old-style edit looked clean); 'tests' = the code as it stood at the stop, run against the task's
  failing tests and a sample of its passing tests.
  k=1: paper metric net -13.5% (rescued 15, harmed 20); tests net -37.8% (rescued 0, harmed 14); n=37
  k=2: paper metric net -10.8% (rescued 16, harmed 20); tests net -27.0% (rescued 0, harmed 10); n=37
  k=3: paper metric net -8.1% (rescued 17, harmed 20); tests net -21.6% (rescued 0, harmed 8); n=37
  k=5: paper metric net -2.7% (rescued 16, harmed 17); tests net -18.9% (rescued 0, harmed 7); n=37
  failed runs whose code passed the task's tests at some edit (the most any stopping rule could rescue): 0 of 17
```
