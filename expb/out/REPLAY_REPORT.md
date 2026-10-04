# The main-run replay: results

Generated 2026-10-04 06:21 by `expb.py --step analyze` from `out/replay/runs/*.summary.json` and the harness reports in `out/replay/scores.json`. ANALYSIS_PLAN.md matches its recorded SHA-256; this expb.py matches the code hash recorded in the plan.

## R1. Faithfulness

- Finished main runs: 418; replayed: 68; faithful (the replay's own submit command reproduced the recorded submission byte for byte): 55; not faithful: 11; ended at a limit, so uncertified: 2; infrastructure failures: 0.
- Share of a replay's commands whose output was at least 80% similar to the recorded output: median 0.97 (output similarity is reported, it certifies nothing).
- Not faithful (first 15): astropy__astropy-14365, django__django-14534, django__django-14752, django__django-16139, django__django-16595, pydata__xarray-4094, pytest-dev__pytest-7432, scikit-learn__scikit-learn-13142, django__django-11848, astropy__astropy-14182, django__django-12308

## R2. The paper's DeepSeek detector and edit figures, on the paper's own runs (GBvi 1)

- Truth = a source edit; `is_real_edit` on every command: precision 50/130 (38.5%, 95% CI 30.5-47.0), recall 50/183 (27.3%, 95% CI 21.4-34.2)
- Truth = any file change; `is_real_edit` on every command: precision 50/130 (38.5%, 95% CI 30.5-47.0), recall 50/248 (20.2%, 95% CI 15.6-25.6)
- Calls with true source edits: 183/3405 (5.4%, 95% CI 4.7-6.2) in total; mean per run 5.3%, median 4.1%.
- Calls with `is_real_edit` (the paper's detector): 130/3405 (3.8%, 95% CI 3.2-4.5) in total; mean per run 4.1%, median 2.9%.
- Median source edits per run 2 over a median of 54 calls with commands. The paper reported 5.2% of steps, a median of 2 edits and 48 steps.

## R3. Could any stop have rescued a failed main run? (LiyU 1)

- faithful replays of submitted runs: failed runs with a resolving state a stop could have submitted: 3/33 (9.1%, 95% CI 3.1-23.6) (mwaskom__seaborn-3069, django__django-11477, django__django-11790); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.
- replays of runs that ended at a limit (uncertified): failed runs with a resolving state a stop could have submitted: 0/2 (0.0%, 95% CI 0.0-65.8); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.

## R4. Step caps (LiyU 7)

No submission at the cap, over all 418 finished runs from their recorded call counts (305 resolved). Submit current changes at the cap, over the sampled tasks with faithful replays.

| Cap N | Runs longer than N | Kept, no submission | Calls used | Sample: kept, submit current | Sample: failed runs resolved at the cap |
|---|---|---|---|---|---|
| 15 | 407 | 9/305 (3.0%, 95% CI 1.6-5.5) | 26.1% | 6/22 (27.3%, 95% CI 13.2-48.2) | 0 |
| 25 | 343 | 64/305 (21.0%, 95% CI 16.8-25.9) | 42.0% | 10/22 (45.5%, 95% CI 26.9-65.3) | 0 |
| 50 | 192 | 190/305 (62.3%, 95% CI 56.7-67.5) | 69.5% | 17/22 (77.3%, 95% CI 56.6-89.9) | 0 |
| 75 | 86 | 262/305 (85.9%, 95% CI 81.5-89.4) | 83.5% | 21/22 (95.5%, 95% CI 78.2-99.2) | 0 |
| 100 | 49 | 284/305 (93.1%, 95% CI 89.7-95.5) | 90.4% | 22/22 (100.0%, 95% CI 85.1-100.0) | 0 |
| 150 | 14 | 302/305 (99.0%, 95% CI 97.1-99.7) | 96.9% | 22/22 (100.0%, 95% CI 85.1-100.0) | 0 |

## R5. The paper's stopping metric against the harness, on the paper's own runs (sampled tasks)

Two definitions of an edit: the paper's (commands flagged by `is_real_edit`, labelled by error keywords in their recorded output), and true source edits with the same labels. Net is a share of the sampled runs.

| Edits | k | Runs reaching k | Paper, its variant: rescued / harmed / net | Paper, without final-edit stops | Harness, stop-and-submit | Harness, stop-and-revert |
|---|---|---|---|---|---|---|
| paper's | 1 | 22 | 5 / 16 / -35.5% | 2 / 8 / -19.4% | 0 / 9 / -29.0% | 0 / 9 / -29.0% |
| paper's | 2 | 11 | 2 / 8 / -19.4% | 1 / 4 / -9.7% | 0 / 4 / -12.9% | 0 / 4 / -12.9% |
| paper's | 3 | 6 | 1 / 4 / -9.7% | 1 / 2 / -3.2% | 0 / 2 / -6.5% | 0 / 2 / -6.5% |
| paper's | 5 | 3 | 0 / 2 / -6.5% | 0 / 2 / -6.5% | 0 / 1 / -3.2% | 0 / 1 / -3.2% |
| paper's | 10 | 3 | 1 / 2 / -3.2% | 1 / 1 / +0.0% | 0 / 1 / -3.2% | 0 / 1 / -3.2% |
| paper's | 15 | 1 | 1 / 0 / +3.2% | 1 / 0 / +3.2% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |
| true | 1 | 31 | 9 / 22 / -41.9% | 3 / 9 / -19.4% | 1 / 4 / -9.7% | 1 / 4 / -9.7% |
| true | 2 | 12 | 3 / 9 / -19.4% | 1 / 5 / -12.9% | 0 / 4 / -12.9% | 0 / 2 / -6.5% |
| true | 3 | 6 | 1 / 5 / -12.9% | 0 / 2 / -6.5% | 0 / 1 / -3.2% | 0 / 1 / -3.2% |
| true | 5 | 2 | 0 / 2 / -6.5% | 0 / 1 / -3.2% | 0 / 1 / -3.2% | 0 / 1 / -3.2% |
| true | 10 | 1 | 0 / 1 / -3.2% | 0 / 1 / -3.2% | 0 / 1 / -3.2% | 0 / 1 / -3.2% |
| true | 15 | 0 | 0 / 0 / +0.0% | 0 / 0 / +0.0% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |

## R6. Edit labels against harness truth, the paper's own runs (LiyU 4)

- error keyword in the edit's recorded output (the paper's DeepSeek label): kappa 0.04 [0.01, 0.09] over 183 scored edits in 55 runs
- the next recorded execution before the next edit: kappa -0.01 [-0.15, 0.13] over 124 scored edits in 55 runs

## R7. Patch construction in the paper's own runs

- Faithful runs that left a new source file out of their submitted patch: 0/55 (0.0%, 95% CI 0.0-6.5); of them resolved: 0. {}
