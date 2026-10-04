# The main-run replay: results

Generated 2026-10-04 16:20 by `expb.py --step analyze` from `out/replay/runs/*.summary.json` and the harness reports in `out/replay/scores.json`. ANALYSIS_PLAN.md matches its recorded SHA-256; this expb.py matches the code hash recorded in the plan.

## R1. Faithfulness

- Finished main runs: 418; replayed: 90; faithful (the replay's own submit command reproduced the recorded submission byte for byte): 87; not faithful: 1; ended at a limit, so uncertified: 2; infrastructure failures: 0.
- Share of a replay's commands whose output was at least 80% similar to the recorded output: median 0.97 (output similarity is reported, it certifies nothing).
- Not faithful (first 15): sympy__sympy-12481

## R2. The paper's DeepSeek detector and edit figures, on the paper's own runs (GBvi 1)

- Truth = a source edit; `is_real_edit` on every command: precision 74/209 (35.4%, 95% CI 29.2-42.1), recall 74/299 (24.7%, 95% CI 20.2-29.9)
- Truth = any file change; `is_real_edit` on every command: precision 74/209 (35.4%, 95% CI 29.2-42.1), recall 74/397 (18.6%, 95% CI 15.1-22.8)
- Calls with true source edits: 299/5419 (5.5%, 95% CI 4.9-6.2) in total; mean per run 5.2%, median 3.9%.
- Calls with `is_real_edit` (the paper's detector): 209/5419 (3.9%, 95% CI 3.4-4.4) in total; mean per run 4.1%, median 2.6%.
- Median source edits per run 1 over a median of 53 calls with commands. The paper reported 5.2% of steps, a median of 2 edits and 48 steps.

## R3. Could any stop have rescued a failed main run? (LiyU 1)

- faithful replays of submitted runs: failed runs with a resolving state a stop could have submitted: 6/49 (12.2%, 95% CI 5.7-24.2) (mwaskom__seaborn-3069, sphinx-doc__sphinx-10673, sympy__sympy-18698, sympy__sympy-18763, django__django-11477, django__django-11790); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.
- replays of runs that ended at a limit (uncertified): failed runs with a resolving state a stop could have submitted: 0/2 (0.0%, 95% CI 0.0-65.8); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.

## R4. Step caps (LiyU 7)

No submission at the cap, over all 418 finished runs from their recorded call counts (305 resolved). Submit current changes at the cap, over the sampled tasks with faithful replays.

| Cap N | Runs longer than N | Kept, no submission | Calls used | Sample: kept, submit current | Sample: failed runs resolved at the cap |
|---|---|---|---|---|---|
| 15 | 407 | 9/305 (3.0%, 95% CI 1.6-5.5) | 26.1% | 9/38 (23.7%, 95% CI 13.0-39.2) | 0 |
| 25 | 343 | 64/305 (21.0%, 95% CI 16.8-25.9) | 42.0% | 16/38 (42.1%, 95% CI 27.9-57.8) | 0 |
| 50 | 192 | 190/305 (62.3%, 95% CI 56.7-67.5) | 69.5% | 30/38 (78.9%, 95% CI 63.7-88.9) | 0 |
| 75 | 86 | 262/305 (85.9%, 95% CI 81.5-89.4) | 83.5% | 37/38 (97.4%, 95% CI 86.5-99.5) | 0 |
| 100 | 49 | 284/305 (93.1%, 95% CI 89.7-95.5) | 90.4% | 38/38 (100.0%, 95% CI 90.8-100.0) | 0 |
| 150 | 14 | 302/305 (99.0%, 95% CI 97.1-99.7) | 96.9% | 38/38 (100.0%, 95% CI 90.8-100.0) | 0 |

## R5. The paper's stopping metric against the harness, on the paper's own runs (sampled tasks)

Two definitions of an edit: the paper's (commands flagged by `is_real_edit`, labelled by error keywords in their recorded output), and true source edits with the same labels. Net is a share of the sampled runs.

| Edits | k | Runs reaching k | Paper, its variant: rescued / harmed / net | Paper, without final-edit stops | Harness, stop-and-submit | Harness, stop-and-revert |
|---|---|---|---|---|---|---|
| paper's | 1 | 32 | 6 / 25 / -38.8% | 2 / 13 / -22.4% | 0 / 15 / -30.6% | 0 / 15 / -30.6% |
| paper's | 2 | 16 | 2 / 13 / -22.4% | 1 / 8 / -14.3% | 0 / 8 / -16.3% | 0 / 8 / -16.3% |
| paper's | 3 | 10 | 1 / 8 / -14.3% | 1 / 6 / -10.2% | 0 / 5 / -10.2% | 0 / 5 / -10.2% |
| paper's | 5 | 5 | 0 / 4 / -8.2% | 0 / 4 / -8.2% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
| paper's | 10 | 4 | 1 / 3 / -4.1% | 1 / 2 / -2.0% | 0 / 1 / -2.0% | 0 / 1 / -2.0% |
| paper's | 15 | 2 | 1 / 1 / +0.0% | 1 / 0 / +2.0% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |
| true | 1 | 49 | 11 / 38 / -55.1% | 3 / 16 / -26.5% | 1 / 10 / -18.4% | 1 / 10 / -18.4% |
| true | 2 | 19 | 3 / 16 / -26.5% | 1 / 12 / -22.4% | 0 / 9 / -18.4% | 0 / 7 / -14.3% |
| true | 3 | 13 | 1 / 12 / -22.4% | 0 / 6 / -12.2% | 0 / 5 / -10.2% | 0 / 5 / -10.2% |
| true | 5 | 6 | 0 / 6 / -12.2% | 0 / 4 / -8.2% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
| true | 10 | 3 | 0 / 3 / -6.1% | 0 / 3 / -6.1% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
| true | 15 | 2 | 0 / 2 / -4.1% | 0 / 2 / -4.1% | 0 / 1 / -2.0% | 0 / 1 / -2.0% |

## R6. Edit labels against harness truth, the paper's own runs (LiyU 4)

- error keyword in the edit's recorded output (the paper's DeepSeek label): kappa 0.05 [0.02, 0.09] over 299 scored edits in 87 runs
- the next recorded execution before the next edit: kappa 0.05 [-0.08, 0.16] over 221 scored edits in 87 runs

## R7. Patch construction in the paper's own runs

- Faithful runs that left a new source file out of their submitted patch: 0/87 (0.0%, 95% CI 0.0-4.2); of them resolved: 0. {}
