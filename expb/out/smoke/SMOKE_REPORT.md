# Experiment B and replay: smoke test

Agent runs took 5.5 min (6 runs, 4 at a time by default), replays 0.7 min, scoring 5.9 min.
API cost $0.0669 at peak prices from recorded tokens. Cache hits: 95.8% of prompt tokens. A B0 run cost $0.0137 at peak, so the full run's ~400 runs would cost at most about $5.47 at peak and half that off-peak (stopped arms cost less).

- **B0 psf__requests-2931**: exit Submitted, 25 calls, 33 commands, 1 source edits, $0.0098 at peak (litellm $0.0049), cache hits 95.3% of prompt tokens, 58s, tracking errors 0, timeouts 0, masked 0; served {('deepseek-flash', 'aeb56401ca74e127821c4f9126dcb669'): 25}
  - cmd 20 call 13: source edit=True, paper detector=False, masked=False, changed {'source': 1}, `cd /testbed && python - <<'EOF'
import re
p = 'requests/models.py'
s = open(p).read()

# C`
  - cmd 29 call 22: source edit=False, paper detector=True, masked=False, changed {'source': 1}, `cd /testbed && cat > /tmp/conftest_patch.py <<'EOF'
import collections, collections.abc
fo`
  - submission scored: resolved=True, patch applied=True
- **k1 psf__requests-2931**: exit BudgetStop, 18 calls, 24 commands, 1 source edits, $0.0060 at peak (litellm $0.0030), cache hits 92.1% of prompt tokens, 45s, tracking errors 0, timeouts 0, masked 0; served {('deepseek-flash', 'aeb56401ca74e127821c4f9126dcb669'): 18}
  - stopped after command 23 (call 18) at 1 source edits; patch 791 characters
  - cmd 23 call 18: source edit=True, paper detector=False, masked=False, changed {'source': 1}, `cd /testbed && python - <<'EOF'
import re
p = 'requests/models.py'
s = open(p).read()

# 1`
  - submission scored: resolved=True, patch applied=True
- **k3aware psf__requests-2931**: exit Submitted, 28 calls, 37 commands, 1 source edits, $0.0104 at peak (litellm $0.0052), cache hits 95.0% of prompt tokens, 77s, tracking errors 0, timeouts 0, masked 0; served {('deepseek-flash', 'aeb56401ca74e127821c4f9126dcb669'): 28}
  - cmd 27 call 20: source edit=True, paper detector=False, masked=False, changed {'source': 1}, `cd /testbed && python - <<'EOF'
import re
p = 'requests/models.py'
s = open(p).read()

# F`
  - cmd 32 call 24: source edit=False, paper detector=True, masked=False, changed {'source': 1}, `cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest test_requests.py -q -p no`
  - submission scored: resolved=True, patch applied=True
- psf__requests-2931: 1 distinct Experiment B patches scored
- **B0 pytest-dev__pytest-7236**: exit Submitted, 40 calls, 51 commands, 1 source edits, $0.0176 at peak (litellm $0.0088), cache hits 96.6% of prompt tokens, 132s, tracking errors 0, timeouts 0, masked 0; served {('deepseek-flash', 'aeb56401ca74e127821c4f9126dcb669'): 40}
  - cmd 6 call 4: source edit=False, paper detector=True, masked=False, changed {}, `cd /testbed && cat > /tmp/test_repro.py <<'EOF'
import unittest

class MyTestCase(unittest`
  - cmd 33 call 25: source edit=True, paper detector=False, masked=False, changed {'source': 1}, `cd /testbed && python - <<'EOF'
import re
p = "src/_pytest/unittest.py"
s = open(p).read()`
  - cmd 39 call 30: source edit=False, paper detector=True, masked=False, changed {'source': 1}, `cd /testbed && source activate testbed && cat > /tmp/test_verify.py <<'EOF'
import unittes`
  - cmd 40 call 31: source edit=False, paper detector=True, masked=False, changed {'source': 1}, `cd /testbed && source activate testbed && cat > /tmp/test_teardown_order.py <<'EOF'
import`
  - cmd 42 call 33: source edit=False, paper detector=True, masked=False, changed {'other': 1, 'source': 1}, `cd /testbed && cat > changelog/7113.bugfix.rst <<'EOF'
Fixed ``tearDown`` being executed f`
  - submission scored: resolved=True, patch applied=True
- **k1 pytest-dev__pytest-7236**: exit BudgetStop, 16 calls, 19 commands, 1 source edits, $0.0058 at peak (litellm $0.0029), cache hits 92.5% of prompt tokens, 46s, tracking errors 0, timeouts 0, masked 0; served {('deepseek-flash', 'aeb56401ca74e127821c4f9126dcb669'): 16}
  - stopped after command 18 (call 16) at 1 source edits; patch 512 characters
  - cmd 6 call 4: source edit=False, paper detector=True, masked=False, changed {}, `cd /tmp && cat > test_repro.py <<'EOF'
import unittest

class MyTestCase(unittest.TestCase`
  - cmd 12 call 10: source edit=False, paper detector=True, masked=False, changed {}, `source activate testbed && cd /tmp && python -m pytest --pdb test_repro.py -p no:cacheprov`
  - cmd 18 call 16: source edit=True, paper detector=False, masked=False, changed {'source': 1}, `cd /testbed && python - <<'EOF'
import re
p='src/_pytest/unittest.py'
s=open(p).read()
s=s`
  - submission scored: resolved=False, patch applied=True
- **k3aware pytest-dev__pytest-7236**: exit Submitted, 42 calls, 45 commands, 2 source edits, $0.0174 at peak (litellm $0.0087), cache hits 96.7% of prompt tokens, 142s, tracking errors 0, timeouts 0, masked 0; served {('deepseek-flash', 'aeb56401ca74e127821c4f9126dcb669'): 42}
  - cmd 6 call 4: source edit=False, paper detector=True, masked=False, changed {}, `cd /testbed && cat > /tmp/test_repro.py <<'EOF'
import unittest

class MyTestCase(unittest`
  - cmd 11 call 9: source edit=False, paper detector=True, masked=False, changed {}, `source activate testbed; cd /testbed && python -m pytest --pdb /tmp/test_repro.py 2>&1 | g`
  - cmd 23 call 21: source edit=True, paper detector=False, masked=False, changed {'source': 1}, `cd /testbed && python - <<'EOF'
import re
p = "src/_pytest/unittest.py"
s = open(p).read()`
  - cmd 25 call 23: source edit=False, paper detector=True, masked=False, changed {'source': 1}, `source activate testbed; cd /testbed && cat > /tmp/test_edge.py <<'EOF'
import unittest

c`
  - cmd 32 call 30: source edit=True, paper detector=False, masked=False, changed {'source': 1}, `cd /testbed && python - <<'EOF'
p = "src/_pytest/unittest.py"
s = open(p).read()
s = s.rep`
  - cmd 33 call 31: source edit=False, paper detector=True, masked=False, changed {'source': 1}, `source activate testbed; cd /testbed && echo "=== method skip ===" && python -m pytest --p`
  - cmd 36 call 34: source edit=False, paper detector=True, masked=False, changed {'other': 1, 'source': 1}, `cd /testbed && cat > changelog/7247.bugfix.rst <<'EOF'
Fixed `--pdb` and `--trace` with un`
  - submission scored: resolved=True, patch applied=True
- pytest-dev__pytest-7236: 5 distinct Experiment B patches scored

## Replays

- **psf__requests-2931** (main run Submitted, resolved=True): exit Submitted, faithful=True, 96/96 commands replayed, 11 source edits, 10 distinct states, 10 scored, output similarity >= 0.8 in 0.989, 39s
- **pytest-dev__pytest-7236** (main run Submitted, resolved=True): exit Submitted, faithful=True, 52/52 commands replayed, 5 source edits, 1 distinct states, 1 scored, output similarity >= 0.8 in 0.941, 44s

## Checklist

- PASS: B0 psf__requests-2931: ended normally
- PASS: B0 psf__requests-2931: a state for every command
- PASS: B0 psf__requests-2931: no tracking errors
- PASS: B0 psf__requests-2931: no reasoning in any call
- PASS: B0 psf__requests-2931: served fingerprint unchanged
- PASS: B0 psf__requests-2931: submission applied by the harness
- PASS: k1 psf__requests-2931: ended normally
- PASS: k1 psf__requests-2931: a state for every command
- PASS: k1 psf__requests-2931: no tracking errors
- PASS: k1 psf__requests-2931: no reasoning in any call
- PASS: k1 psf__requests-2931: served fingerprint unchanged
- PASS: k1 psf__requests-2931: submission applied by the harness
- PASS: k1 psf__requests-2931: budget stop fired with a non-empty patch
- PASS: k3aware psf__requests-2931: ended normally
- PASS: k3aware psf__requests-2931: a state for every command
- PASS: k3aware psf__requests-2931: no tracking errors
- PASS: k3aware psf__requests-2931: no reasoning in any call
- PASS: k3aware psf__requests-2931: served fingerprint unchanged
- PASS: k3aware psf__requests-2931: submission applied by the harness
- PASS: B0 pytest-dev__pytest-7236: ended normally
- PASS: B0 pytest-dev__pytest-7236: a state for every command
- PASS: B0 pytest-dev__pytest-7236: no tracking errors
- PASS: B0 pytest-dev__pytest-7236: no reasoning in any call
- PASS: B0 pytest-dev__pytest-7236: served fingerprint unchanged
- PASS: B0 pytest-dev__pytest-7236: submission applied by the harness
- PASS: k1 pytest-dev__pytest-7236: ended normally
- PASS: k1 pytest-dev__pytest-7236: a state for every command
- PASS: k1 pytest-dev__pytest-7236: no tracking errors
- PASS: k1 pytest-dev__pytest-7236: no reasoning in any call
- PASS: k1 pytest-dev__pytest-7236: served fingerprint unchanged
- PASS: k1 pytest-dev__pytest-7236: submission applied by the harness
- PASS: k1 pytest-dev__pytest-7236: budget stop fired with a non-empty patch
- PASS: k3aware pytest-dev__pytest-7236: ended normally
- PASS: k3aware pytest-dev__pytest-7236: a state for every command
- PASS: k3aware pytest-dev__pytest-7236: no tracking errors
- PASS: k3aware pytest-dev__pytest-7236: no reasoning in any call
- PASS: k3aware pytest-dev__pytest-7236: served fingerprint unchanged
- PASS: k3aware pytest-dev__pytest-7236: submission applied by the harness
- PASS: replay psf__requests-2931: ended normally
- PASS: replay psf__requests-2931: reproduced the recorded submission exactly
- PASS: replay psf__requests-2931: every state scored
- PASS: replay pytest-dev__pytest-7236: ended normally
- PASS: replay pytest-dev__pytest-7236: reproduced the recorded submission exactly
- PASS: replay pytest-dev__pytest-7236: every state scored
