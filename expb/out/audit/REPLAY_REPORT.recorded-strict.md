# The main-run replay: results

Generated 2026-10-05 20:49 by `expb.py --step analyze` from `out/replay/runs/*.summary.json` and the harness reports in `out/replay/scores.json`. ANALYSIS_PLAN.md matches its recorded SHA-256; this expb.py matches the code hash recorded in the plan.

## R1. Faithfulness

- Finished main runs: 418; replayed: 90; faithful (the replay's own submit command reproduced the recorded submission byte for byte): 73; not faithful: 15; ended at a limit, so uncertified: 2; infrastructure failures: 0.
- Share of a replay's commands whose output was at least 80% similar to the recorded output: median 0.97 (output similarity is reported, it certifies nothing).
- Not faithful (first 15): astropy__astropy-14365, django__django-14534, django__django-14752, django__django-16139, django__django-16595, pydata__xarray-4094, pytest-dev__pytest-7432, scikit-learn__scikit-learn-13142, sphinx-doc__sphinx-8721, sympy__sympy-12481, sympy__sympy-13031, sympy__sympy-18698, django__django-11848, astropy__astropy-14182, django__django-12308

## R2. The paper's DeepSeek detector and edit figures, on the paper's own runs (GBvi 1)

- Truth = a source edit; `is_real_edit` on every command: precision 68/177 (38.4%, 95% CI 31.6-45.8), recall 68/276 (24.6%, 95% CI 19.9-30.0)
- Truth = any file change; `is_real_edit` on every command: precision 68/177 (38.4%, 95% CI 31.6-45.8), recall 68/360 (18.9%, 95% CI 15.2-23.3)
- Calls with true source edits: 276/4771 (5.8%, 95% CI 5.2-6.5) in total; mean per run 5.5%, median 4.2%.
- Calls with `is_real_edit` (the paper's detector): 177/4771 (3.7%, 95% CI 3.2-4.3) in total; mean per run 4.0%, median 2.9%.
- Median source edits per run 2 over a median of 55 calls with commands. The paper reported 5.2% of steps, a median of 2 edits and 48 steps.

## R3. Could any stop have rescued a failed main run? (LiyU 1)

- faithful replays of submitted runs: failed runs with a resolving state a stop could have submitted: 5/43 (11.6%, 95% CI 5.1-24.5) (mwaskom__seaborn-3069, sphinx-doc__sphinx-10673, sympy__sympy-18763, django__django-11477, django__django-11790); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.
- replays of runs that ended at a limit (uncertified): failed runs with a resolving state a stop could have submitted: 0/2 (0.0%, 95% CI 0.0-65.8); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.

## R4. Step caps (LiyU 7)

No submission at the cap, over all 418 finished runs from their recorded call counts (305 resolved). Submit current changes at the cap, over the sampled tasks with faithful replays.

| Cap N | Runs longer than N | Kept, no submission | Calls used | Sample: kept, submit current | Sample: failed runs resolved at the cap |
|---|---|---|---|---|---|
| 15 | 407 | 9/305 (3.0%, 95% CI 1.6-5.5) | 26.1% | 6/30 (20.0%, 95% CI 9.5-37.3) | 0 |
| 25 | 343 | 64/305 (21.0%, 95% CI 16.8-25.9) | 42.0% | 11/30 (36.7%, 95% CI 21.9-54.5) | 0 |
| 50 | 192 | 190/305 (62.3%, 95% CI 56.7-67.5) | 69.5% | 23/30 (76.7%, 95% CI 59.1-88.2) | 0 |
| 75 | 86 | 262/305 (85.9%, 95% CI 81.5-89.4) | 83.5% | 29/30 (96.7%, 95% CI 83.3-99.4) | 0 |
| 100 | 49 | 284/305 (93.1%, 95% CI 89.7-95.5) | 90.4% | 30/30 (100.0%, 95% CI 88.6-100.0) | 0 |
| 150 | 14 | 302/305 (99.0%, 95% CI 97.1-99.7) | 96.9% | 30/30 (100.0%, 95% CI 88.6-100.0) | 0 |

## R5. The paper's stopping metric against the harness, on the paper's own runs (sampled tasks)

Two definitions of an edit: the paper's (commands flagged by `is_real_edit`, labelled by error keywords in their recorded output), and true source edits with the same labels. Net is a share of the sampled runs.

| Edits | k | Runs reaching k | Paper, its variant: rescued / harmed / net | Paper, without final-edit stops | Harness, stop-and-submit | Harness, stop-and-revert |
|---|---|---|---|---|---|---|
| paper's | 1 | 27 | 5 / 21 / -40.0% | 2 / 12 / -25.0% | 0 / 14 / -35.0% | 0 / 14 / -35.0% |
| paper's | 2 | 15 | 2 / 12 / -25.0% | 1 / 7 / -15.0% | 0 / 8 / -20.0% | 0 / 8 / -20.0% |
| paper's | 3 | 9 | 1 / 7 / -15.0% | 1 / 5 / -10.0% | 0 / 4 / -10.0% | 0 / 4 / -10.0% |
| paper's | 5 | 4 | 0 / 3 / -7.5% | 0 / 3 / -7.5% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
| paper's | 10 | 3 | 1 / 2 / -2.5% | 1 / 1 / +0.0% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
| paper's | 15 | 1 | 1 / 0 / +2.5% | 1 / 0 / +2.5% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |
| true | 1 | 40 | 10 / 30 / -50.0% | 3 / 15 / -30.0% | 1 / 10 / -22.5% | 1 / 10 / -22.5% |
| true | 2 | 18 | 3 / 15 / -30.0% | 1 / 11 / -25.0% | 0 / 8 / -20.0% | 0 / 6 / -15.0% |
| true | 3 | 12 | 1 / 11 / -25.0% | 0 / 5 / -12.5% | 0 / 4 / -10.0% | 0 / 4 / -10.0% |
| true | 5 | 5 | 0 / 5 / -12.5% | 0 / 3 / -7.5% | 0 / 2 / -5.0% | 0 / 2 / -5.0% |
| true | 10 | 3 | 0 / 3 / -7.5% | 0 / 3 / -7.5% | 0 / 2 / -5.0% | 0 / 2 / -5.0% |
| true | 15 | 2 | 0 / 2 / -5.0% | 0 / 2 / -5.0% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |

## R6. Edit labels against harness truth, the paper's own runs (LiyU 4)

- error keyword in the edit's recorded output (the paper's DeepSeek label): kappa 0.04 [0.01, 0.08] over 276 scored edits in 73 runs
- the next recorded execution before the next edit: kappa 0.05 [-0.07, 0.16] over 203 scored edits in 73 runs

## R7. Patch construction in the paper's own runs

- Faithful runs that left a new source file out of their submitted patch: 0/73 (0.0%, 95% CI 0.0-5.0); of them resolved: 0. {}
