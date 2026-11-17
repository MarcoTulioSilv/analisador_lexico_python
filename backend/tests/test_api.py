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
# Etapa 4: a resposta ganhou os campos da análise sintática (ast, derivacao,
# erros_sintaticos, linhas_ignoradas); "tokens" e "erros" continuam idênticos e
# "sucesso" passou a valer para léxico E sintático. Estes testes comparam só os
# campos da Etapa 3 (via campos_da_etapa_3), com entradas sintaticamente válidas.

CAMPOS_ETAPA_3 = ("sucesso", "tokens", "erros")
CAMPOS_ETAPA_4 = ("ast", "derivacao", "erros_sintaticos", "linhas_ignoradas")


def campos_da_etapa_3(dados):
    assert set(dados) == set(CAMPOS_ETAPA_3) | set(CAMPOS_ETAPA_4)
    return {campo: dados[campo] for campo in CAMPOS_ETAPA_3}


def test_analisar_codigo_valido_retorna_tokens(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": "idade = 17"})
    assert resp.status_code == 200
    assert resp.is_json
    assert campos_da_etapa_3(resp.get_json()) == {
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
    assert campos_da_etapa_3(dados) == {"sucesso": True, "tokens": [], "erros": []}


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


# ---------- /api/analisar: análise sintática (Etapa 4) ----------

def test_tokens_e_erros_lexicos_continuam_iguais_aos_da_etapa_3(cliente):
    # Regressão: "tokens" e "erros" são exatamente o que o scanner da Etapa 3 produz.
    from scanner import analisar_lexico

    codigo = 'nome = "Ana"\nidade = 17 @'
    dados = cliente.post("/api/analisar", json={"codigo": codigo}).get_json()
    tokens, erros = analisar_lexico(codigo)
    assert dados["tokens"] == tokens
    assert dados["erros"] == erros


def test_codigo_valido_retorna_ast(cliente):  # CT-01 / CT-08
    resp = cliente.post("/api/analisar", json={"codigo": "resultado = 10 + 5 * 2"})
    assert resp.status_code == 200
    dados = resp.get_json()
    assert set(dados) == set(CAMPOS_ETAPA_3) | set(CAMPOS_ETAPA_4)
    assert dados["sucesso"] is True
    assert dados["erros"] == []
    assert dados["erros_sintaticos"] == []
    assert dados["linhas_ignoradas"] == []
    ast = dados["ast"]
    assert ast["tipo"] == "PROGRAMA"
    atribuicao = ast["filhos"][0]
    assert atribuicao["tipo"] == "ATRIBUICAO"
    adicao = atribuicao["filhos"][1]
    assert adicao["tipo"] == "ADICAO"
    assert adicao["filhos"][1]["tipo"] == "MULTIPLICACAO"  # precedência: * fica abaixo do +
    assert dados["derivacao"]["simbolo"] == "programa"


def test_erro_sintatico_retorna_ast_nula_e_erros(cliente):
    resp = cliente.post("/api/analisar", json={"codigo": "x = 5 +\ny = 1"})
    assert resp.status_code == 200
    dados = resp.get_json()
    assert dados["sucesso"] is False
    assert dados["erros"] == []          # o léxico passou
    assert dados["ast"] is None
    assert dados["derivacao"] is None
    assert len(dados["erros_sintaticos"]) == 1
    erro = dados["erros_sintaticos"][0]
    assert set(erro) == {"tipo", "linha", "coluna", "encontrado", "esperado", "regra", "mensagem"}
    assert (erro["tipo"], erro["linha"], erro["coluna"]) == ("ERRO_SINTATICO", 1, 8)
    assert erro["encontrado"] == "o fim da linha"


def test_sucesso_passa_a_considerar_o_sintatico(cliente):  # CT-17
    # Na Etapa 3 este código dava sucesso (os tokens são válidos); agora não dá mais.
    dados = cliente.post("/api/analisar", json={"codigo": "= = 17"}).get_json()
    assert dados["erros"] == []
    assert len(dados["erros_sintaticos"]) == 1
    assert dados["sucesso"] is False


def test_varios_erros_sintaticos(cliente):
    codigo = "x = 5 +\ny = * 2\nz = (1 + 2))\n17 = idade"
    dados = cliente.post("/api/analisar", json={"codigo": codigo}).get_json()
    assert [e["linha"] for e in dados["erros_sintaticos"]] == [1, 2, 3, 4]


def test_com_erro_lexico_o_parser_analisa_as_outras_linhas(cliente):  # CT-27
    dados = cliente.post("/api/analisar", json={"codigo": "x = 1 @ 2\ny = 2 + 3"}).get_json()
    assert dados["sucesso"] is False
    assert [e["lexema"] for e in dados["erros"]] == ["@"]   # o erro léxico continua informado
    assert dados["erros_sintaticos"] == []                  # sem erro inventado em "x = 1 2"
    assert dados["linhas_ignoradas"] == [1]
    assert [c["atributos"]["nome"] for c in dados["ast"]["filhos"]] == ["y"]


def test_erro_lexico_e_sintatico_juntos(cliente):
    dados = cliente.post("/api/analisar", json={"codigo": "a = 1 $\nb = (2"}).get_json()
    assert dados["sucesso"] is False
    assert [e["linha"] for e in dados["erros"]] == [1]
    assert [e["linha"] for e in dados["erros_sintaticos"]] == [2]
    assert dados["ast"] is None


def test_so_comentario_gera_programa_vazio(cliente):  # CT-23
    dados = cliente.post("/api/analisar", json={"codigo": "# nada"}).get_json()
    assert dados["sucesso"] is True
    assert dados["ast"]["filhos"] == []


def test_aninhamento_extremo_nao_gera_erro_500(cliente):
    codigo = "x = " + "(" * 4000 + "1" + ")" * 4000
    resp = cliente.post("/api/analisar", json={"codigo": codigo})
    assert resp.status_code == 200
    assert "aninhada ou longa demais" in resp.get_json()["erros_sintaticos"][0]["mensagem"]


def test_maior_aninhamento_aceito_serializa_sem_erro(cliente):
    # Logo abaixo do limite, a árvore (profunda) ainda precisa virar JSON sem estourar.
    codigo = "x = " + "(" * 35 + "1" + ")" * 35  # 35 é o máximo (36 já dá erro de limite)
    resp = cliente.post("/api/analisar", json={"codigo": codigo})
    assert resp.status_code == 200
    assert resp.get_json()["sucesso"] is True


def test_erro_sintatico_nao_expoe_detalhes_internos(cliente):
    dados = cliente.post("/api/analisar", json={"codigo": "x = (1 +\nif )"}).get_json()
    for erro in dados["erros_sintaticos"]:
        assert "Traceback" not in erro["mensagem"]
        assert ".py" not in erro["mensagem"]
