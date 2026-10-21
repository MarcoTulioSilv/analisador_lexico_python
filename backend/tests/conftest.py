import sys
from pathlib import Path

import pytest

# Permite importar app.py e validacao.py, que ficam na pasta acima.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app as flask_app  # noqa: E402


@pytest.fixture
def cliente():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()
