# Reports rebuilt from the recorded and the corrected verdicts

Written 2026-10-05 20:49:40 UTC by `expb_audit.py reports`, with expb.py's own report code. 'strict': the plan's byte-for-byte rule, so 14 replays count as unfaithful: ['astropy__astropy-14182', 'astropy__astropy-14365', 'django__django-11848', 'django__django-12308', 'django__django-14534', 'django__django-14752', 'django__django-16139', 'django__django-16595', 'pydata__xarray-4094', 'pytest-dev__pytest-7432', 'scikit-learn__scikit-learn-13142', 'sphinx-doc__sphinx-8721', 'sympy__sympy-13031', 'sympy__sympy-18698']. 'corrected': 16 verdict(s) replaced after two agreeing clean rescorings:

- replay django__django-14752 cd23498d74558083: None -> True (changed)
- replay django__django-16139 fe56021389b4cda6: None -> True (changed)
- replay django__django-16595 f5e377c1505d5fd4: None -> True (changed)
- replay pydata__xarray-4094 b3bdb842572f8c90: None -> True (changed)
- replay pytest-dev__pytest-7432 188f4fba09fbf790: None -> True (changed)
- replay pytest-dev__pytest-7432 6ddcf9783057f707: None -> False (changed)
- replay pytest-dev__pytest-7432 bb86473d6d7a3d4c: None -> True (changed)
- replay scikit-learn__scikit-learn-13142 283882ad87507dbf: None -> True (changed)
- replay sphinx-doc__sphinx-8721 d50eb9525405f1e2: None -> True (changed)
- replay astropy__astropy-14182 54985d3e20dcd0db: None -> False (changed)
- replay astropy__astropy-14365 a6a0727c6774e3a1: None -> False (changed)
- replay django__django-11848 0de9b02513302b3f: None -> False (changed)
- replay django__django-12308 5001f711dd815212: None -> False (changed)
- replay django__django-14534 a13c67915adab750: None -> False (changed)
- replay sympy__sympy-18698 2c7cf9a45690c7ba: None -> True (changed)
- replay sympy__sympy-18698 323cec6699e055ea: None -> False (changed)

## EXPB_REPORT.md as committed -> recorded: no change

## REPLAY_REPORT.md as committed -> recorded: no change

## REPLAY_REPORT recorded -> recorded-strict: 58 changed line(s)
```
-- Finished main runs: 418; replayed: 90; faithful (the replay's own submit command reproduced the recorded submission byte for byte): 87; not faithful: 1; ended at a limit, so uncertified: 2; infrastructure failures: 0.
+- Finished main runs: 418; replayed: 90; faithful (the replay's own submit command reproduced the recorded submission byte for byte): 73; not faithful: 15; ended at a limit, so uncertified: 2; infrastructure failures: 0.
-- Not faithful (first 15): sympy__sympy-12481
+- Not faithful (first 15): astropy__astropy-14365, django__django-14534, django__django-14752, django__django-16139, django__django-16595, pydata__xarray-4094, pytest-dev__pytest-7432, scikit-learn__scikit-learn-13142, sphinx-doc__sphinx-8721, sympy__sympy-12481, sympy__sympy-13031, sympy__sympy-18698, django__django-11848, astropy__astropy-14182, django__django-12308
-- Truth = a source edit; `is_real_edit` on every command: precision 74/209 (35.4%, 95% CI 29.2-42.1), recall 74/299 (24.7%, 95% CI 20.2-29.9)
-- Truth = any file change; `is_real_edit` on every command: precision 74/209 (35.4%, 95% CI 29.2-42.1), recall 74/397 (18.6%, 95% CI 15.1-22.8)
-- Calls with true source edits: 299/5419 (5.5%, 95% CI 4.9-6.2) in total; mean per run 5.2%, median 3.9%.
-- Calls with `is_real_edit` (the paper's detector): 209/5419 (3.9%, 95% CI 3.4-4.4) in total; mean per run 4.1%, median 2.6%.
-- Median source edits per run 1 over a median of 53 calls with commands. The paper reported 5.2% of steps, a median of 2 edits and 48 steps.
+- Truth = a source edit; `is_real_edit` on every command: precision 68/177 (38.4%, 95% CI 31.6-45.8), recall 68/276 (24.6%, 95% CI 19.9-30.0)
+- Truth = any file change; `is_real_edit` on every command: precision 68/177 (38.4%, 95% CI 31.6-45.8), recall 68/360 (18.9%, 95% CI 15.2-23.3)
+- Calls with true source edits: 276/4771 (5.8%, 95% CI 5.2-6.5) in total; mean per run 5.5%, median 4.2%.
+- Calls with `is_real_edit` (the paper's detector): 177/4771 (3.7%, 95% CI 3.2-4.3) in total; mean per run 4.0%, median 2.9%.
+- Median source edits per run 2 over a median of 55 calls with commands. The paper reported 5.2% of steps, a median of 2 edits and 48 steps.
-- faithful replays of submitted runs: failed runs with a resolving state a stop could have submitted: 6/49 (12.2%, 95% CI 5.7-24.2) (mwaskom__seaborn-3069, sphinx-doc__sphinx-10673, sympy__sympy-18698, sympy__sympy-18763, django__django-11477, django__django-11790); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.
+- faithful replays of submitted runs: failed runs with a resolving state a stop could have submitted: 5/43 (11.6%, 95% CI 5.1-24.5) (mwaskom__seaborn-3069, sphinx-doc__sphinx-10673, sympy__sympy-18763, django__django-11477, django__django-11790); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.
-| 15 | 407 | 9/305 (3.0%, 95% CI 1.6-5.5) | 26.1% | 9/38 (23.7%, 95% CI 13.0-39.2) | 0 |
-| 25 | 343 | 64/305 (21.0%, 95% CI 16.8-25.9) | 42.0% | 16/38 (42.1%, 95% CI 27.9-57.8) | 0 |
-| 50 | 192 | 190/305 (62.3%, 95% CI 56.7-67.5) | 69.5% | 30/38 (78.9%, 95% CI 63.7-88.9) | 0 |
-| 75 | 86 | 262/305 (85.9%, 95% CI 81.5-89.4) | 83.5% | 37/38 (97.4%, 95% CI 86.5-99.5) | 0 |
-| 100 | 49 | 284/305 (93.1%, 95% CI 89.7-95.5) | 90.4% | 38/38 (100.0%, 95% CI 90.8-100.0) | 0 |
-| 150 | 14 | 302/305 (99.0%, 95% CI 97.1-99.7) | 96.9% | 38/38 (100.0%, 95% CI 90.8-100.0) | 0 |
+| 15 | 407 | 9/305 (3.0%, 95% CI 1.6-5.5) | 26.1% | 6/30 (20.0%, 95% CI 9.5-37.3) | 0 |
+| 25 | 343 | 64/305 (21.0%, 95% CI 16.8-25.9) | 42.0% | 11/30 (36.7%, 95% CI 21.9-54.5) | 0 |
+| 50 | 192 | 190/305 (62.3%, 95% CI 56.7-67.5) | 69.5% | 23/30 (76.7%, 95% CI 59.1-88.2) | 0 |
+| 75 | 86 | 262/305 (85.9%, 95% CI 81.5-89.4) | 83.5% | 29/30 (96.7%, 95% CI 83.3-99.4) | 0 |
+| 100 | 49 | 284/305 (93.1%, 95% CI 89.7-95.5) | 90.4% | 30/30 (100.0%, 95% CI 88.6-100.0) | 0 |
+| 150 | 14 | 302/305 (99.0%, 95% CI 97.1-99.7) | 96.9% | 30/30 (100.0%, 95% CI 88.6-100.0) | 0 |
-| paper's | 1 | 32 | 6 / 25 / -38.8% | 2 / 13 / -22.4% | 0 / 15 / -30.6% | 0 / 15 / -30.6% |
-| paper's | 2 | 16 | 2 / 13 / -22.4% | 1 / 8 / -14.3% | 0 / 8 / -16.3% | 0 / 8 / -16.3% |
-| paper's | 3 | 10 | 1 / 8 / -14.3% | 1 / 6 / -10.2% | 0 / 5 / -10.2% | 0 / 5 / -10.2% |
-| paper's | 5 | 5 | 0 / 4 / -8.2% | 0 / 4 / -8.2% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
-| paper's | 10 | 4 | 1 / 3 / -4.1% | 1 / 2 / -2.0% | 0 / 1 / -2.0% | 0 / 1 / -2.0% |
-| paper's | 15 | 2 | 1 / 1 / +0.0% | 1 / 0 / +2.0% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |
-| true | 1 | 49 | 11 / 38 / -55.1% | 3 / 16 / -26.5% | 1 / 10 / -18.4% | 1 / 10 / -18.4% |
-| true | 2 | 19 | 3 / 16 / -26.5% | 1 / 12 / -22.4% | 0 / 9 / -18.4% | 0 / 7 / -14.3% |
-| true | 3 | 13 | 1 / 12 / -22.4% | 0 / 6 / -12.2% | 0 / 5 / -10.2% | 0 / 5 / -10.2% |
-| true | 5 | 6 | 0 / 6 / -12.2% | 0 / 4 / -8.2% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
-| true | 10 | 3 | 0 / 3 / -6.1% | 0 / 3 / -6.1% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
-| true | 15 | 2 | 0 / 2 / -4.1% | 0 / 2 / -4.1% | 0 / 1 / -2.0% | 0 / 1 / -2.0% |
+| paper's | 1 | 27 | 5 / 21 / -40.0% | 2 / 12 / -25.0% | 0 / 14 / -35.0% | 0 / 14 / -35.0% |
+| paper's | 2 | 15 | 2 / 12 / -25.0% | 1 / 7 / -15.0% | 0 / 8 / -20.0% | 0 / 8 / -20.0% |
+| paper's | 3 | 9 | 1 / 7 / -15.0% | 1 / 5 / -10.0% | 0 / 4 / -10.0% | 0 / 4 / -10.0% |
+| paper's | 5 | 4 | 0 / 3 / -7.5% | 0 / 3 / -7.5% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
+| paper's | 10 | 3 | 1 / 2 / -2.5% | 1 / 1 / +0.0% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
+| paper's | 15 | 1 | 1 / 0 / +2.5% | 1 / 0 / +2.5% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |
+| true | 1 | 40 | 10 / 30 / -50.0% | 3 / 15 / -30.0% | 1 / 10 / -22.5% | 1 / 10 / -22.5% |
+| true | 2 | 18 | 3 / 15 / -30.0% | 1 / 11 / -25.0% | 0 / 8 / -20.0% | 0 / 6 / -15.0% |
+| true | 3 | 12 | 1 / 11 / -25.0% | 0 / 5 / -12.5% | 0 / 4 / -10.0% | 0 / 4 / -10.0% |
+| true | 5 | 5 | 0 / 5 / -12.5% | 0 / 3 / -7.5% | 0 / 2 / -5.0% | 0 / 2 / -5.0% |
+| true | 10 | 3 | 0 / 3 / -7.5% | 0 / 3 / -7.5% | 0 / 2 / -5.0% | 0 / 2 / -5.0% |
+| true | 15 | 2 | 0 / 2 / -5.0% | 0 / 2 / -5.0% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
-- error keyword in the edit's recorded output (the paper's DeepSeek label): kappa 0.05 [0.02, 0.09] over 299 scored edits in 87 runs
-- the next recorded execution before the next edit: kappa 0.05 [-0.08, 0.16] over 221 scored edits in 87 runs
+- error keyword in the edit's recorded output (the paper's DeepSeek label): kappa 0.04 [0.01, 0.08] over 276 scored edits in 73 runs
+- the next recorded execution before the next edit: kappa 0.05 [-0.07, 0.16] over 203 scored edits in 73 runs
-- Faithful runs that left a new source file out of their submitted patch: 0/87 (0.0%, 95% CI 0.0-4.2); of them resolved: 0. {}
+- Faithful runs that left a new source file out of their submitted patch: 0/73 (0.0%, 95% CI 0.0-5.0); of them resolved: 0. {}
```

## EXPB_REPORT recorded -> corrected: no change

## REPLAY_REPORT recorded -> corrected: no change

## REPLAY_REPORT corrected -> corrected-strict: 58 changed line(s)
```
-- Finished main runs: 418; replayed: 90; faithful (the replay's own submit command reproduced the recorded submission byte for byte): 87; not faithful: 1; ended at a limit, so uncertified: 2; infrastructure failures: 0.
+- Finished main runs: 418; replayed: 90; faithful (the replay's own submit command reproduced the recorded submission byte for byte): 73; not faithful: 15; ended at a limit, so uncertified: 2; infrastructure failures: 0.
-- Not faithful (first 15): sympy__sympy-12481
+- Not faithful (first 15): astropy__astropy-14365, django__django-14534, django__django-14752, django__django-16139, django__django-16595, pydata__xarray-4094, pytest-dev__pytest-7432, scikit-learn__scikit-learn-13142, sphinx-doc__sphinx-8721, sympy__sympy-12481, sympy__sympy-13031, sympy__sympy-18698, django__django-11848, astropy__astropy-14182, django__django-12308
-- Truth = a source edit; `is_real_edit` on every command: precision 74/209 (35.4%, 95% CI 29.2-42.1), recall 74/299 (24.7%, 95% CI 20.2-29.9)
-- Truth = any file change; `is_real_edit` on every command: precision 74/209 (35.4%, 95% CI 29.2-42.1), recall 74/397 (18.6%, 95% CI 15.1-22.8)
-- Calls with true source edits: 299/5419 (5.5%, 95% CI 4.9-6.2) in total; mean per run 5.2%, median 3.9%.
-- Calls with `is_real_edit` (the paper's detector): 209/5419 (3.9%, 95% CI 3.4-4.4) in total; mean per run 4.1%, median 2.6%.
-- Median source edits per run 1 over a median of 53 calls with commands. The paper reported 5.2% of steps, a median of 2 edits and 48 steps.
+- Truth = a source edit; `is_real_edit` on every command: precision 68/177 (38.4%, 95% CI 31.6-45.8), recall 68/276 (24.6%, 95% CI 19.9-30.0)
+- Truth = any file change; `is_real_edit` on every command: precision 68/177 (38.4%, 95% CI 31.6-45.8), recall 68/360 (18.9%, 95% CI 15.2-23.3)
+- Calls with true source edits: 276/4771 (5.8%, 95% CI 5.2-6.5) in total; mean per run 5.5%, median 4.2%.
+- Calls with `is_real_edit` (the paper's detector): 177/4771 (3.7%, 95% CI 3.2-4.3) in total; mean per run 4.0%, median 2.9%.
+- Median source edits per run 2 over a median of 55 calls with commands. The paper reported 5.2% of steps, a median of 2 edits and 48 steps.
-- faithful replays of submitted runs: failed runs with a resolving state a stop could have submitted: 6/49 (12.2%, 95% CI 5.7-24.2) (mwaskom__seaborn-3069, sphinx-doc__sphinx-10673, sympy__sympy-18698, sympy__sympy-18763, django__django-11477, django__django-11790); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.
+- faithful replays of submitted runs: failed runs with a resolving state a stop could have submitted: 5/43 (11.6%, 95% CI 5.1-24.5) (mwaskom__seaborn-3069, sphinx-doc__sphinx-10673, sympy__sympy-18763, django__django-11477, django__django-11790); resolving only at the final state, so lost by how the patch was built: 0; unscored states: 0.
-| 15 | 407 | 9/305 (3.0%, 95% CI 1.6-5.5) | 26.1% | 9/38 (23.7%, 95% CI 13.0-39.2) | 0 |
-| 25 | 343 | 64/305 (21.0%, 95% CI 16.8-25.9) | 42.0% | 16/38 (42.1%, 95% CI 27.9-57.8) | 0 |
-| 50 | 192 | 190/305 (62.3%, 95% CI 56.7-67.5) | 69.5% | 30/38 (78.9%, 95% CI 63.7-88.9) | 0 |
-| 75 | 86 | 262/305 (85.9%, 95% CI 81.5-89.4) | 83.5% | 37/38 (97.4%, 95% CI 86.5-99.5) | 0 |
-| 100 | 49 | 284/305 (93.1%, 95% CI 89.7-95.5) | 90.4% | 38/38 (100.0%, 95% CI 90.8-100.0) | 0 |
-| 150 | 14 | 302/305 (99.0%, 95% CI 97.1-99.7) | 96.9% | 38/38 (100.0%, 95% CI 90.8-100.0) | 0 |
+| 15 | 407 | 9/305 (3.0%, 95% CI 1.6-5.5) | 26.1% | 6/30 (20.0%, 95% CI 9.5-37.3) | 0 |
+| 25 | 343 | 64/305 (21.0%, 95% CI 16.8-25.9) | 42.0% | 11/30 (36.7%, 95% CI 21.9-54.5) | 0 |
+| 50 | 192 | 190/305 (62.3%, 95% CI 56.7-67.5) | 69.5% | 23/30 (76.7%, 95% CI 59.1-88.2) | 0 |
+| 75 | 86 | 262/305 (85.9%, 95% CI 81.5-89.4) | 83.5% | 29/30 (96.7%, 95% CI 83.3-99.4) | 0 |
+| 100 | 49 | 284/305 (93.1%, 95% CI 89.7-95.5) | 90.4% | 30/30 (100.0%, 95% CI 88.6-100.0) | 0 |
+| 150 | 14 | 302/305 (99.0%, 95% CI 97.1-99.7) | 96.9% | 30/30 (100.0%, 95% CI 88.6-100.0) | 0 |
-| paper's | 1 | 32 | 6 / 25 / -38.8% | 2 / 13 / -22.4% | 0 / 15 / -30.6% | 0 / 15 / -30.6% |
-| paper's | 2 | 16 | 2 / 13 / -22.4% | 1 / 8 / -14.3% | 0 / 8 / -16.3% | 0 / 8 / -16.3% |
-| paper's | 3 | 10 | 1 / 8 / -14.3% | 1 / 6 / -10.2% | 0 / 5 / -10.2% | 0 / 5 / -10.2% |
-| paper's | 5 | 5 | 0 / 4 / -8.2% | 0 / 4 / -8.2% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
-| paper's | 10 | 4 | 1 / 3 / -4.1% | 1 / 2 / -2.0% | 0 / 1 / -2.0% | 0 / 1 / -2.0% |
-| paper's | 15 | 2 | 1 / 1 / +0.0% | 1 / 0 / +2.0% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |
-| true | 1 | 49 | 11 / 38 / -55.1% | 3 / 16 / -26.5% | 1 / 10 / -18.4% | 1 / 10 / -18.4% |
-| true | 2 | 19 | 3 / 16 / -26.5% | 1 / 12 / -22.4% | 0 / 9 / -18.4% | 0 / 7 / -14.3% |
-| true | 3 | 13 | 1 / 12 / -22.4% | 0 / 6 / -12.2% | 0 / 5 / -10.2% | 0 / 5 / -10.2% |
-| true | 5 | 6 | 0 / 6 / -12.2% | 0 / 4 / -8.2% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
-| true | 10 | 3 | 0 / 3 / -6.1% | 0 / 3 / -6.1% | 0 / 2 / -4.1% | 0 / 2 / -4.1% |
-| true | 15 | 2 | 0 / 2 / -4.1% | 0 / 2 / -4.1% | 0 / 1 / -2.0% | 0 / 1 / -2.0% |
+| paper's | 1 | 27 | 5 / 21 / -40.0% | 2 / 12 / -25.0% | 0 / 14 / -35.0% | 0 / 14 / -35.0% |
+| paper's | 2 | 15 | 2 / 12 / -25.0% | 1 / 7 / -15.0% | 0 / 8 / -20.0% | 0 / 8 / -20.0% |
+| paper's | 3 | 9 | 1 / 7 / -15.0% | 1 / 5 / -10.0% | 0 / 4 / -10.0% | 0 / 4 / -10.0% |
+| paper's | 5 | 4 | 0 / 3 / -7.5% | 0 / 3 / -7.5% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
+| paper's | 10 | 3 | 1 / 2 / -2.5% | 1 / 1 / +0.0% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
+| paper's | 15 | 1 | 1 / 0 / +2.5% | 1 / 0 / +2.5% | 0 / 0 / +0.0% | 0 / 0 / +0.0% |
+| true | 1 | 40 | 10 / 30 / -50.0% | 3 / 15 / -30.0% | 1 / 10 / -22.5% | 1 / 10 / -22.5% |
+| true | 2 | 18 | 3 / 15 / -30.0% | 1 / 11 / -25.0% | 0 / 8 / -20.0% | 0 / 6 / -15.0% |
+| true | 3 | 12 | 1 / 11 / -25.0% | 0 / 5 / -12.5% | 0 / 4 / -10.0% | 0 / 4 / -10.0% |
+| true | 5 | 5 | 0 / 5 / -12.5% | 0 / 3 / -7.5% | 0 / 2 / -5.0% | 0 / 2 / -5.0% |
+| true | 10 | 3 | 0 / 3 / -7.5% | 0 / 3 / -7.5% | 0 / 2 / -5.0% | 0 / 2 / -5.0% |
+| true | 15 | 2 | 0 / 2 / -5.0% | 0 / 2 / -5.0% | 0 / 1 / -2.5% | 0 / 1 / -2.5% |
-- error keyword in the edit's recorded output (the paper's DeepSeek label): kappa 0.05 [0.02, 0.09] over 299 scored edits in 87 runs
-- the next recorded execution before the next edit: kappa 0.05 [-0.08, 0.16] over 221 scored edits in 87 runs
+- error keyword in the edit's recorded output (the paper's DeepSeek label): kappa 0.04 [0.01, 0.08] over 276 scored edits in 73 runs
+- the next recorded execution before the next edit: kappa 0.05 [-0.07, 0.16] over 203 scored edits in 73 runs
-- Faithful runs that left a new source file out of their submitted patch: 0/87 (0.0%, 95% CI 0.0-4.2); of them resolved: 0. {}
+- Faithful runs that left a new source file out of their submitted patch: 0/73 (0.0%, 95% CI 0.0-5.0); of them resolved: 0. {}
```

## 9VzP 1a, recomputed as in FINAL_MEASURES
- recorded: 37 of 38 runs have a resolving state; commands after it 44.2% of all, median per run 41.4%; model calls after it 45.4% of all, median per run 43.2%; no resolving state: ['sympy__sympy-11618']
- recorded-strict: 29 of 30 runs have a resolving state; commands after it 44.0% of all, median per run 40.4%; model calls after it 45.3% of all, median per run 42.9%; no resolving state: ['sympy__sympy-11618']
- corrected: 37 of 38 runs have a resolving state; commands after it 44.2% of all, median per run 41.4%; model calls after it 45.4% of all, median per run 43.2%; no resolving state: ['sympy__sympy-11618']
- corrected-strict: 29 of 30 runs have a resolving state; commands after it 44.0% of all, median per run 40.4%; model calls after it 45.3% of all, median per run 42.9%; no resolving state: ['sympy__sympy-11618']
