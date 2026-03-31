"""
Example: execute JavaScript code via the Code Execution API.

Usage:
    MAINLAYER_TOKEN=<token> python examples/run_javascript.py
"""

import os
import sys
import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
TOKEN = os.getenv("MAINLAYER_TOKEN")

if not TOKEN:
    print("Error: set MAINLAYER_TOKEN environment variable")
    sys.exit(1)

CODE = """\
function fibonacci(n) {
  let a = 0, b = 1;
  for (let i = 0; i < n; i++) {
    [a, b] = [b, a + b];
  }
  return a;
}

for (let i = 0; i < 10; i++) {
  console.log(`fib(${i}) = ${fibonacci(i)}`);
}

console.log(`pi = ${Math.PI.toFixed(6)}`);
"""

resp = httpx.post(
    f"{API_BASE}/execute",
    json={"code": CODE, "language": "javascript", "timeout": 10},
    headers={"x-mainlayer-token": TOKEN},
)

if resp.status_code == 402:
    print("Payment required — get access at https://mainlayer.fr")
    sys.exit(1)

resp.raise_for_status()
data = resp.json()

print(f"Exit code   : {data['exit_code']}")
print(f"Duration    : {data['duration_ms']:.1f} ms")
print(f"Credits used: {data['credits_used']}")
print("\n--- stdout ---")
print(data["stdout"])
if data["stderr"]:
    print("--- stderr ---")
    print(data["stderr"])
