"""Testes unitários do analisador sintático (parser.py).

Os resultados esperados vêm da gramática (docs/gramatica.md) e das regras de
precedência do Python, não da saída atual do parser.
"""
import pytest

from parser import REGRAS, analisar_sintaxe
from scanner import analisar_lexico


def analisar(codigo):
    tokens, erros_lexicos = analisar_lexico(codigo)
    assert erros_lexicos == [], erros_lexicos
    return analisar_sintaxe(tokens)


def compacta(no):
    """AST em texto curto: ATRIBUICAO(x, ADICAO(1, 2)). Folhas viram o próprio valor/nome."""
    if no["tipo"] == "IDENTIFICADOR":
        return no["atributos"]["nome"]
    if no["tipo"].startswith("LITERAL"):
        return no["atributos"]["valor"]
    nome = no["tipo"]
    if no["tipo"] in ("ATRIBUICAO", "CHAMADA_FUNCAO") and no["tipo"] == "CHAMADA_FUNCAO":
        nome = f"CHAMADA_FUNCAO:{no['atributos']['nome']}"
    if no["tipo"] == "COMPARACAO":
        nome = f"COMPARACAO{no['atributos']['operador']}"
    return f"{nome}({', '.join(compacta(f) for f in no['filhos'])})"


def arvore(codigo):
    """Forma compacta de cada comando do programa (deve ser válido)."""
    ast, _, erros = analisar(codigo)
    assert erros == [], [e["mensagem"] for e in erros]
    return [compacta(c) for c in ast["filhos"]]


def expr(codigo):
    """Forma compacta de uma única expressão."""
    comandos = arvore(codigo)
    assert len(comandos) == 1
    return comandos[0]


def erros(codigo):
    ast, derivacao, lista = analisar(codigo)
    assert ast is None and derivacao is None
    return lista


def erro(codigo):
    lista = erros(codigo)
    assert len(lista) == 1, [e["mensagem"] for e in lista]
    return lista[0]


# ---------- Construções válidas ----------

def test_atribuicao_simples():
    assert expr("idade = 17") == "ATRIBUICAO(idade, 17)"


@pytest.mark.parametrize("codigo, folha", [
    ("17", "17"), ("1.75", "1.75"), ('"Ana"', '"Ana"'), ("True", "True"), ("None", "None"), ("x", "x"),
])
def test_cada_tipo_de_valor(codigo, folha):
    assert expr(codigo) == folha


@pytest.mark.parametrize("codigo, tipo", [
    ("17", "LITERAL_INTEIRO"), ("1.5", "LITERAL_REAL"), ("'a'", "LITERAL_STRING"),
    ("False", "LITERAL_BOOLEANO"), ("None", "LITERAL_NONE"), ("nome", "IDENTIFICADOR"),
])
def test_tipo_do_no_folha(codigo, tipo):
    ast, _, _ = analisar(codigo)
    assert ast["filhos"][0]["tipo"] == tipo


@pytest.mark.parametrize("operador, tipo", [
    ("+", "ADICAO"), ("-", "SUBTRACAO"), ("*", "MULTIPLICACAO"), ("/", "DIVISAO"),
    ("//", "DIVISAO_INTEIRA"), ("%", "RESTO"), ("**", "POTENCIA"),
])
def test_cada_operador_aritmetico(operador, tipo):
    assert expr(f"a {operador} b") == f"{tipo}(a, b)"


@pytest.mark.parametrize("operador", ["==", "!=", "<", ">", "<=", ">="])
def test_cada_operador_relacional(operador):
    assert expr(f"a {operador} b") == f"COMPARACAO{operador}(a, b)"


def test_operadores_logicos():
    assert expr("a and b") == "E_LOGICO(a, b)"
    assert expr("a or b") == "OU_LOGICO(a, b)"
    assert expr("not a") == "NAO_LOGICO(a)"


def test_operadores_unarios():
    assert expr("-x") == "MENOS_UNARIO(x)"
    assert expr("+x") == "MAIS_UNARIO(x)"
    assert expr("- - x") == "MENOS_UNARIO(MENOS_UNARIO(x))"


def test_chamada_de_funcao():
    assert expr("print()") == "CHAMADA_FUNCAO:print()"
    assert expr('print("Oi")') == 'CHAMADA_FUNCAO:print("Oi")'
    assert expr('print("Idade:", idade + 1)') == 'CHAMADA_FUNCAO:print("Idade:", ADICAO(idade, 1))'
    assert expr("f(1,)") == "CHAMADA_FUNCAO:f(1)"  # vírgula final é aceita, como no Python


def test_chamada_aninhada_e_em_expressao():
    assert expr("x = abs(-2) + max(a, min(b, c))") == \
        "ATRIBUICAO(x, ADICAO(CHAMADA_FUNCAO:abs(MENOS_UNARIO(2)), CHAMADA_FUNCAO:max(a, CHAMADA_FUNCAO:min(b, c))))"


def test_programa_com_varios_comandos():
    codigo = 'idade = 17\nnome = "Ana"\n\n# comentário\nprint(nome, idade)\n'
    assert arvore(codigo) == ["ATRIBUICAO(idade, 17)", 'ATRIBUICAO(nome, "Ana")', "CHAMADA_FUNCAO:print(nome, idade)"]


def test_expressao_solta_e_um_comando_valido():
    assert arvore("x + 1\nTrue") == ["ADICAO(x, 1)", "True"]


def test_expressao_quebrada_dentro_de_parenteses():
    assert expr("total = (1 +\n         2)") == "ATRIBUICAO(total, ADICAO(1, 2))"


def test_combinacao_de_construcoes():
    codigo = "pode_votar = idade >= 16 and not (idade > 70) or convidado == True"
    assert expr(codigo) == (
        "ATRIBUICAO(pode_votar, OU_LOGICO(E_LOGICO(COMPARACAO>=(idade, 16), "
        "NAO_LOGICO(COMPARACAO>(idade, 70))), COMPARACAO==(convidado, True)))"
    )


# ---------- Precedência e associatividade ----------

@pytest.mark.parametrize("codigo, esperado", [
    ("resultado = 10 + 5 * 2", "ATRIBUICAO(resultado, ADICAO(10, MULTIPLICACAO(5, 2)))"),
    ("2 + 3 * 4", "ADICAO(2, MULTIPLICACAO(3, 4))"),
    ("2 * 3 + 4", "ADICAO(MULTIPLICACAO(2, 3), 4)"),
    ("10 - 3 - 2", "SUBTRACAO(SUBTRACAO(10, 3), 2)"),            # esquerda
    ("20 - 5 - 3", "SUBTRACAO(SUBTRACAO(20, 5), 3)"),
    ("8 / 4 / 2", "DIVISAO(DIVISAO(8, 4), 2)"),                  # esquerda
    ("(10 + 5) * 2", "MULTIPLICACAO(ADICAO(10, 5), 2)"),         # parênteses mudam a árvore
    ("10 - (3 - 2)", "SUBTRACAO(10, SUBTRACAO(3, 2))"),
    ("2 ** 3 ** 2", "POTENCIA(2, POTENCIA(3, 2))"),              # direita
    ("-2 ** 2", "MENOS_UNARIO(POTENCIA(2, 2))"),                 # ** pesa mais que o menos
    ("2 ** -1", "POTENCIA(2, MENOS_UNARIO(1))"),
    ("-a * b", "MULTIPLICACAO(MENOS_UNARIO(a), b)"),
    ("a + b > c * d", "COMPARACAO>(ADICAO(a, b), MULTIPLICACAO(c, d))"),
    ("not a == b", "NAO_LOGICO(COMPARACAO==(a, b))"),            # not pesa menos que ==
    ("not a and b", "E_LOGICO(NAO_LOGICO(a), b)"),
    ("a or b and c", "OU_LOGICO(a, E_LOGICO(b, c))"),            # and pesa mais que or
    ("a and b and c", "E_LOGICO(E_LOGICO(a, b), c)"),
    ("a or b or c", "OU_LOGICO(OU_LOGICO(a, b), c)"),
    ("not not a", "NAO_LOGICO(NAO_LOGICO(a))"),
    ("7 % 3 * 2 // 1", "DIVISAO_INTEIRA(MULTIPLICACAO(RESTO(7, 3), 2), 1)"),
])
def test_precedencia_e_associatividade(codigo, esperado):
    assert expr(codigo) == esperado


def test_parenteses_nao_viram_no_na_ast():
    assert expr("x = (((1)))") == "ATRIBUICAO(x, 1)"


# ---------- Formato e posições dos nós ----------

def test_formato_do_no():
    ast, _, _ = analisar("x = 10 + 5")
    atribuicao = ast["filhos"][0]
    adicao = atribuicao["filhos"][1]
    assert set(adicao) == {"id", "tipo", "rotulo", "atributos", "regra", "linha", "coluna",
                           "linhaFim", "colunaFim", "filhos"}
    assert adicao["tipo"] == "ADICAO"
    assert adicao["rotulo"] == "Adição (+)"
    assert adicao["atributos"] == {"operador": "+"}
    assert adicao["regra"] == REGRAS["soma"]
    assert atribuicao["atributos"] == {"nome": "x"}
    assert atribuicao["regra"] == REGRAS["atribuicao"]


def test_mesmo_tipo_de_no_tem_os_mesmos_atributos():
    ast, _, _ = analisar("a = 1 + 2 + 3\nb = x - 1")
    vistos = {}
    pilha = [ast]
    while pilha:
        no = pilha.pop()
        chaves = set(no["atributos"])
        assert vistos.setdefault(no["tipo"], chaves) == chaves
        pilha.extend(no["filhos"])


def test_posicoes_de_inicio_e_fim():
    ast, _, _ = analisar("total = (10 + 5) * 2\nprint(total)")
    atribuicao = ast["filhos"][0]
    mult = atribuicao["filhos"][1]
    soma = mult["filhos"][0]
    chamada = ast["filhos"][1]
    assert (atribuicao["linha"], atribuicao["coluna"], atribuicao["linhaFim"], atribuicao["colunaFim"]) == (1, 1, 1, 20)
    assert (mult["coluna"], mult["colunaFim"]) == (9, 20)    # "(10 + 5) * 2" inclui os parênteses
    assert (soma["coluna"], soma["colunaFim"]) == (10, 15)   # "10 + 5"
    assert (chamada["linha"], chamada["coluna"], chamada["colunaFim"]) == (2, 1, 12)
    assert (ast["linha"], ast["coluna"], ast["linhaFim"], ast["colunaFim"]) == (1, 1, 2, 12)


def test_posicao_de_no_em_varias_linhas():
    ast, _, _ = analisar("x = (1 +\n     2)")
    soma = ast["filhos"][0]["filhos"][1]
    assert (soma["linha"], soma["coluna"], soma["linhaFim"], soma["colunaFim"]) == (1, 6, 2, 6)


def test_folhas_tem_a_posicao_do_token():
    tokens, _ = analisar_lexico('nome = "Ana" + sobrenome')
    ast, _, _ = analisar_sintaxe(tokens)
    folhas = []
    pilha = [ast]
    while pilha:
        no = pilha.pop()
        if not no["filhos"] and no["tipo"] != "PROGRAMA":
            folhas.append((no["linha"], no["coluna"]))
        pilha.extend(no["filhos"])
    posicoes_tokens = {(t["linha"], t["coluna"]) for t in tokens}
    assert set(folhas) <= posicoes_tokens
    assert len(folhas) == 3


def test_ids_seguem_a_ordem_de_construcao():
    # Os filhos são construídos antes do pai: o passo a passo da tela usa essa ordem.
    ast, _, _ = analisar("r = 10 + 5 * 2")
    ordem = {}
    pilha = [ast]
    while pilha:
        no = pilha.pop()
        ordem[compacta(no) if no["tipo"] != "PROGRAMA" else "PROGRAMA"] = no["id"]
        for filho in no["filhos"]:
            assert filho["id"] < no["id"]
        pilha.extend(no["filhos"])
    assert sorted(ordem.values()) == list(range(1, 9))  # 8 nós: r, 10, 5, 2, *, +, =, programa
    assert ordem["MULTIPLICACAO(5, 2)"] < ordem["ADICAO(10, MULTIPLICACAO(5, 2))"]


def test_programa_vazio():
    ast, derivacao, lista = analisar_sintaxe([])
    assert lista == []
    assert ast["tipo"] == "PROGRAMA" and ast["filhos"] == []
    assert derivacao == {"tipo": "NAO_TERMINAL", "simbolo": "programa", "filhos": []}


def test_so_comentarios():
    assert arvore("# só comentário\n\n# outro") == []


# ---------- Árvore de derivação ----------

def folhas_da_derivacao(no):
    if no["tipo"] == "TERMINAL":
        return [(no["lexema"], no["linha"], no["coluna"])]
    return [f for filho in no["filhos"] for f in folhas_da_derivacao(filho)]


@pytest.mark.parametrize("codigo", [
    "x = 1", "r = (10 + 5) * 2\nprint(r, 'ok')", "a = not (b or c) and -d ** 2 >= 3", "f()\ng(1,)\n",
])
def test_folhas_da_derivacao_sao_os_tokens(codigo):
    # O parser consumiu todos os tokens, na ordem, sem inventar nenhum.
    tokens, _ = analisar_lexico(codigo)
    _, derivacao, _ = analisar_sintaxe(tokens)
    assert folhas_da_derivacao(derivacao) == [(t["lexema"], t["linha"], t["coluna"]) for t in tokens]


def test_derivacao_mostra_os_nao_terminais_e_os_parenteses():
    _, derivacao, _ = analisar("x = (1)")
    simbolos = []
    pilha = [derivacao]
    while pilha:
        no = pilha.pop()
        simbolos.append(no["simbolo"])
        pilha.extend(no.get("filhos", []))
    for nao_terminal in ["programa", "comando", "atribuicao", "expressao", "disjuncao", "conjuncao",
                         "negacao", "comparacao", "soma", "termo", "unario", "potencia", "primario"]:
        assert nao_terminal in simbolos
    assert "DELIMITADOR" in simbolos  # os parênteses aparecem na derivação (e não na AST)


def test_derivacao_e_maior_que_a_ast():
    ast, derivacao, _ = analisar("x = 1 + 2")

    def contar(no):
        return 1 + sum(contar(f) for f in no.get("filhos", []))

    assert contar(derivacao) > contar(ast)


# ---------- Erros sintáticos ----------

def test_formato_do_erro():
    e = erro("x = 5 +")
    assert set(e) == {"tipo", "linha", "coluna", "encontrado", "esperado", "regra", "mensagem"}
    assert e["tipo"] == "ERRO_SINTATICO"
    assert e["mensagem"].startswith(f"Erro sintático na linha {e['linha']}, coluna {e['coluna']}: ")


def test_expressao_incompleta_no_fim_da_linha():
    e = erro("x = 5 +\ny = 1")
    assert (e["linha"], e["coluna"]) == (1, 8)
    assert e["encontrado"] == "o fim da linha"
    assert "depois de '+' era esperado um valor" in e["mensagem"]
    assert e["regra"] == REGRAS["primario"]
    assert "nome" in e["esperado"] and "número" in e["esperado"]


def test_expressao_incompleta_no_fim_do_codigo():
    e = erro("x =")
    assert e["encontrado"] == "o fim do código"
    assert (e["linha"], e["coluna"]) == (1, 4)


def test_operadores_seguidos():
    e = erro("y = 5 + * 2")
    assert e["encontrado"] == "'*'"
    assert (e["linha"], e["coluna"]) == (1, 9)
    assert "dois operadores seguidos" in e["mensagem"]


def test_operador_composto_fora_do_subconjunto():
    e = erro("x += 1")
    assert "'+='" in e["mensagem"] and "x = x + 1" in e["mensagem"]


@pytest.mark.parametrize("codigo", ["17 = idade", "None = 1", "x + 1 = 2", '"a" = b'])
def test_lado_esquerdo_da_atribuicao_precisa_ser_nome(codigo):
    e = erro(codigo)
    assert "só um nome (identificador) pode receber um valor" in e["mensagem"]
    assert e["encontrado"] == "'='"


def test_atribuicao_multipla():
    assert "atribuição múltipla" in erro("x = y = 1")["mensagem"]


def test_parentese_nao_fechado_aponta_onde_abriu():
    e = erro("y = (1 + 2\n")
    assert "parêntese aberto na linha 1, coluna 5" in e["mensagem"]
    assert e["esperado"] == [")"]


def test_parentese_nao_fechado_antes_de_outro_token():
    e = erro("y = (1 + 2 3)")
    assert e["encontrado"] == "'3'"
    assert "para fechar o parêntese aberto na linha 1, coluna 5" in e["mensagem"]


def test_parentese_sobrando():
    e = erro("z = (1 + 2))")
    assert (e["linha"], e["coluna"]) == (1, 12)
    assert "sobrando" in e["mensagem"]


def test_parenteses_vazios():
    e = erro("x = ()")
    assert e["encontrado"] == "')'"


def test_argumentos_sem_virgula():
    e = erro('print("a" "b")')
    assert e["esperado"] == [",", ")"]
    assert e["encontrado"] == "'\"b\"'"
    assert "chamada de 'print' (aberta na linha 1, coluna 6)" in e["mensagem"]
    assert e["regra"] == REGRAS["argumentos"]


def test_chamada_nao_fechada_no_fim_do_codigo():
    e = erro("print(1, 2")
    assert e["encontrado"] == "o fim do código"


@pytest.mark.parametrize("palavra", ["if", "else", "while", "for", "def", "return"])
def test_palavra_reservada_fora_do_subconjunto_no_comando(palavra):
    e = erro(f"{palavra} x")
    assert f"palavra reservada '{palavra}' não faz parte do subconjunto" in e["mensagem"]


def test_palavra_reservada_onde_se_esperava_valor():
    assert "palavra reservada 'and' não pode ser usada como valor" in erro("x = and")["mensagem"]
    assert "palavra reservada 'while'" in erro("x = while")["mensagem"]


def test_comando_comecando_com_igual():
    e = erro("= = 17 idade")
    assert (e["linha"], e["coluna"]) == (1, 1)
    assert "não pode começar com '='" in e["mensagem"]


def test_comparacao_encadeada():
    e = erro("a < b < c")
    assert "comparações encadeadas" in e["mensagem"]
    assert e["regra"] == REGRAS["comparacao"]


def test_dois_valores_sem_operador():
    e = erro("x = 1 2")
    assert e["encontrado"] == "'2'"
    assert e["esperado"] == ["fim da linha"]
    assert "talvez falte um operador" in e["mensagem"]


def test_virgula_fora_de_chamada():
    e = erro("x = 1, 2")
    assert e["encontrado"] == "','"


# ---------- Recuperação de erros ----------

def test_acumula_um_erro_por_comando():
    codigo = "x = 5 +\ny = * 2\nz = (1 + 2))\n17 = idade"
    assert [(e["linha"], e["coluna"]) for e in erros(codigo)] == [(1, 8), (2, 5), (3, 12), (4, 4)]


def test_sem_cascata_na_mesma_linha():
    # Vários problemas na mesma linha geram um único erro.
    assert len(erros("x = + * / 1 2 3 ) ) (")) == 1


def test_comandos_validos_entre_os_erros_nao_geram_erro():
    codigo = "a = 1\nb = 2 +\nc = 3\nd = )\ne = 5"
    assert [e["linha"] for e in erros(codigo)] == [2, 4]


def test_parentese_aberto_engole_o_resto_e_gera_um_so_erro():
    # Dentro de parênteses a quebra de linha não encerra o comando (como no Python).
    assert len(erros("x = (1 +\ny = 2\nz = 3")) == 1


# ---------- Limites e entradas patológicas ----------

@pytest.mark.parametrize("codigo", [
    "(" * 300 + "1" + ")" * 300,
    "x = " + "-" * 3000 + "1",
    "x = " + "not " * 2000 + "a",
    "x = " + "1 + " * 2000 + "1",
    "x = " + "2 ** " * 2000 + "2",
    "x = " + "f(" * 500 + "1" + ")" * 500,
])
def test_entrada_aninhada_demais_vira_erro_sintatico(codigo):
    e = erro(codigo)
    assert "aninhada ou longa demais" in e["mensagem"]


def test_aninhamento_razoavel_e_aceito():
    assert expr("x = " + "(" * 30 + "1" + ")" * 30) == "ATRIBUICAO(x, 1)"
    assert expr("x = " + " + ".join(["1"] * 100)).startswith("ATRIBUICAO(x, ADICAO(")


# ---------- Integração com o scanner ----------

@pytest.mark.parametrize("codigo", [
    "idade = 17\naltura = 1.75",
    'idade = 17\nidade_texto = "17"\nnome = "Ana"',
    "aprovado = True\npendente = False\nsituacao = aprovado",
    "idade = 17\nproxima = idade + 1\nmaior = idade >= 18 and not False",
    '# média\nnota1 = 7.5\nmedia = (nota1 + 9) / 2  # divisão\nprint("Média:", media)',
])
def test_exemplos_validos_da_etapa_3_sao_aceitos(codigo):
    ast, _, lista = analisar(codigo)
    assert lista == []
    assert ast["tipo"] == "PROGRAMA"


def test_comando_unico_sem_quebra_de_linha_no_fim():
    assert arvore("x = 1") == ["ATRIBUICAO(x, 1)"]


def test_crlf():
    assert arvore("a = 1\r\nb = a\r\n") == ["ATRIBUICAO(a, 1)", "ATRIBUICAO(b, a)"]
