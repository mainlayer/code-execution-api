import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from mainlayer import MainlayerClient
from src.sandbox import execute_code, SandboxError, LANGUAGE_CONFIG

app = FastAPI(
    title="Code Execution API",
    description="Per-execution billed code sandbox powered by Mainlayer",
    version="1.0.0",
)

ml = MainlayerClient(api_key=os.environ["MAINLAYER_API_KEY"])
RESOURCE_ID = os.environ["MAINLAYER_RESOURCE_ID"]

MAX_CODE_LENGTH = 32_768  # 32 KB
MAX_TIMEOUT = 30


class ExecuteRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_LENGTH, description="Source code to execute")
    language: str = Field(..., description="Programming language: python or javascript")
    timeout: Optional[int] = Field(10, ge=1, le=MAX_TIMEOUT, description="Execution timeout in seconds")


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    language: str
    duration_ms: float
    credits_used: int


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/execute", response_model=ExecuteResponse)
async def execute(
    request: ExecuteRequest,
    x_mainlayer_token: str = Header(..., description="Mainlayer payment token"),
):
    access = await ml.resources.verify_access(RESOURCE_ID, x_mainlayer_token)
    if not access.authorized:
        raise HTTPException(
            status_code=402,
            detail="Payment required. Get access at mainlayer.fr",
        )

    if request.language not in LANGUAGE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{request.language}'. Supported: {list(LANGUAGE_CONFIG)}",
        )

    try:
        result = execute_code(
            code=request.code,
            language=request.language,
            timeout=request.timeout or 10,
        )
    except SandboxError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ExecuteResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        language=result.language,
        duration_ms=result.duration_ms,
        credits_used=1,
    )
