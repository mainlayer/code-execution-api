import pytest
from src.sandbox import execute_code, SandboxError


def test_python_hello_world():
    result = execute_code('print("hello world")', "python")
    assert result.exit_code == 0
    assert "hello world" in result.stdout
    assert not result.timed_out


def test_python_arithmetic():
    result = execute_code("print(2 + 2)", "python")
    assert result.exit_code == 0
    assert "4" in result.stdout


def test_python_syntax_error():
    result = execute_code("def foo(:\n    pass", "python")
    assert result.exit_code != 0
    assert result.stderr  # should have error output


def test_python_timeout():
    result = execute_code("import time; time.sleep(10)", "python", timeout=1)
    assert result.timed_out
    assert result.exit_code == -1


def test_unsupported_language():
    with pytest.raises(SandboxError, match="Unsupported language"):
        execute_code("puts 'hello'", "ruby")


def test_duration_measured():
    result = execute_code("print('ok')", "python")
    assert result.duration_ms >= 0


def test_stdout_capture():
    result = execute_code(
        "for i in range(5):\n    print(i)",
        "python",
    )
    assert result.exit_code == 0
    for i in range(5):
        assert str(i) in result.stdout
