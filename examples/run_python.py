"""
Example: execute Python code via the Code Execution API.

Usage:
    MAINLAYER_TOKEN=<token> python examples/run_python.py
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
import math

def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")

print(f"pi = {math.pi:.6f}")
"""

resp = httpx.post(
    f"{API_BASE}/execute",
    json={"code": CODE, "language": "python", "timeout": 10},
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
