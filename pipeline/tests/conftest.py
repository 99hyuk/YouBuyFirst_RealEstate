import pytest


@pytest.fixture(autouse=True)
def disable_local_dotenv(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
