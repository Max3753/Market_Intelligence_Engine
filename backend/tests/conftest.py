"""Pytest fixtures for the MIE test suite."""

from fastapi.testclient import TestClient


def get_test_client() -> TestClient:
    """Return a FastAPI TestClient bound to the app."""
    # 惰性导入：app.main 导入链含 tensorflow（embedding），
    # 顶层导入会让 pytest 收集阶段就触发 protobuf 版本冲突。
    from app.main import app
    return TestClient(app)
