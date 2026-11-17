"""Teste diferencial: a AST do nosso parser contra a AST do próprio Python.

Para programas válidos do subconjunto, a estrutura da nossa árvore precisa ser
igual à que o módulo `ast` da biblioteca padrão produz. Isso confirma, contra o
interpretador real, que precedência e associatividade estão corretas.

As duas árvores são convertidas para a mesma forma compacta, por exemplo
ATRIBUICAO(x, ADICAO(1, MULTIPLICACAO(2, 3))). Diferença conhecida e tratada na
conversão: o Python junta `a and b and c` num único nó com 3 valores; aqui ele é
convertido para a forma binária à esquerda, igual à nossa. Já a comparação
encadeada (a < b < c) é um nó só nas duas árvores.
"""
import ast as py_ast

import pytest

from parser import analisar_sintaxe
from scanner import analisar_lexico

OPERADORES_PY = {
    py_ast.Add: "ADICAO", py_ast.Sub: "SUBTRACAO", py_ast.Mult: "MULTIPLICACAO",
    py_ast.Div: "DIVISAO", py_ast.FloorDiv: "DIVISAO_INTEIRA", py_ast.Mod: "RESTO",
    py_ast.Pow: "POTENCIA",
}
UNARIOS_PY = {py_ast.USub: "MENOS_UNARIO", py_ast.UAdd: "MAIS_UNARIO", py_ast.Not: "NAO_LOGICO"}
COMPARACOES_PY = {
    py_ast.Eq: "==", py_ast.NotEq: "!=", py_ast.Lt: "<", py_ast.Gt: ">", py_ast.LtE: "<=", py_ast.GtE: ">=",
}


def do_python(no):
    if isinstance(no, py_ast.Module):
        return [do_python(c) for c in no.body]
    if isinstance(no, py_ast.Assign):
        return f"ATRIBUICAO({no.targets[0].id}, {do_python(no.value)})"
    if isinstance(no, py_ast.Expr):
        return do_python(no.value)
    if isinstance(no, py_ast.BinOp):
        return f"{OPERADORES_PY[type(no.op)]}({do_python(no.left)}, {do_python(no.right)})"
    if isinstance(no, py_ast.UnaryOp):
        return f"{UNARIOS_PY[type(no.op)]}({do_python(no.operand)})"
    if isinstance(no, py_ast.BoolOp):
        tipo = "E_LOGICO" if isinstance(no.op, py_ast.And) else "OU_LOGICO"
        texto = do_python(no.values[0])
        for valor in no.values[1:]:
            texto = f"{tipo}({texto}, {do_python(valor)})"
        return texto
    if isinstance(no, py_ast.Compare):
        operadores = ",".join(COMPARACOES_PY[type(op)] for op in no.ops)
        operandos = [do_python(no.left)] + [do_python(c) for c in no.comparators]
        return f"COMPARACAO{operadores}({', '.join(operandos)})"
    if isinstance(no, py_ast.Call):
        return f"CHAMADA:{do_python(no.func)}({', '.join(do_python(a) for a in no.args)})"
    if isinstance(no, py_ast.Name):
        return no.id
    if isinstance(no, py_ast.Constant):
        return f"CONST:{type(no.value).__name__}:{no.value!r}"
    raise AssertionError(f"nó do Python fora do subconjunto: {type(no).__name__}")


TIPOS_LITERAIS = {
    "LITERAL_INTEIRO": int, "LITERAL_REAL": float, "LITERAL_BOOLEANO": bool, "LITERAL_NONE": type(None),
}


def do_nosso(no):
    tipo = no["tipo"]
    if tipo == "PROGRAMA":
        return [do_nosso(c) for c in no["filhos"]]
    if tipo == "IDENTIFICADOR":
        return no["atributos"]["nome"]
    if tipo in TIPOS_LITERAIS or tipo == "LITERAL_STRING":
        valor = py_ast.literal_eval(no["atributos"]["valor"])  # "17" -> 17, '"Ana"' -> 'Ana'
        return f"CONST:{type(valor).__name__}:{valor!r}"
    if tipo == "ATRIBUICAO":
        return f"ATRIBUICAO({no['atributos']['nome']}, {do_nosso(no['filhos'][1])})"
    if tipo == "CHAMADA_FUNCAO":
        chamado, *argumentos = no["filhos"]
        return f"CHAMADA:{do_nosso(chamado)}({', '.join(do_nosso(f) for f in argumentos)})"
    if tipo == "COMPARACAO":
        tipo = "COMPARACAO" + ",".join(no["atributos"]["operadores"])
    return f"{tipo}({', '.join(do_nosso(f) for f in no['filhos'])})"


PROGRAMAS = [
    # Exemplos da interface sem erro intencional
    "idade = 17\naltura = 1.75",
    'idade = 17\nidade_texto = "17"\nnome = "Ana"',
    "aprovado = True\npendente = False\nsituacao = aprovado",
    "idade = 17\nproxima = idade + 1\nmaior = idade >= 18 and not False",
    '# média\nnota1 = 7.5\nmedia = (nota1 + 9) / 2  # divisão\nprint("Média:", media)',
    "resultado = 10 + 5 * 2\nsubtracao = 20 - 5 - 3\ncom_parenteses = (10 + 5) * 2",
    'idade = 17\npode_votar = idade >= 16 and not (idade > 70)\nprint("Vota?", pode_votar)',
    # Precedência e associatividade
    "r = 2 + 3 * 4 - 5 / 6 // 7 % 8",
    "r = 10 - 3 - 2",
    "r = 2 ** 3 ** 2",
    "r = -2 ** 2",
    "r = 2 ** -1",
    "r = -a * +b - -c",
    "r = not a == b",
    "r = a or b and c or not d",
    "r = a and b and c",
    "r = a or b or c",
    "r = (a or b) and c",
    "r = a + b >= c * d",
    "r = a < b <= c != d",
    "ok = 0 <= nota < 10 == True",
    "r = not not x",
    "r = ((1 + 2) * (3 - 4)) ** 2",
    # Chamadas e valores
    "print()",
    "print(1, 2.5, 'tres', True, None)",
    "x = max(a, min(b, -c)) + abs(d)",
    "f(1)(2)",
    "x = (f)(a, b)(c)",
    "y = g(1) ** 2",
    "x = (1 +\n     2)",
    "x + 1\nTrue",
]


@pytest.mark.parametrize("codigo", PROGRAMAS)
def test_nossa_ast_tem_a_mesma_estrutura_que_a_do_python(codigo):
    tokens, erros_lexicos = analisar_lexico(codigo)
    assert erros_lexicos == []
    ast, _, erros, _ = analisar_sintaxe(tokens)
    assert erros == [], [e["mensagem"] for e in erros]
    assert do_nosso(ast) == do_python(py_ast.parse(codigo))


@pytest.mark.parametrize("codigo", [
    "x = 5 +", "y = * 2", "z = (1 + 2))", "17 = idade", "x = 1 2", "print('a' 'b' 1)",
    "= = 17 idade", "x = (1 + 2", "print(1, 2",
])
def test_o_que_rejeitamos_o_python_tambem_rejeita(codigo):
    # Nenhum falso erro: tudo que o nosso parser recusa também é inválido para o Python.
    tokens, _ = analisar_lexico(codigo)
    _, _, erros, _ = analisar_sintaxe(tokens)
    assert erros != []
    with pytest.raises(SyntaxError):
        compile(codigo, "<teste>", "exec")
