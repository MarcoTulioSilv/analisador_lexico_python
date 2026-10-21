from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

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

    # A análise léxica entra aqui nas próximas etapas.
    return jsonify(
        recebido=True,
        mensagem="Código recebido com sucesso.",
        linhas=len(codigo.splitlines()),
        caracteres=len(codigo),
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
