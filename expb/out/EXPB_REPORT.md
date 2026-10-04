# Experiment B: results

Generated 2026-10-04 06:21 by `expb.py --step analyze` from `out/runs/*/*.summary.json` and the harness reports in `out/scores.json`. ANALYSIS_PLAN.md matches its recorded SHA-256; this expb.py matches the code hash recorded in the plan.

Outcome, unless stated otherwise: the harness result for the rule-built patch of the code at which a run submitted (its own submission or a budget stop); a run that submitted nothing is unresolved.

## 0. What ran

| Arm | Runs | Exits | Reruns | Infrastructure failures (unresolved) | Tracking errors | Command timeouts | Masked outputs | Format errors | Calls with reasoning |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 50 | {'Submitted': 50} | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| B0b | 50 | {'Submitted': 50} | 0 | 0 | 0 | 17 | 0 | 3 | 0 |
| k3 | 50 | {'Submitted': 37, 'BudgetStop': 13} | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| k3aware | 50 | {'Submitted': 40, 'BudgetStop': 10} | 0 | 0 | 0 | 7 | 0 | 0 | 0 |

Patches scored: 130 of 130 (unscorable after 3 attempts: 0; patch did not apply: 0). API cost from recorded tokens: $2.16 at peak prices, $1.08 if all off-peak (litellm's estimate: $1.08); cache hits 96.6% of prompt tokens. Calls whose tokens are unknown (format errors): 3.
Served model and fingerprint over all calls: {('deepseek-flash', 'aeb56401ca74e127821c4f9126dcb669'): 5435}; the pre-flight's: 'aeb56401ca74e127821c4f9126dcb669'.

## 1. Resolution by arm (primary)

B0 resolved 43/50 (86.0%, 95% CI 73.8-93.0).

| Arm | Resolved | vs B0: difference [95% CI] | B0 only / arm only | McNemar p | Holm p | Paper's predicted gain (its variant; without final-edit stops) | Interval excludes the prediction | Interval excludes 0 |
|---|---|---|---|---|---|---|---|---|
| B0b | 41/50 (82.0%, 95% CI 69.2-90.2) | -4.0 [-12.0, +4.0] | 3 / 1 | 0.625 | (secondary) | - | - | no |
| k3 | 40/50 (80.0%, 95% CI 67.0-88.8) | -6.0 [-16.0, +2.0] | 4 / 1 | 0.375 | 0.375 | -14.0; -4.0 | no | no |
| k3aware | 42/50 (84.0%, 95% CI 71.5-91.7) | -2.0 [-10.0, +6.0] | 3 / 2 | 1 | (secondary) | - | - | no |

Secondary outcome, the patch each run actually submitted:

B0 resolved 43/50 (86.0%, 95% CI 73.8-93.0).

| Arm | Resolved | vs B0: difference [95% CI] | McNemar p |
|---|---|---|---|
| B0b | 41/50 (82.0%, 95% CI 69.2-90.2) | -4.0 [-12.0, +4.0] | 0.625 |
| k3 | 40/50 (80.0%, 95% CI 67.0-88.8) | -6.0 [-16.0, +2.0] | 0.375 |
| k3aware | 42/50 (84.0%, 95% CI 71.5-91.7) | -2.0 [-10.0, +6.0] | 1 |

## 2. On-policy against off-policy (B1, GBvi 2) and stop-and-revert (B2)

For a silent stop, the k arm and B0's state at its k-th edit are two runs of the same process up to that edit; B0b's state at its k-th edit is a third. If off-policy evaluation is unbiased, the k arm disagrees with B0 as often as B0b does.

| k | Tasks | k arm vs B0@k: discordant | B0b@k vs B0@k: discordant | Difference [95% CI] | Verdict | Identical patches: arm vs B0@k; B0b@k vs B0@k |
|---|---|---|---|---|---|---|
| 3 | 50 | 6/50 (12.0%, 95% CI 5.6-23.8) | 9/50 (18.0%, 95% CI 9.8-30.8) | -6.0 [-18.0, +6.0] | no bias detected; |bias| bounded by 18.0 points | 48%; 42% |

| Arm (k) | Stop-and-revert, off-policy (B0) | Stop-and-revert, on-policy | Stop-and-submit, on-policy | Revert target differs from the stop state |
|---|---|---|---|---|
| k3 (3) | 40/50 (80.0%, 95% CI 67.0-88.8) | 40/50 (80.0%, 95% CI 67.0-88.8) | 40/50 (80.0%, 95% CI 67.0-88.8) | 0/13 (0.0%, 95% CI 0.0-22.8) of stops |
| k3aware (3) | 40/50 (80.0%, 95% CI 67.0-88.8) | 42/50 (84.0%, 95% CI 71.5-91.7) | 42/50 (84.0%, 95% CI 71.5-91.7) | 1/10 (10.0%, 95% CI 1.8-40.4) of stops |

## 3. How often each budget fired, and what it saved (B3)

| Arm | Budget fired | B0 runs reaching k edits | Calls: mean, vs B0 [95% CI] | Tokens processed (thousands): mean, vs B0 | Cost at peak $: mean, vs B0 |
|---|---|---|---|---|---|
| B0 | - | - | 30.04 | 419.99 | 0.01 |
| B0b | - | - | 31.96, +1.92 [-2.02, +5.82] | 434.09, +14.10 [-115.20, +117.71] | 0.01, +0.00 [-0.00, +0.00] |
| k3 | 13/50 (26.0%, 95% CI 15.9-39.6) | 11/50 (22.0%, 95% CI 12.8-35.2) | 23.12, -6.92 [-13.38, -1.70] | 216.76, -203.23 [-442.87, -29.32] | 0.01, -0.00 [-0.01, -0.00] |
| k3aware | 10/50 (20.0%, 95% CI 11.2-33.0) | 11/50 (22.0%, 95% CI 12.8-35.2) | 23.64, -6.40 [-11.96, -2.02] | 252.74, -167.25 [-367.14, -21.69] | 0.01, -0.00 [-0.01, -0.00] |

## 4. Could any stop rescue a failed B0 run? (B4, LiyU 1)

- Failed B0 runs rescued by an earlier state: Not run in this design: B0's intermediate states were not scored (B0_ALL_STATES = False). REPLAY_REPORT.md does this analysis on the paper's own runs.

- B0 runs whose submitted patch failed but whose code at submission resolves (how the patch was built, no stop involved): 0/7 (0.0%, 95% CI 0.0-35.4).
- First resolving state of resolved runs: Not run in this design: B0's intermediate states were not scored (B0_ALL_STATES = False). REPLAY_REPORT.md does this analysis on the paper's own runs.


## 5-6. The paper's metric against the harness, and step caps (B5, B6): Not run in this design: B0's intermediate states were not scored (B0_ALL_STATES = False). REPLAY_REPORT.md does this analysis on the paper's own runs.

## 7. The paper's DeepSeek edit detector against the recorded states (B7, GBvi 1)

- Truth = a source edit; `is_real_edit` on every command: precision 6/152 (3.9%, 95% CI 1.8-8.3), recall 6/106 (5.7%, 95% CI 2.6-11.8)
- Truth = a source edit; on each call's first command only (as cell 40): precision 6/148 (4.1%, 95% CI 1.9-8.6), recall 6/106 (5.7%, 95% CI 2.6-11.8)
- Truth = any file change; `is_real_edit` on every command: precision 40/152 (26.3%, 95% CI 20.0-33.8), recall 40/199 (20.1%, 95% CI 15.1-26.2)
- Truth = any file change; on each call's first command only (as cell 40): precision 40/148 (27.0%, 95% CI 20.5-34.7), recall 40/199 (20.1%, 95% CI 15.1-26.2)
- Calls with a source edit: 106/1502 (7.1%, 95% CI 5.9-8.5); median source edits per run 1.0 over a median of 24.0 calls (the paper: 5.2%, 2 edits, 48 steps, on its own model).

## 8. Edit labels against harness truth, B0's states (B8, LiyU 4)

- Not run in this design: B0's intermediate states were not scored (B0_ALL_STATES = False). REPLAY_REPORT.md does this analysis on the paper's own runs.

## 9. Patch construction, and B0 against the main run (B9)

- B0, patch submitted against code at submission: 43/50 against 43/50; resolved only as submitted 0, only as code 0.
- B0 (V4.1 Flash) against the main run (the retired V4-Flash preview), submitted patches, same tasks: main 39/50, B0 43/50; agreement 88.0%, main only 1, B0 only 5, McNemar p 0.219. This compares two models, not drift.

## 10. Budget-aware agent, tier 2, and the source-file audit (B10)

- k3aware: resolved 42/50 (84.0%, 95% CI 71.5-91.7); vs B0 -2.0 points [-10.0, +6.0], McNemar p 1; vs k3 +4.0 points [-6.0, +14.0], McNemar p 0.688; mean source edits 1.58 (B0 2.12); mean calls 23.6 (B0 30.0); submitted on its own before the budget fired: 40/50 (80.0%, 95% CI 67.0-88.8)
- norepeat: not run
- reward: not run
- New files counted as source (audit; path: snapshots seen): none

## Reading these results

- One run per task and arm at temperature 0; B0 against B0b shows how much a rerun changes.
- 100 tasks, one agent, one scaffold, a successor model: the intervals say what the data can resolve.
- k3aware and reward are prompted interventions; reward probes the hacking route, it is not an agent optimised against a process reward.
