import pytest
from fastapi.testclient import TestClient

from presentation.api import app


@pytest.fixture
def client():
    return TestClient(app)
