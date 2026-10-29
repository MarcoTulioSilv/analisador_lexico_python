"""Testes unitários do analisador léxico (scanner.py)."""
import keyword

import pytest

from scanner import DELIMITADORES, OPERADORES, PALAVRAS_RESERVADAS, analisar_lexico


def pares(codigo):
    """(tipo, lexema) de cada token, sem as NOVA_LINHA, e garantindo que não houve erro."""
    tokens, erros = analisar_lexico(codigo)
    assert erros == []
    return [(t["tipo"], t["lexema"]) for t in tokens if t["tipo"] != "NOVA_LINHA"]


def unico(codigo):
    """O único token (além da NOVA_LINHA final) produzido pelo código."""
    resultado = pares(codigo)
    assert len(resultado) == 1, resultado
    return resultado[0]


def erros_de(codigo):
    return analisar_lexico(codigo)[1]


# ---------- Formato ----------

def test_formato_do_token():
    tokens, erros = analisar_lexico("idade")
    assert erros == []
    assert tokens[0] == {
        "tipo": "IDENTIFICADOR",
        "lexema": "idade",
        "linha": 1,
        "coluna": 1,
        "descricao": "nome (identificador): uma etiqueta que aponta para um objeto",
    }


def test_exemplo_completo():
    assert pares("idade = 17") == [
        ("IDENTIFICADOR", "idade"),
        ("OPERADOR", "="),
        ("LITERAL_INTEIRO", "17"),
    ]


# ---------- Palavras reservadas ----------

@pytest.mark.parametrize("palavra", ["and", "or", "not", "None"])
def test_palavras_reservadas_do_subconjunto(palavra):
    assert unico(palavra) == ("PALAVRA_RESERVADA", palavra)


@pytest.mark.parametrize("palavra", sorted(PALAVRAS_RESERVADAS))
def test_todas_as_palavras_reservadas_do_python(palavra):
    assert unico(palavra) == ("PALAVRA_RESERVADA", palavra)


def test_lista_de_reservadas_e_a_do_python():
    assert PALAVRAS_RESERVADAS == set(keyword.kwlist) - {"True", "False"}


def test_palavra_fora_do_subconjunto_tem_descricao_propria():
    token = analisar_lexico("while")[0][0]
    assert "fora do subconjunto" in token["descricao"]


@pytest.mark.parametrize("nome", ["And", "NONE", "true", "notas", "ifa", "_and"])
def test_parecido_com_reservada_e_identificador(nome):
    assert unico(nome) == ("IDENTIFICADOR", nome)


# ---------- Identificadores ----------

@pytest.mark.parametrize("nome", ["x", "idade", "_x1", "__nome__", "idade_texto", "média", "ação", "A1b2"])
def test_identificadores_validos(nome):
    assert unico(nome) == ("IDENTIFICADOR", nome)


def test_identificador_nao_comeca_com_digito():
    erros = erros_de("1abc")
    assert len(erros) == 1
    assert erros[0]["lexema"] == "1abc"
    assert "número malformado" in erros[0]["mensagem"]


def test_identificador_para_no_simbolo():
    assert pares("a+b") == [("IDENTIFICADOR", "a"), ("OPERADOR", "+"), ("IDENTIFICADOR", "b")]


# ---------- Literais ----------

@pytest.mark.parametrize("numero", ["0", "7", "17", "123456789"])
def test_literal_inteiro(numero):
    assert unico(numero) == ("LITERAL_INTEIRO", numero)


@pytest.mark.parametrize("numero", ["1.75", "0.5", ".5", "3.", "10.0"])
def test_literal_real(numero):
    assert unico(numero) == ("LITERAL_REAL", numero)


@pytest.mark.parametrize(
    "texto",
    ['"Ana"', "'Ana'", '""', "''", '"17"', '"ação 😀"', r'"diz \"oi\""', r"'it\'s'", r'"a\\"', '"# não é comentário"'],
)
def test_literal_string(texto):
    assert unico(texto) == ("LITERAL_STRING", texto)


@pytest.mark.parametrize("valor", ["True", "False"])
def test_literal_booleano(valor):
    assert unico(valor) == ("LITERAL_BOOLEANO", valor)


def test_17_e_diferente_de_string_17():
    # O ponto central do projeto: a forma escrita decide a categoria.
    assert pares('17 "17"') == [("LITERAL_INTEIRO", "17"), ("LITERAL_STRING", '"17"')]


@pytest.mark.parametrize(
    "codigo, tipo_python",
    [("17", "int"), ("1.5", "float"), ('"a"', "str"), ("True", "bool")],
)
def test_descricao_do_literal_cita_o_tipo_python(codigo, tipo_python):
    token = analisar_lexico(codigo)[0][0]
    assert f"tipo {tipo_python}" in token["descricao"]


# ---------- Operadores ----------

@pytest.mark.parametrize("operador", list(OPERADORES))
def test_cada_operador(operador):
    assert unico(operador) == ("OPERADOR", operador)


@pytest.mark.parametrize("operador", ["==", "!=", "<=", ">=", "**", "//"])
def test_operador_composto_sem_espacos(operador):
    assert pares(f"a{operador}b") == [
        ("IDENTIFICADOR", "a"),
        ("OPERADOR", operador),
        ("IDENTIFICADOR", "b"),
    ]


def test_maior_casamento():
    assert [lex for _, lex in pares("a===b")] == ["a", "==", "=", "b"]
    assert [lex for _, lex in pares("2***3")] == ["2", "**", "*", "3"]


def test_exclamacao_sozinha_e_erro():
    erros = erros_de("a ! b")
    assert [e["lexema"] for e in erros] == ["!"]


# ---------- Delimitadores ----------

@pytest.mark.parametrize("delimitador", list(DELIMITADORES))
def test_cada_delimitador(delimitador):
    assert unico(delimitador) == ("DELIMITADOR", delimitador)


def test_chamada_de_funcao():
    assert pares('print("Idade:", idade)') == [
        ("IDENTIFICADOR", "print"),
        ("DELIMITADOR", "("),
        ("LITERAL_STRING", '"Idade:"'),
        ("DELIMITADOR", ","),
        ("IDENTIFICADOR", "idade"),
        ("DELIMITADOR", ")"),
    ]


# ---------- Comentários e espaços ----------

def test_comentario_e_ignorado():
    assert pares("x = 1  # comentário com @ e $") == [
        ("IDENTIFICADOR", "x"),
        ("OPERADOR", "="),
        ("LITERAL_INTEIRO", "1"),
    ]


def test_espacos_e_tabs_sao_ignorados():
    assert pares("  \t x \t=\t 1   ") == pares("x=1")


# ---------- Posição ----------

def posicoes(codigo):
    return [(t["lexema"], t["linha"], t["coluna"]) for t in analisar_lexico(codigo)[0]]


def test_posicao_na_mesma_linha():
    assert posicoes("idade = 17") == [("idade", 1, 1), ("=", 1, 7), ("17", 1, 9), ("", 1, 11)]


def test_posicao_em_varias_linhas():
    codigo = "a = 1\n\n  b = 2.5"
    assert posicoes(codigo) == [
        ("a", 1, 1), ("=", 1, 3), ("1", 1, 5), ("\n", 1, 6),
        ("b", 3, 3), ("=", 3, 5), ("2.5", 3, 7), ("", 3, 10),
    ]


def test_posicao_conta_acentos_e_emoji_como_um_caractere():
    assert posicoes('é = "😀" + x')[3] == ("+", 1, 9)
    assert posicoes('é = "😀" + x')[4] == ("x", 1, 11)


def test_tab_conta_como_uma_coluna():
    assert posicoes("\tx")[0] == ("x", 1, 2)


# ---------- NOVA_LINHA ----------

def tipos(codigo):
    return [t["tipo"] for t in analisar_lexico(codigo)[0]]


def test_nova_linha_encerra_cada_comando():
    assert tipos("a = 1\nb = 2\n").count("NOVA_LINHA") == 2


def test_nova_linha_no_fim_sem_quebra():
    tokens = analisar_lexico("x")[0]
    assert tokens[-1]["tipo"] == "NOVA_LINHA"
    assert tokens[-1]["lexema"] == ""


def test_linhas_em_branco_e_comentarios_nao_geram_nova_linha():
    assert tipos("\n\n# só comentário\n   \nx\n\n") == ["IDENTIFICADOR", "NOVA_LINHA"]


def test_quebra_dentro_de_parenteses_nao_encerra_comando():
    assert tipos("print(1,\n      2)\n") == [
        "IDENTIFICADOR", "DELIMITADOR", "LITERAL_INTEIRO", "DELIMITADOR",
        "LITERAL_INTEIRO", "DELIMITADOR", "NOVA_LINHA",
    ]


def test_parentese_sobrando_nao_quebra_o_scanner():
    assert tipos(")\nx\n") == ["DELIMITADOR", "NOVA_LINHA", "IDENTIFICADOR", "NOVA_LINHA"]


def test_crlf_do_windows():
    assert pares("a = 1\r\nb = 2\r\n") == pares("a = 1\nb = 2\n")
    assert tipos("a = 1\r\nb = 2\r\n").count("NOVA_LINHA") == 2


# ---------- Erros léxicos ----------

@pytest.mark.parametrize("caractere", ["@", "$", "?", "!", ":", ";", "[", "]", "{", "}", "\\", "`", "&", "|", "^", "~", "."])
def test_caractere_nao_reconhecido(caractere):
    erros = erros_de(f"x {caractere} y")
    assert erros == [{
        "tipo": "ERRO_LEXICO",
        "lexema": caractere,
        "linha": 1,
        "coluna": 3,
        "mensagem": f"Erro léxico na linha 1, coluna 3: caractere não reconhecido '{caractere}'. "
                    "Verifique se ele faz parte do subconjunto suportado.",
    }]


def test_erro_informa_linha_e_coluna_corretas():
    erro = erros_de("a = 1\nb = 2 @ 3")[0]
    assert (erro["linha"], erro["coluna"]) == (2, 7)
    assert erro["mensagem"].startswith("Erro léxico na linha 2, coluna 7:")


@pytest.mark.parametrize("codigo, lexema", [('nome = "Ana', '"Ana'), ("x = 'abc\ny = 1", "'abc"), ('s = "a\\"', '"a\\"')])
def test_string_nao_fechada(codigo, lexema):
    erros = erros_de(codigo)
    assert len(erros) == 1
    assert erros[0]["lexema"] == lexema
    assert "string não fechada" in erros[0]["mensagem"]


def test_string_nao_fechada_nao_engole_a_linha_seguinte():
    tokens, erros = analisar_lexico('a = "abc\nb = 2')
    assert len(erros) == 1
    assert ("b", 2) in [(t["lexema"], t["linha"]) for t in tokens]


def test_string_nao_fechada_com_crlf_nao_inclui_o_retorno():
    assert erros_de('a = "abc\r\nb = 1')[0]["lexema"] == '"abc'


@pytest.mark.parametrize("numero", ["12abc", "1.2.3", "10.5.2", "3_000", "1e5", "7x"])
def test_numero_malformado(numero):
    erros = erros_de(f"n = {numero}")
    assert len(erros) == 1
    assert erros[0]["lexema"] == numero
    assert erros[0]["coluna"] == 5
    assert "número malformado" in erros[0]["mensagem"]


@pytest.mark.parametrize("codigo", ['"""doc"""', "'''doc'''", '"""sem fim', 'x = """a\nb"""'])
def test_string_de_tres_aspas_fora_do_subconjunto(codigo):
    erros = erros_de(codigo)
    assert len(erros) == 1
    assert "três aspas" in erros[0]["mensagem"]


def test_continua_depois_dos_erros_e_acumula_todos():
    codigo = "preco = 10.5.2\nemail = ana@escola\ntotal = 12abc\nok = 1"
    tokens, erros = analisar_lexico(codigo)
    assert [(e["lexema"], e["linha"]) for e in erros] == [("10.5.2", 1), ("@", 2), ("12abc", 3)]
    lexemas = [t["lexema"] for t in tokens]
    assert lexemas[-4:] == ["ok", "=", "1", ""]
    assert "escola" in lexemas


def test_erro_nao_expoe_detalhes_internos():
    for erro in erros_de("@ $ \"abc 1.2.3"):
        assert "Traceback" not in erro["mensagem"]
        assert ".py" not in erro["mensagem"]


# ---------- Casos de borda ----------

@pytest.mark.parametrize("codigo", ["", "   ", "\n\n", "\t \r\n", "# só comentário", "# a\n# b\n"])
def test_sem_tokens(codigo):
    assert analisar_lexico(codigo) == ([], [])


def test_token_no_fim_sem_quebra_de_linha():
    assert pares("x = 10") == [("IDENTIFICADOR", "x"), ("OPERADOR", "="), ("LITERAL_INTEIRO", "10")]
    assert pares('x = "fim"')[-1] == ("LITERAL_STRING", '"fim"')
    assert pares("x = y >=")[-1] == ("OPERADOR", ">=")


def test_ponto_no_fim_do_arquivo():
    assert [e["lexema"] for e in erros_de("x.")] == ["."]


def test_codigo_grande_nao_trava():
    codigo = "x = 1 + 2\n" * 1000
    tokens, erros = analisar_lexico(codigo)
    assert erros == []
    assert len(tokens) == 6000
