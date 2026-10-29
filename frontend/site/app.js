// Interação da tela: exemplos, validação no navegador, comunicação com o backend
// e apresentação didática do resultado da análise léxica.
// Todo conteúdo vindo do usuário entra na página via textContent (nunca innerHTML).

const MSG_VAZIO = "Informe um código-fonte antes de solicitar a análise.";
const MSG_SEM_CONEXAO = "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.";
const MSG_INESPERADO = "Ocorreu um erro inesperado. Tente novamente mais tarde.";
const INTERVALO_REPRODUCAO_MS = 800;

const seletor = document.getElementById("exemplos");
const campoCodigo = document.getElementById("codigo");
const botao = document.getElementById("analisar");
const resultado = document.getElementById("resultado");

const areaAnalise = document.getElementById("analise");
const secaoErros = document.getElementById("secao-erros");
const listaErros = document.getElementById("lista-erros");
const codigoColorido = document.getElementById("codigo-colorido");
const contagem = document.getElementById("contagem");
const corpoTabela = document.querySelector("#tabela-tokens tbody");
const botaoAnterior = document.getElementById("passo-anterior");
const botaoReproduzir = document.getElementById("passo-reproduzir");
const botaoProximo = document.getElementById("passo-proximo");
const explicacaoPasso = document.getElementById("passo-explicacao");

// tipo: "sucesso" | "aviso" (problema na entrada) | "erro" (comunicação ou servidor)
function mostrarResultado(texto, tipo) {
  resultado.textContent = texto;
  resultado.className = tipo;
}

function criar(tag, texto, classe) {
  const el = document.createElement(tag);
  if (texto !== undefined) el.textContent = texto;
  if (classe) el.className = classe;
  return el;
}

// Como o lexema aparece para o aluno (a quebra de linha é invisível).
function lexemaVisivel(token) {
  if (token.tipo === "NOVA_LINHA") return token.lexema === "" ? "(fim do código)" : "↵ (quebra de linha)";
  return token.lexema;
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
  limparAnalise();

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

    if (resposta.ok && dados && Array.isArray(dados.tokens) && Array.isArray(dados.erros)) {
      mostrarAnalise(codigo, dados);
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

// ---------- Resultado da análise léxica ----------

let tokensAtuais = [];
let passoAtual = -1;
let temporizador = null;

function limparAnalise() {
  pararReproducao();
  areaAnalise.hidden = true;
  tokensAtuais = [];
  passoAtual = -1;
}

function mostrarAnalise(codigo, dados) {
  const { tokens, erros } = dados;
  tokensAtuais = tokens;

  if (erros.length === 0) {
    mostrarResultado(`Análise léxica concluída: ${tokens.length} token(s) reconhecido(s).`, "sucesso");
  } else {
    mostrarResultado(
      `A análise léxica encontrou ${erros.length} erro(s). ` +
        `Veja os detalhes abaixo (${tokens.length} token(s) foram reconhecidos).`,
      "aviso"
    );
  }

  listaErros.replaceChildren(...erros.map((erro) => criar("li", erro.mensagem)));
  secaoErros.hidden = erros.length === 0;

  desenharCodigoColorido(codigo, tokens, erros);
  desenharContagem(tokens);
  desenharTabela(tokens);

  areaAnalise.hidden = false;
  irParaPasso(-1);
}

// Monta o código de novo, linha por linha, envolvendo cada token num <span> colorido.
// Linha e coluna vêm do backend contadas em caracteres (code points); Array.from
// separa a linha do mesmo jeito, então acentos e emoji não desalinham a marcação.
function desenharCodigoColorido(codigo, tokens, erros) {
  const marcas = [
    ...tokens.map((token, indice) => ({ ...token, indice })),
    ...erros.map((erro) => ({ ...erro, ehErro: true })),
  ];
  const linhas = codigo.split("\n");
  const partes = [];

  linhas.forEach((textoLinha, i) => {
    const caracteres = Array.from(textoLinha.replace(/\r$/, ""));
    const daLinha = marcas
      .filter((m) => m.linha === i + 1)
      .sort((a, b) => a.coluna - b.coluna || (a.tipo === "NOVA_LINHA") - (b.tipo === "NOVA_LINHA"));
    let coluna = 1;

    for (const marca of daLinha) {
      if (marca.coluna < coluna) continue; // sobreposição (não deveria acontecer)
      if (marca.coluna > coluna) {
        partes.push(document.createTextNode(caracteres.slice(coluna - 1, marca.coluna - 1).join("")));
        coluna = marca.coluna;
      }
      if (marca.tipo === "NOVA_LINHA") {
        const span = criar("span", "↵", `tk tk-NOVA_LINHA`);
        span.dataset.indice = marca.indice;
        partes.push(span);
        continue;
      }
      const tamanho = Array.from(marca.lexema).length;
      const texto = caracteres.slice(coluna - 1, coluna - 1 + tamanho).join("");
      if (marca.ehErro) {
        const span = criar("span", texto, "tk-erro");
        span.title = marca.mensagem;
        partes.push(span);
      } else {
        const span = criar("span", texto, `tk tk-${marca.tipo}`);
        span.dataset.indice = marca.indice;
        span.title = `${marca.tipo}: ${marca.descricao}`;
        partes.push(span);
      }
      coluna += tamanho;
    }

    if (coluna <= caracteres.length) {
      partes.push(document.createTextNode(caracteres.slice(coluna - 1).join("")));
    }
    if (i < linhas.length - 1) partes.push(document.createTextNode("\n"));
  });

  codigoColorido.replaceChildren(...partes);
}

function desenharContagem(tokens) {
  const porTipo = new Map();
  for (const token of tokens) porTipo.set(token.tipo, (porTipo.get(token.tipo) || 0) + 1);
  contagem.replaceChildren(
    ...[...porTipo].map(([tipo, quantidade]) => {
      const chip = criar("span", `${tipo} × ${quantidade}`, `chip tk-${tipo}`);
      chip.dataset.tipo = tipo;
      return chip;
    })
  );
}

function desenharTabela(tokens) {
  corpoTabela.replaceChildren(
    ...tokens.map((token, indice) => {
      const linha = document.createElement("tr");
      linha.dataset.indice = indice;
      const lexema = criar("td");
      lexema.appendChild(criar("code", lexemaVisivel(token)));
      linha.append(
        criar("td", String(indice + 1)),
        criar("td", token.tipo, `tk-${token.tipo}`),
        lexema,
        criar("td", String(token.linha)),
        criar("td", String(token.coluna)),
        criar("td", token.descricao)
      );
      return linha;
    })
  );
}

// ---------- Passo a passo ----------

function irParaPasso(indice) {
  passoAtual = indice;
  document.querySelectorAll(".atual").forEach((el) => el.classList.remove("atual"));

  const total = tokensAtuais.length;
  if (total === 0) {
    explicacaoPasso.textContent = "Nenhum token foi reconhecido: o código só tem espaços, comentários ou erros.";
  } else if (indice < 0) {
    explicacaoPasso.textContent =
      `O scanner reconheceu ${total} token(s). Clique em "Próximo" para vê-lo ler o código, um token por vez.`;
  } else {
    const token = tokensAtuais[indice];
    document.querySelectorAll(`[data-indice="${indice}"]`).forEach((el) => el.classList.add("atual"));
    explicacaoPasso.textContent =
      `Passo ${indice + 1} de ${total}: o scanner leu ${lexemaVisivel(token)} ` +
      `na linha ${token.linha}, coluna ${token.coluna} → ${token.tipo} (${token.descricao}).`;
  }

  botaoAnterior.disabled = indice < 0;
  botaoProximo.disabled = indice >= total - 1;
  botaoReproduzir.disabled = total === 0;
}

function pararReproducao() {
  clearInterval(temporizador);
  temporizador = null;
  botaoReproduzir.textContent = "▶ Reproduzir";
}

botaoAnterior.addEventListener("click", () => {
  pararReproducao();
  irParaPasso(passoAtual - 1);
});

botaoProximo.addEventListener("click", () => {
  pararReproducao();
  irParaPasso(passoAtual + 1);
});

botaoReproduzir.addEventListener("click", () => {
  if (temporizador) {
    pararReproducao();
    return;
  }
  if (passoAtual >= tokensAtuais.length - 1) irParaPasso(-1); // chegou ao fim: recomeça
  botaoReproduzir.textContent = "⏸ Pausar";
  temporizador = setInterval(() => {
    irParaPasso(passoAtual + 1);
    if (passoAtual >= tokensAtuais.length - 1) pararReproducao();
  }, INTERVALO_REPRODUCAO_MS);
});
