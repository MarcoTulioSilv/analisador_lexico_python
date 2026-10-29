"""Teste diferencial: o nosso scanner contra o tokenizador do próprio Python.

Para programas válidos do subconjunto, a sequência de lexemas e posições
produzida por scanner.py tem que ser idêntica à do módulo tokenize da
biblioteca padrão (o interpretador real). As categorias não são comparadas,
porque as nossas são mais didáticas (o tokenize chama tudo de NAME, OP...).
"""
import io
import tokenize

import pytest

from scanner import analisar_lexico

# tokenize gera tokens que o nosso scanner descarta de propósito.
IGNORADOS = {tokenize.COMMENT, tokenize.NL, tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT}

PROGRAMAS = [
    # Os 7 exemplos da interface que não têm erro intencional
    "idade = 17\naltura = 1.75",
    'idade = 17\nidade_texto = "17"\nnome = "Ana"',
    "aprovado = True\npendente = False\nsituacao = aprovado",
    "idade = 17\nproxima = idade + 1\nmaior = idade >= 18 and not False",
    '# média\nnota1 = 7.5\nmedia = (nota1 + 9) / 2  # divisão\nprint("Média:", media)',
    # Outros casos
    "x = 1\n",
    "a=b==c!=d<=e>=f<g>h",
    "r = 2 ** 3 // 4 % 5 - 6 * 7 / 8",
    "x = .5 + 3. - 0.25",
    "ok = not (a or b) and c is None",
    "print(1,\n      2,\n      3)\n",
    "\n\n# comentário\nx = 1\n\n\ny = 2\n",
    "s = 'it\\'s' + \"diz \\\"oi\\\"\"",
    "ação = 'coração 😀'\nfim = ação",
    "x = 1  # comentário no fim",
    "x\t=\t1\ty = x",
]


def tokens_do_python(codigo):
    tokens = tokenize.generate_tokens(io.StringIO(codigo).readline)
    return [
        (t.string, t.start[0], t.start[1] + 1)  # tokenize conta colunas a partir de 0
        for t in tokens
        if t.type not in IGNORADOS
    ]


def tokens_do_scanner(codigo):
    tokens, erros = analisar_lexico(codigo)
    assert erros == []
    return [(t["lexema"], t["linha"], t["coluna"]) for t in tokens]


@pytest.mark.parametrize("codigo", PROGRAMAS)
def test_scanner_igual_ao_tokenize_do_python(codigo):
    assert tokens_do_scanner(codigo) == tokens_do_python(codigo)
