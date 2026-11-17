from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from parser import analisar_sintaxe
from scanner import analisar_lexico
from validacao import validar_codigo

app = Flask(__name__)


@app.get("/api/saude")
def saude():
    return jsonify(status="ok")


@app.post("/api/analisar")
def analisar():
    dados = request.get_json(silent=True)
    codigo, erro = validar_codigo(dados)
    if erro:
        return jsonify(recebido=False, erro=erro), 400

    # Etapa 3: análise léxica. Erros (léxicos ou sintáticos) não são erro da requisição:
    # a resposta continua 200 e quem diz se o código passou é o campo "sucesso".
    tokens, erros = analisar_lexico(codigo)

    # Etapa 4: o parser roda mesmo com erro léxico (decisão registrada em docs/fluxograma.md),
    # pulando os comandos que contêm erro léxico. Assim o aluno vê os dois tipos de erro de uma vez.
    ast, derivacao, erros_sintaticos, linhas_ignoradas = analisar_sintaxe(tokens, erros)

    return jsonify(
        sucesso=not erros and not erros_sintaticos,  # a partir da Etapa 4: léxico E sintático
        tokens=tokens,
        erros=erros,                                  # erros léxicos (mesmo formato da Etapa 3)
        ast=ast,
        derivacao=derivacao,
        erros_sintaticos=erros_sintaticos,
        linhas_ignoradas=linhas_ignoradas,
    )


@app.errorhandler(Exception)
def erro_inesperado(erro):
    # Erros HTTP comuns (404, 405...) seguem o tratamento padrão do Flask.
    if isinstance(erro, HTTPException):
        return erro
    # Qualquer outra exceção: mensagem genérica, sem detalhes internos.
    app.logger.exception("Erro inesperado")
    return jsonify(recebido=False, erro="Erro interno no servidor. Tente novamente mais tarde."), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
