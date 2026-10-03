# Experiment B and replay: environment check

Run Sat Oct  3 17:03:23 2026.

- OK   python: 3.12.3
- OK   mini-swe-agent: 2.3.0 from /workspaces/mini-swe-agent/.venv-expb/lib/python3.12/site-packages/minisweagent
- OK   mini-swe-agent is the released wheel, not the repository's source
- OK   built-in swebench.yaml
- OK   litellm
- OK   datasets
- OK   docker: 29.8.0-1
- OK   harness CLI: /workspaces/mini-swe-agent/.venv-expb/bin/swebench
- OK   swebench package: 5.0.2 (the main run's re-score used 5.0.2)
- OK   package list: 107 packages written to out/ENVIRONMENT.txt
- OK   free disk: 18.1 GB (need 10)
- OK   main run: 433 trajectories in /workspaces/mini-swe-agent/results_full: {'Submitted': 413, 'no exit status': 14, 'LimitsExceeded': 5, 'unreadable': 1}; its fingerprint(s): {'fp_8b330d02d0_prod0820_fp8_kvcache_20260402': 432}
- dataset princeton-nlp/SWE-Bench_Verified: revision c104f840cc67f8b6eec6f759ebc8b2693d585d4a
- dataset SWE-bench/SWE-bench_Verified: revision 78f471bf655a3137b2e8a75af1501690ec009ec3
- OK   API pre-flight through mini-swe-agent's model code: served 'deepseek-flash', fingerprint 'aeb56401ca74e127821c4f9126dcb669', reasoning off, tool call ['echo hi'], cost per call $0.000102 at peak (litellm $5.1083999999999994e-05)
