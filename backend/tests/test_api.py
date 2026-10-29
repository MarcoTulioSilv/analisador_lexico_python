"""Testes dos endpoints do backend (contrato documentado no README)."""
import pytest

import app as modulo_app
from validacao import ERRO_CAMPO, ERRO_JSON, ERRO_LIMITE, ERRO_VAZIO, LIMITE_CARACTERES


# ---------- /api/saude ----------

def test_saude_responde_ok(cliente):
    resp = cliente.get("/api/saude")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


# ---------- /api/analisar: análise léxica (Etapa 3) ----------
# Mudança intencional: a resposta 200 da Etapa 2 (recebido, mensagem, linhas,
# caracteres) foi substituída pelo resultado do scanner (sucesso, tokens, erros).

def test_analisar_codigo_valido_retorna_tokens(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": "idade = 17"})
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {
        "sucesso": True,
        "erros": [],
        "tokens": [
            {"tipo": "IDENTIFICADOR", "lexema": "idade", "linha": 1, "coluna": 1,
             "descricao": "nome (identificador): uma etiqueta que aponta para um objeto"},
            {"tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 7,
             "descricao": "operador de atribuição: cola o nome ao valor"},
            {"tipo": "LITERAL_INTEIRO", "lexema": "17", "linha": 1, "coluna": 9,
             "descricao": "número inteiro: vira um objeto do tipo int"},
            {"tipo": "NOVA_LINHA", "lexema": "", "linha": 1, "coluna": 11,
             "descricao": "fim da linha: em Python, a quebra de linha encerra o comando"},
        ],
    }


def test_analisar_campos_de_cada_token(cliente):
    dados = cliente.post("/api/analisar", json={"codigo": 'x = "a" + 1.5'}).get_json()
    for token in dados["tokens"]:
        assert set(token) == {"tipo", "lexema", "linha", "coluna", "descricao"}
        assert isinstance(token["linha"], int) and isinstance(token["coluna"], int)


def test_analisar_com_erro_lexico_retorna_200_e_sucesso_falso(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": "a = 1\nb = 2 @ 3"})
    assert resp.status_code == 200
    dados = resp.get_json()
    assert dados["sucesso"] is False
    assert dados["erros"] == [{
        "tipo": "ERRO_LEXICO",
        "lexema": "@",
        "linha": 2,
        "coluna": 7,
        "mensagem": "Erro léxico na linha 2, coluna 7: caractere não reconhecido '@'. "
                    "Verifique se ele faz parte do subconjunto suportado.",
    }]
    # Os tokens válidos continuam vindo junto.
    assert [t["lexema"] for t in dados["tokens"] if t["tipo"] != "NOVA_LINHA"] == ["a", "=", "1", "b", "=", "2", "3"]


def test_analisar_acumula_varios_erros(cliente):
    codigo = "preco = 10.5.2\nemail = ana@escola\ntotal = 12abc"
    dados = cliente.post("/api/analisar", json={"codigo": codigo}).get_json()
    assert dados["sucesso"] is False
    assert [(e["lexema"], e["linha"], e["coluna"]) for e in dados["erros"]] == [
        ("10.5.2", 1, 9), ("@", 2, 12), ("12abc", 3, 9),
    ]


def test_analisar_string_nao_fechada(cliente):
    dados = cliente.post("/api/analisar", json={"codigo": 'nome = "Ana'}).get_json()
    assert dados["sucesso"] is False
    assert "string não fechada" in dados["erros"][0]["mensagem"]


def test_analisar_aceita_caracteres_especiais(cliente):
    codigo = 'texto = "ação 😀"\t# comentário {}'
    resp = cliente.post("/api/analisar", json={"codigo": codigo})
    assert resp.status_code == 200
    dados = resp.get_json()
    assert dados["sucesso"] is True
    assert dados["tokens"][2]["lexema"] == '"ação 😀"'


def test_analisar_so_comentario_tem_sucesso_sem_tokens(cliente):
    dados = cliente.post("/api/analisar", json={"codigo": "# só comentário"}).get_json()
    assert dados == {"sucesso": True, "tokens": [], "erros": []}


def test_analisar_ignora_campos_extras(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": "x = 1", "extra": 123})
    assert resp.status_code == 200
    assert resp.get_json()["sucesso"] is True


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
