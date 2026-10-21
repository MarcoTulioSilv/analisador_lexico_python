// Interação da tela: exemplos, validação no navegador e comunicação com o backend.

const MSG_VAZIO = "Informe um código-fonte antes de solicitar a análise.";
const MSG_SEM_CONEXAO = "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.";
const MSG_INESPERADO = "Ocorreu um erro inesperado. Tente novamente mais tarde.";

const seletor = document.getElementById("exemplos");
const campoCodigo = document.getElementById("codigo");
const botao = document.getElementById("analisar");
const resultado = document.getElementById("resultado");

// tipo: "sucesso" | "aviso" (problema na entrada) | "erro" (comunicação ou servidor)
function mostrarResultado(texto, tipo) {
  resultado.textContent = texto;
  resultado.className = tipo;
}

// ---------- Exemplos ----------

EXEMPLOS.forEach((exemplo, indice) => {
  const opcao = document.createElement("option");
  opcao.value = String(indice);
  opcao.textContent = exemplo.titulo;
  seletor.appendChild(opcao);
});

seletor.addEventListener("change", () => {
  if (seletor.value === "") return;
  // Escolher um exemplo substitui o conteúdo do campo.
  campoCodigo.value = EXEMPLOS[Number(seletor.value)].codigo;
  campoCodigo.focus();
});

// ---------- Envio ----------

async function analisar() {
  const codigo = campoCodigo.value;

  if (codigo.trim() === "") {
    mostrarResultado(MSG_VAZIO, "aviso");
    return;
  }

  botao.disabled = true;
  botao.textContent = "Enviando...";
  try {
    let resposta;
    try {
      resposta = await fetch("/api/analisar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codigo }),
      });
    } catch {
      mostrarResultado(MSG_SEM_CONEXAO, "erro");
      return;
    }

    const dados = await resposta.json().catch(() => null);

    if (resposta.ok && dados && dados.recebido) {
      mostrarResultado(
        `${dados.mensagem} (${dados.linhas} linha(s), ${dados.caracteres} caractere(s))`,
        "sucesso"
      );
    } else if (resposta.status === 400 && dados && dados.erro) {
      mostrarResultado(dados.erro, "aviso");
    } else {
      mostrarResultado(MSG_INESPERADO, "erro");
    }
  } finally {
    botao.disabled = false;
    botao.textContent = "Analisar";
  }
}

botao.addEventListener("click", analisar);
