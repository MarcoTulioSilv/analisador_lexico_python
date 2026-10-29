from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

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

    # Etapa 3: análise léxica. Erros léxicos não são erro da requisição (continua 200);
    # quem diz se o código passou é o campo "sucesso".
    tokens, erros = analisar_lexico(codigo)
    return jsonify(sucesso=not erros, tokens=tokens, erros=erros)


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
