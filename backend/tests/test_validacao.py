"""Testes unitários da função validar_codigo."""
import pytest

from validacao import (
    ERRO_CAMPO,
    ERRO_JSON,
    ERRO_LIMITE,
    ERRO_VAZIO,
    LIMITE_CARACTERES,
    validar_codigo,
)


@pytest.mark.parametrize(
    "codigo",
    [
        "idade = 17",
        "idade = 17\naltura = 1.75\n",
        'nome = "Ana',  # erro intencional: string não fechada também é aceita
        'texto = "ação, coração 😀"',
        "a = 'aspas simples' # comentário\t{}",
        "   idade = 17   ",  # espaços em volta não tornam a entrada vazia
    ],
)
def test_aceita_codigo_com_conteudo(codigo):
    assert validar_codigo({"codigo": codigo}) == (codigo, None)


def test_preserva_o_codigo_sem_alterar():
    codigo = "  x = 1\r\n\ty = 2  "
    recebido, erro = validar_codigo({"codigo": codigo})
    assert erro is None
    assert recebido == codigo


@pytest.mark.parametrize("codigo", ["", " ", "     ", "\n", "\t", " \n\t \r\n "])
def test_recusa_codigo_vazio_ou_so_espacos(codigo):
    assert validar_codigo({"codigo": codigo}) == (None, ERRO_VAZIO)


@pytest.mark.parametrize("valor", [None, 17, 1.5, True, ["x = 1"], {"x": 1}])
def test_recusa_codigo_que_nao_e_texto(valor):
    assert validar_codigo({"codigo": valor}) == (None, ERRO_CAMPO)


def test_recusa_campo_ausente():
    assert validar_codigo({"outro": "x = 1"}) == (None, ERRO_CAMPO)


@pytest.mark.parametrize("dados", [None, "x = 1", ["x = 1"], 17])
def test_recusa_corpo_que_nao_e_objeto_json(dados):
    assert validar_codigo(dados) == (None, ERRO_JSON)


def test_aceita_exatamente_o_limite():
    codigo = "x" * LIMITE_CARACTERES
    assert validar_codigo({"codigo": codigo}) == (codigo, None)


def test_recusa_acima_do_limite():
    codigo = "x" * (LIMITE_CARACTERES + 1)
    assert validar_codigo({"codigo": codigo}) == (None, ERRO_LIMITE)
