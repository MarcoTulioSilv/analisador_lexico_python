"""Testes dos endpoints do backend (contrato documentado no README)."""
import pytest

import app as modulo_app
from validacao import ERRO_CAMPO, ERRO_JSON, ERRO_LIMITE, ERRO_VAZIO, LIMITE_CARACTERES


# ---------- /api/saude ----------

def test_saude_responde_ok(cliente):
    resp = cliente.get("/api/saude")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


# ---------- /api/analisar: casos aceitos ----------

def test_analisar_codigo_valido(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": "idade = 17"})
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {
        "recebido": True,
        "mensagem": "Código recebido com sucesso.",
        "linhas": 1,
        "caracteres": 10,
    }


def test_analisar_conta_linhas_e_caracteres(cliente):
    codigo = 'idade = 17\nidade_texto = "17"\nnome = "Ana"'
    dados = cliente.post("/api/analisar", json={"codigo": codigo}).get_json()
    assert dados["linhas"] == 3
    assert dados["caracteres"] == len(codigo)


def test_analisar_aceita_caracteres_especiais(cliente):
    codigo = 'texto = "ação 😀"\t# comentário {}'
    resp = cliente.post("/api/analisar", json={"codigo": codigo})
    assert resp.status_code == 200
    assert resp.get_json()["caracteres"] == len(codigo)


def test_analisar_aceita_codigo_com_erro_intencional(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": 'nome = "Ana'})
    assert resp.status_code == 200
    assert resp.get_json()["recebido"] is True


def test_analisar_ignora_campos_extras(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": "x = 1", "extra": 123})
    assert resp.status_code == 200


# ---------- /api/analisar: entradas inválidas ----------

def _assert_erro_400(resp, mensagem):
    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json() == {"recebido": False, "erro": mensagem}


def test_analisar_sem_corpo(cliente):
    _assert_erro_400(cliente.post("/api/analisar"), ERRO_JSON)


def test_analisar_json_malformado(cliente):
    resp = cliente.post("/api/analisar", data='{"codigo": ', content_type="application/json")
    _assert_erro_400(resp, ERRO_JSON)


def test_analisar_content_type_errado(cliente):
    resp = cliente.post("/api/analisar", data='{"codigo": "x = 1"}', content_type="text/plain")
    _assert_erro_400(resp, ERRO_JSON)


def test_analisar_json_que_nao_e_objeto(cliente):
    _assert_erro_400(cliente.post("/api/analisar", json=["x = 1"]), ERRO_JSON)


def test_analisar_campo_ausente(cliente):
    _assert_erro_400(cliente.post("/api/analisar", json={"programa": "x = 1"}), ERRO_CAMPO)


@pytest.mark.parametrize("valor", [None, 17, ["x = 1"]])
def test_analisar_campo_com_tipo_errado(cliente, valor):
    _assert_erro_400(cliente.post("/api/analisar", json={"codigo": valor}), ERRO_CAMPO)


@pytest.mark.parametrize("codigo", ["", "   ", "\n\t \n"])
def test_analisar_vazio_ou_so_espacos(cliente, codigo):
    _assert_erro_400(cliente.post("/api/analisar", json={"codigo": codigo}), ERRO_VAZIO)


def test_analisar_acima_do_limite(cliente):
    codigo = "x" * (LIMITE_CARACTERES + 1)
    _assert_erro_400(cliente.post("/api/analisar", json={"codigo": codigo}), ERRO_LIMITE)


def test_analisar_aceita_apenas_post(cliente):
    assert cliente.get("/api/analisar").status_code == 405


def test_rota_inexistente_retorna_404(cliente):
    assert cliente.get("/api/nao-existe").status_code == 404


def test_hello_da_etapa_1_foi_removido(cliente):
    # Mudança intencional da Etapa 2: o Hello World foi substituído pela tela principal.
    assert cliente.get("/api/hello").status_code == 404


# ---------- erro inesperado ----------

def test_erro_inesperado_nao_expoe_detalhes(cliente, monkeypatch):
    def explode(_dados):
        raise RuntimeError("segredo interno /app/validacao.py")

    monkeypatch.setattr(modulo_app, "validar_codigo", explode)
    resp = cliente.post("/api/analisar", json={"codigo": "x = 1"})

    assert resp.status_code == 500
    assert resp.get_json() == {
        "recebido": False,
        "erro": "Erro interno no servidor. Tente novamente mais tarde.",
    }
    corpo = resp.get_data(as_text=True)
    assert "segredo" not in corpo
    assert "Traceback" not in corpo
