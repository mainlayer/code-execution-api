# Code Execution API

A production-ready sandboxed code execution service with per-execution billing via [Mainlayer](https://mainlayer.fr).

## Features

- **Python & JavaScript support**: Execute code in Python 3.11+ or Node.js
- **Sandboxed execution**: Subprocess isolation with timeout enforcement
- **Output streaming**: Capture stdout/stderr up to 64 KB each
- **Per-execution billing**: $0.01 per execution via Mainlayer
- **Safety limits**: 32 KB code limit, 30 second max timeout
- **Production-ready**: Structured logging and error handling

## Pricing

| Operation | Cost |
|-----------|------|
| Code execution | $0.01 per run |
| Health check | FREE |
| List languages | FREE |

## 5-Minute Quickstart

### 1. Install dependencies

```bash
pip install -e ".[dev]"
```

### 2. Set environment variables

```bash
export MAINLAYER_API_KEY=your_api_key
export MAINLAYER_RESOURCE_ID=your_resource_id
export LOG_LEVEL=INFO
```

### 3. Start the server

```bash
uvicorn src.main:app --reload --port 8000
```

Server runs at `http://localhost:8000`

### 4. Check supported languages

```bash
curl http://localhost:8000/languages
```

### 5. Execute Python code

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -H "X-Mainlayer-Token: your_payment_token" \
  -d '{
    "code": "print(sum(range(100)))",
    "language": "python",
    "timeout": 5
  }'
```

Response:
```json
{
  "stdout": "4950\n",
  "stderr": "",
  "exit_code": 0,
  "timed_out": false,
  "language": "python",
  "duration_ms": 42.5,
  "credits_used": 1
}
```

### 6. Execute JavaScript code

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -H "X-Mainlayer-Token: your_payment_token" \
  -d '{
    "code": "console.log([...Array(5).keys()].join(\", \"))",
    "language": "javascript"
  }'
```

## API Reference

### `POST /execute`

Execute code in a sandboxed environment.

**Request Body**:
```json
{
  "code": "string (required, max 32 KB)",
  "language": "python | javascript",
  "timeout": 10
}
```

**Response**:
```json
{
  "stdout": "string",
  "stderr": "string",
  "exit_code": 0,
  "timed_out": false,
  "language": "python",
  "duration_ms": 42.5,
  "credits_used": 1
}
```

**Cost**: $0.01 per execution

**Status Codes**:
- `200`: Execution completed (check `exit_code` and `timed_out`)
- `400`: Invalid request or unsupported language
- `402`: Payment required or invalid token
- `413`: Code exceeds 32 KB size limit
- `500`: Execution engine error

---

### `GET /languages`

List supported programming languages.

**Response**:
```json
{
  "languages": ["python", "javascript"],
  "default_timeout_seconds": 10,
  "max_timeout_seconds": 30
}
```

**Cost**: FREE

---

### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Cost**: FREE

---

## Language Details

### Python

**Runtime**: Python 3.11+ with full stdlib

**Available modules**: All standard library modules (no pip packages)

**Example**:
```python
import json
data = {"sum": sum(range(100)), "count": 100}
print(json.dumps(data))
```

### JavaScript

**Runtime**: Node.js (latest stable)

**Built-in modules**: fs, path, util, events, stream, etc.

**Example**:
```javascript
const arr = [...Array(5).keys()];
console.log(JSON.stringify({count: arr.length, items: arr}));
```

---

## Limits

| Limit | Value |
|-------|-------|
| Max code size | 32 KB |
| Max stdout | 64 KB |
| Max stderr | 64 KB |
| Max timeout | 30 seconds |
| Default timeout | 10 seconds |

---

## Security

### Process Isolation
- Each execution runs in a separate subprocess
- Subprocess inherits minimal environment
- No network access
- Limited filesystem access (/tmp only)

### Production Hardening
1. **Container isolation**: Docker, Kubernetes
2. **VM sandboxing**: gVisor, Firecracker
3. **Seccomp/AppArmor**: OS-level profiles
4. **Resource limits**: CPU, memory, file descriptors
5. **Dedicated user**: Non-root, limited permissions
6. **Network isolation**: Block outbound traffic entirely
7. **Audit logging**: Log all executions

---

## Development

### Running tests

```bash
pytest tests/ -v
```

### Docker deployment

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y nodejs
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY src/ src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
```

---

## Support

- Docs: https://docs.mainlayer.fr
- Issues: https://github.com/mainlayer/code-execution-api/issues
