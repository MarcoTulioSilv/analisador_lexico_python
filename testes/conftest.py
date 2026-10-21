"""Configuração comum dos testes de navegador (Playwright).

Os testes rodam num container próprio, na mesma rede do Docker Compose,
e acessam a aplicação pelo Nginx: http://frontend (o mesmo caminho do navegador).
"""
import os

import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
PASTA_EVIDENCIAS = os.environ.get("PASTA_EVIDENCIAS", "evidencias")


@pytest.fixture
def tela(page):
    """Página principal já aberta."""
    page.goto(BASE_URL)
    return page


@pytest.fixture
def chamadas_api(tela):
    """Lista que registra cada requisição feita para /api/analisar."""
    chamadas = []
    tela.on("request", lambda req: chamadas.append(req) if "/api/analisar" in req.url else None)
    return chamadas
