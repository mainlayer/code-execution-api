# code-execution-api

[![CI](https://github.com/mainlayer/code-execution-api/actions/workflows/ci.yml/badge.svg)](https://github.com/mainlayer/code-execution-api/actions/workflows/ci.yml)

A FastAPI service that executes code in a sandboxed environment with **per-execution credit billing** via [Mainlayer](https://mainlayer.fr).

## Features

- `POST /execute` — run Python or JavaScript code in an isolated subprocess
- Per-execution billing via Mainlayer payment tokens
- Configurable timeout (1–30 seconds)
- Captures stdout, stderr, exit code, and execution duration
- Output truncated at 64 KB for safety

## Quickstart

```bash
pip install mainlayer
```

```bash
export MAINLAYER_API_KEY=your_api_key
export MAINLAYER_RESOURCE_ID=your_resource_id
uvicorn src.main:app --reload
```

### Execute Python code

```python
import httpx

resp = httpx.post(
    "http://localhost:8000/execute",
    json={
        "code": "print(sum(range(100)))",
        "language": "python",
        "timeout": 10,
    },
    headers={"x-mainlayer-token": "<your-token>"},
)
data = resp.json()
print(data["stdout"])   # 4950
print(f"Duration: {data['duration_ms']:.1f} ms")
```

### Execute JavaScript code

```python
resp = httpx.post(
    "http://localhost:8000/execute",
    json={"code": "console.log([...Array(5).keys()].join(', '))", "language": "javascript"},
    headers={"x-mainlayer-token": "<your-token>"},
)
```

## API Reference

### `POST /execute`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `code` | string | required | Source code (max 32 KB) |
| `language` | string | required | `python` or `javascript` |
| `timeout` | int | 10 | Execution timeout in seconds (1–30) |

**Headers:** `x-mainlayer-token` (required)

**Response:**
```json
{
  "stdout": "4950\n",
  "stderr": "",
  "exit_code": 0,
  "timed_out": false,
  "language": "python",
  "duration_ms": 82.3,
  "credits_used": 1
}
```

## Security

The sandbox uses subprocess isolation with configurable timeouts. For production, deploy inside a container with:
- No outbound network access
- Read-only filesystem (except `/tmp`)
- CPU and memory cgroup limits

## Payment

Access is gated through Mainlayer payment tokens. Get your token at [mainlayer.fr](https://mainlayer.fr).

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```
