"""Testes de implantação: os containers sobem e se comunicam pela rede do Compose."""
from conftest import BASE_URL


def test_frontend_serve_a_pagina(page):
    resposta = page.goto(BASE_URL)
    assert resposta.status == 200


def test_arquivos_estaticos_sao_servidos(page):
    for arquivo in ("estilo.css", "exemplos.js", "app.js"):
        resposta = page.request.get(f"{BASE_URL}/{arquivo}")
        assert resposta.status == 200, arquivo


def test_backend_responde_atraves_do_nginx(page):
    # Prova a comunicação frontend (Nginx) -> backend (Flask) dentro da rede Docker.
    resposta = page.request.get(f"{BASE_URL}/api/saude")
    assert resposta.status == 200
    assert resposta.json() == {"status": "ok"}


def test_endpoint_de_analise_responde_atraves_do_nginx(page):
    resposta = page.request.post(f"{BASE_URL}/api/analisar", data={"codigo": "idade = 17"})
    assert resposta.status == 200
    # Contrato da Etapa 3 (antes era {"recebido": true, ...}).
    dados = resposta.json()
    assert dados["sucesso"] is True
    assert [t["lexema"] for t in dados["tokens"]] == ["idade", "=", "17", ""]
