import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

from mainlayer import MainlayerClient
from src.sandbox import execute_code, SandboxError, LANGUAGE_CONFIG

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Code Execution API starting up")
    yield
    logger.info("Code Execution API shutting down")


app = FastAPI(
    title="Code Execution API",
    description="Per-execution billed code sandbox powered by Mainlayer",
    version="1.0.0",
    lifespan=lifespan,
)

ml = MainlayerClient(api_key=os.environ["MAINLAYER_API_KEY"])
RESOURCE_ID = os.environ["MAINLAYER_RESOURCE_ID"]

MAX_CODE_LENGTH = 32_768  # 32 KB
MAX_TIMEOUT = 30


class ExecuteRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_LENGTH, description="Source code to execute")
    language: str = Field(..., description="Programming language: python or javascript")
    timeout: Optional[int] = Field(10, ge=1, le=MAX_TIMEOUT, description="Execution timeout in seconds")


class LanguagesResponse(BaseModel):
    languages: list[str]
    default_timeout_seconds: int
    max_timeout_seconds: int


class ExecuteResponse(BaseModel):
    stdout: str = Field(..., description="Standard output from the code execution")
    stderr: str = Field(..., description="Standard error from the code execution")
    exit_code: int = Field(..., description="Process exit code (0 = success)")
    timed_out: bool = Field(..., description="Whether execution hit the timeout limit")
    language: str = Field(..., description="Language used for execution")
    duration_ms: float = Field(..., description="Wall-clock execution time in milliseconds")
    credits_used: int = Field(..., description="Credits consumed (1 = $0.01)")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/languages")
async def list_languages():
    """List supported programming languages."""
    return {
        "languages": list(LANGUAGE_CONFIG.keys()),
        "default_timeout_seconds": 10,
        "max_timeout_seconds": MAX_TIMEOUT,
    }


@app.post("/execute", response_model=ExecuteResponse)
async def execute(
    request: ExecuteRequest,
    x_mainlayer_token: str = Header(..., description="Mainlayer payment token"),
):
    """
    Execute code in a sandboxed environment.

    **Cost**: $0.01 per execution (billed via Mainlayer).

    **Supported Languages**:
    - `python` (Python 3.11+)
    - `javascript` (Node.js)

    **Security**:
    - Subprocess isolation with timeout enforcement
    - Output capped at 64 KB per stream
    - No network access from sandbox
    - Max 32 KB code size
    - Max 30 second timeout

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/execute \\
      -H "Content-Type: application/json" \\
      -H "X-Mainlayer-Token: your_token" \\
      -d '{
        "code": "print(\\"Hello, World!\\")",
        "language": "python",
        "timeout": 5
      }'
    ```
    """
    # Verify payment
    try:
        access = await ml.resources.verify_access(RESOURCE_ID, x_mainlayer_token)
    except Exception as exc:
        logger.error(f"Payment verification failed: {exc}")
        raise HTTPException(
            status_code=402,
            detail="Payment verification failed. Ensure your token is valid.",
        )

    if not access.authorized:
        logger.warning(f"Unauthorized execution attempt with token {x_mainlayer_token[:10]}...")
        raise HTTPException(
            status_code=402,
            detail="Payment required. Get access at mainlayer.fr",
        )

    # Validate language
    if request.language not in LANGUAGE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{request.language}'. Supported: {list(LANGUAGE_CONFIG)}",
        )

    # Execute code
    timeout = request.timeout or 10
    logger.info(f"Executing {request.language} code ({len(request.code)} bytes, timeout {timeout}s)")

    try:
        result = execute_code(
            code=request.code,
            language=request.language,
            timeout=timeout,
        )
    except SandboxError as exc:
        logger.error(f"Sandbox error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Execution failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Code execution failed. Please check your code and try again.",
        )

    logger.info(
        f"Execution completed: {request.language}, exit_code={result.exit_code}, "
        f"timed_out={result.timed_out}, duration={result.duration_ms}ms"
    )

    return ExecuteResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        language=result.language,
        duration_ms=result.duration_ms,
        credits_used=1,
    )
