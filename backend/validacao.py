"""Validações iniciais do código-fonte recebido pela API.

Nesta etapa o código NÃO é analisado: só verificamos se a requisição traz
um texto que possa ser processado nas próximas etapas.
"""

LIMITE_CARACTERES = 10_000

ERRO_JSON = 'Requisição inválida: envie um JSON no formato {"codigo": "..."}.'
ERRO_CAMPO = 'O campo "codigo" é obrigatório e deve ser um texto.'
ERRO_VAZIO = "Informe um código-fonte antes de solicitar a análise."
ERRO_LIMITE = "O código excede o limite de 10.000 caracteres."


def validar_codigo(dados):
    """Devolve (codigo, None) se a entrada for aceita, ou (None, mensagem de erro)."""
    if not isinstance(dados, dict):
        return None, ERRO_JSON

    codigo = dados.get("codigo")
    if not isinstance(codigo, str):
        return None, ERRO_CAMPO

    if codigo.strip() == "":
        return None, ERRO_VAZIO

    if len(codigo) > LIMITE_CARACTERES:
        return None, ERRO_LIMITE

    return codigo, None
