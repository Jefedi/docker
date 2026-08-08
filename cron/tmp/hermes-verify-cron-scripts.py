#!/usr/bin/env python3
"""Ad-hoc verification for cron tmp parsing scripts."""
import glob, subprocess, sys, os, json

scripts = sorted(glob.glob("/opt/data/cron/tmp/*.py"))
# Skip the verifier itself and scripts that make network calls (curl via os.system)
network_scripts = {"citya_full.py", "hermes-verify-cron-scripts.py"}
scripts = [s for s in scripts if os.path.basename(s) not in network_scripts]
passed, failed = [], []

for s in scripts:
    try:
        r = subprocess.run([sys.executable, s], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            passed.append(s)
        else:
            failed.append((s, r.returncode, r.stderr[-300:]))
    except subprocess.TimeoutExpired:
        failed.append((s, -1, "TIMEOUT"))
    except Exception as e:
        failed.append((s, -2, str(e)))

print(f"Scripts checked: {len(scripts)}")
print(f"Passed: {len(passed)}")
print(f"Failed: {len(failed)}")
for s in passed:
    print(f"  PASS  {os.path.basename(s)}")
for s, rc, err in failed:
    print(f"  FAIL  {os.path.basename(s)} (rc={rc})")
    print(f"        {err.strip()[-200:]}")

with open("/opt/data/cron/output/havre-rental-seen.json") as f:
    data = json.load(f)
assert "seen_ids" in data
assert isinstance(data["seen_ids"], list)
print(f"\nSeen-file: valid JSON, {len(data['seen_ids'])} IDs")

if failed:
    sys.exit(1)
else:
    print("\nALL CLEAN")