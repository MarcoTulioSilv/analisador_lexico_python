// Análise sintática (Etapa 4): resumo, erros sintáticos, AST, árvore de derivação
// e construção da AST passo a passo. Usa as funções e elementos de app.js
// (criar, codigoColorido, INTERVALO_REPRODUCAO_MS), que é carregado antes.
// Todo conteúdo vindo do usuário entra na página via textContent (nunca innerHTML).

const resultadoSintatico = document.getElementById("resultado-sintatico");
const secaoErrosSintaticos = document.getElementById("secao-erros-sintaticos");
const listaErrosSintaticos = document.getElementById("lista-erros-sintaticos");
const secaoArvore = document.getElementById("secao-arvore");
const contagemArvores = document.getElementById("contagem-arvores");
const abaAst = document.getElementById("aba-ast");
const abaDerivacao = document.getElementById("aba-derivacao");
const painelAst = document.getElementById("painel-ast");
const painelDerivacao = document.getElementById("painel-derivacao");
const arvoreAst = document.getElementById("arvore-ast");
const arvoreDerivacao = document.getElementById("arvore-derivacao");
const botaoExpandirTudo = document.getElementById("expandir-tudo");
const botaoRecolherTudo = document.getElementById("recolher-tudo");
const botaoArvoreAnterior = document.getElementById("arvore-anterior");
const botaoArvoreReproduzir = document.getElementById("arvore-reproduzir");
const botaoArvoreProximo = document.getElementById("arvore-proximo");
const explicacaoArvore = document.getElementById("arvore-explicacao");
const detalhesNo = document.getElementById("detalhes-no");

const FORMAS = { comando: "■", operacao: "◆", valor: "●" };

let codigoAtual = "";
let nosAst = [];              // nós da AST em ordem de construção (id)
let elementoDoNo = new Map(); // id -> botão do nó na tela
let passoArvore = -1;
let temporizadorArvore = null;
let derivacaoAtual = null;
let derivacaoDesenhada = false;

// Categoria visual do nó: a forma (■ ◆ ●) diz o mesmo que a cor, para não depender só dela.
function categoria(tipo) {
  if (tipo === "PROGRAMA" || tipo === "ATRIBUICAO") return "comando";
  if (tipo === "IDENTIFICADOR" || tipo.startsWith("LITERAL")) return "valor";
  return "operacao";
}

function mostrarResultadoSintatico(texto, tipo) {
  resultadoSintatico.textContent = texto;
  resultadoSintatico.className = tipo;
  resultadoSintatico.hidden = false;
}

function limparArvore() {
  pararArvore();
  resultadoSintatico.hidden = true;
  secaoArvore.hidden = true;
  secaoErrosSintaticos.hidden = true;
  detalhesNo.hidden = true;
  arvoreAst.replaceChildren();
  arvoreDerivacao.replaceChildren();
  nosAst = [];
  elementoDoNo = new Map();
  passoArvore = -1;
  derivacaoAtual = null;
  derivacaoDesenhada = false;
  selecionarAba("ast");
}

function mostrarAnaliseSintatica(codigo, dados) {
  codigoAtual = codigo;
  const errosSintaticos = dados.erros_sintaticos || [];
  const ignoradas = dados.linhas_ignoradas || [];

  if (errosSintaticos.length > 0) {
    mostrarResultadoSintatico(
      `A análise sintática encontrou ${errosSintaticos.length} erro(s). Veja os detalhes abaixo.`, "aviso");
  } else if (dados.ast) {
    let texto = `Análise sintática concluída: ${dados.ast.filhos.length} comando(s) reconhecido(s).`;
    if (ignoradas.length > 0) {
      texto += ` Linha(s) não analisada(s) por ter(em) erro léxico: ${ignoradas.join(", ")}.`;
    }
    mostrarResultadoSintatico(texto, ignoradas.length > 0 ? "aviso" : "sucesso");
  }

  listaErrosSintaticos.replaceChildren(...errosSintaticos.map(itemErroSintatico));
  secaoErrosSintaticos.hidden = errosSintaticos.length === 0;
  marcarErrosSintaticosNoCodigo(errosSintaticos);

  if (dados.ast) {
    derivacaoAtual = dados.derivacao;
    desenharAst(dados.ast);
    contagemArvores.textContent =
      `AST: ${contarNos(dados.ast)} nós · Árvore de derivação: ${contarNos(dados.derivacao)} nós`;
    secaoArvore.hidden = false;
    irParaPassoArvore(-1);
  }
}

function itemErroSintatico(erro) {
  const item = criar("li");
  item.appendChild(criar("span", erro.mensagem, "mensagem-erro"));
  const detalhes = criar("div", undefined, "detalhes-erro");
  const esperado = erro.esperado.length > 0 ? erro.esperado.join(", ") : "—";
  detalhes.appendChild(criar("div", `Encontrado: ${erro.encontrado} · Esperado: ${esperado}`));
  const regra = criar("div", "Regra da gramática: ");
  regra.appendChild(criar("code", erro.regra));
  detalhes.appendChild(regra);
  item.appendChild(detalhes);
  return item;
}

// Sublinha no código o token onde o parser parou; se o erro for no fim do código, põe uma marca no fim.
function marcarErrosSintaticosNoCodigo(erros) {
  for (const erro of erros) {
    const span = codigoColorido.querySelector(`.tk[data-linha="${erro.linha}"][data-coluna="${erro.coluna}"]`);
    if (span) {
      span.classList.add("tk-erro-sintatico");
      span.title = erro.mensagem;
    } else {
      const marca = criar("span", " ◀ aqui", "marca-erro-sintatico");
      marca.title = erro.mensagem;
      codigoColorido.appendChild(marca);
    }
  }
}

function contarNos(raiz) {
  let total = 0;
  const pilha = [raiz];
  while (pilha.length > 0) {
    const no = pilha.pop();
    total += 1;
    if (no.filhos) pilha.push(...no.filhos);
  }
  return total;
}

// ---------- Desenho das árvores (listas aninhadas, expansíveis) ----------

function itemDaArvore(rotulo, filhos, aoSelecionar) {
  const item = criar("li");
  item.setAttribute("role", "treeitem");
  const linha = criar("div", undefined, "linha-no");
  if (filhos.length > 0) {
    const alternar = criar("button", "▾", "alternar");
    alternar.type = "button";
    alternar.setAttribute("aria-label", "Recolher ou expandir");
    alternar.addEventListener("click", () => definirRecolhido(item, !item.classList.contains("recolhido")));
    item.setAttribute("aria-expanded", "true");
    linha.appendChild(alternar);
  } else {
    linha.appendChild(criar("span", "", "sem-alternar"));
  }
  rotulo.addEventListener("click", aoSelecionar);
  linha.appendChild(rotulo);
  item.appendChild(linha);
  if (filhos.length > 0) {
    const grupo = criar("ul");
    grupo.setAttribute("role", "group");
    grupo.append(...filhos);
    item.appendChild(grupo);
  }
  return item;
}

function definirRecolhido(item, recolhido) {
  if (!item.hasAttribute("aria-expanded")) return;
  item.classList.toggle("recolhido", recolhido);
  item.setAttribute("aria-expanded", String(!recolhido));
  item.querySelector(":scope > .linha-no > .alternar").textContent = recolhido ? "▸" : "▾";
}

function desenharAst(ast) {
  nosAst = [];
  elementoDoNo = new Map();

  function desenhar(no) {
    nosAst.push(no);
    const cat = categoria(no.tipo);
    const rotulo = criar("button", undefined, `rotulo-no cat-${cat}`);
    rotulo.type = "button";
    rotulo.dataset.id = no.id;
    rotulo.dataset.tipo = no.tipo;
    rotulo.appendChild(criar("span", FORMAS[cat], "forma"));
    rotulo.appendChild(criar("span", ` ${no.rotulo} `, "texto-no"));
    rotulo.appendChild(criar("small", no.tipo, "tipo-no"));
    rotulo.appendChild(criar("code", no.regra, "regra-no"));
    elementoDoNo.set(no.id, rotulo);
    const filhos = no.filhos.map(desenhar);
    return itemDaArvore(rotulo, filhos, () => {
      pararArvore();
      selecionar(rotulo, no.rotulo, no.regra, no);
    });
  }

  arvoreAst.replaceChildren(desenhar(ast));
  nosAst.sort((a, b) => a.id - b.id);
}

// Extensão (início e fim) de um nó da derivação, a partir das folhas (tokens) que ele cobre.
function extensao(no) {
  if (no.tipo === "TERMINAL") {
    const tamanho = Math.max(Array.from(no.lexema).length, 1);
    return { linha: no.linha, coluna: no.coluna, linhaFim: no.linha, colunaFim: no.coluna + tamanho - 1 };
  }
  const partes = no.filhos.map(extensao).filter(Boolean);
  if (partes.length === 0) return null;
  const primeiro = partes[0];
  const ultimo = partes[partes.length - 1];
  return { linha: primeiro.linha, coluna: primeiro.coluna, linhaFim: ultimo.linhaFim, colunaFim: ultimo.colunaFim };
}

function desenharDerivacao(raiz) {
  function desenhar(no) {
    const ehTerminal = no.tipo === "TERMINAL";
    const rotulo = criar("button", undefined, `rotulo-no ${ehTerminal ? "terminal" : "nao-terminal"}`);
    rotulo.type = "button";
    rotulo.dataset.simbolo = no.simbolo;
    if (ehTerminal) {
      const lexema = no.simbolo === "NOVA_LINHA" ? (no.lexema === "" ? "(fim)" : "↵") : no.lexema;
      rotulo.appendChild(criar("small", no.simbolo, "tipo-no"));
      rotulo.appendChild(criar("code", ` ${lexema}`, "lexema-no"));
    } else {
      rotulo.appendChild(criar("span", no.simbolo, "texto-no"));
    }
    const filhos = ehTerminal ? [] : no.filhos.map(desenhar);
    return itemDaArvore(rotulo, filhos, () => {
      const nome = ehTerminal
        ? `Terminal ${no.simbolo}: ${no.lexema === "" ? "(fim do código)" : no.lexema}`
        : `Não terminal: ${no.simbolo}`;
      const regra = ehTerminal ? "(terminal: um token do scanner, não tem regra)" : no.regra;
      selecionar(rotulo, nome, regra, extensao(no));
    });
  }
  arvoreDerivacao.replaceChildren(desenhar(raiz));
  derivacaoDesenhada = true;
}

// ---------- Seleção de nó: destaca o trecho no código ----------

function antes(l1, c1, l2, c2) {
  return l1 < l2 || (l1 === l2 && c1 <= c2);
}

function destacarNoCodigo(faixa) {
  codigoColorido.querySelectorAll(".no-selecionado").forEach((el) => el.classList.remove("no-selecionado"));
  if (!faixa) return;
  codigoColorido.querySelectorAll(".tk[data-linha]").forEach((span) => {
    const linha = Number(span.dataset.linha);
    const coluna = Number(span.dataset.coluna);
    if (antes(faixa.linha, faixa.coluna, linha, coluna) && antes(linha, coluna, faixa.linhaFim, faixa.colunaFim)) {
      span.classList.add("no-selecionado");
    }
  });
}

function trechoDoCodigo(faixa) {
  if (!faixa) return "";
  const linhas = codigoAtual.split("\n").map((l) => Array.from(l.replace(/\r$/, "")));
  const partes = [];
  for (let l = faixa.linha; l <= faixa.linhaFim; l++) {
    const caracteres = linhas[l - 1] || [];
    const inicio = l === faixa.linha ? faixa.coluna - 1 : 0;
    const fim = l === faixa.linhaFim ? faixa.colunaFim : caracteres.length;
    partes.push(caracteres.slice(inicio, fim).join(""));
  }
  return partes.join("\n");
}

function resumir(texto, limite = 60) {
  const caracteres = Array.from(texto.replace(/\s+/g, " ").trim());
  return caracteres.length > limite ? caracteres.slice(0, limite - 1).join("") + "…" : caracteres.join("");
}

function selecionar(rotulo, nome, regra, faixa) {
  document.querySelectorAll(".rotulo-no.selecionado").forEach((el) => el.classList.remove("selecionado"));
  rotulo.classList.add("selecionado");
  destacarNoCodigo(faixa);
  document.getElementById("detalhe-rotulo").textContent = nome;
  document.getElementById("detalhe-regra").textContent = regra;
  document.getElementById("detalhe-posicao").textContent = faixa
    ? `linha ${faixa.linha}, coluna ${faixa.coluna} até linha ${faixa.linhaFim}, coluna ${faixa.colunaFim}`
    : "—";
  document.getElementById("detalhe-trecho").textContent = trechoDoCodigo(faixa);
  detalhesNo.hidden = false;
}

// ---------- Abas, expandir e recolher ----------

function selecionarAba(nome) {
  const ehAst = nome === "ast";
  abaAst.classList.toggle("ativa", ehAst);
  abaDerivacao.classList.toggle("ativa", !ehAst);
  abaAst.setAttribute("aria-selected", String(ehAst));
  abaDerivacao.setAttribute("aria-selected", String(!ehAst));
  painelAst.hidden = !ehAst;
  painelDerivacao.hidden = ehAst;
  // A derivação pode ser grande: só é desenhada quando o aluno abre a aba.
  if (!ehAst && derivacaoAtual && !derivacaoDesenhada) desenharDerivacao(derivacaoAtual);
}

abaAst.addEventListener("click", () => selecionarAba("ast"));
abaDerivacao.addEventListener("click", () => {
  pararArvore();
  selecionarAba("derivacao");
});

function arvoreVisivel() {
  return painelAst.hidden ? arvoreDerivacao : arvoreAst;
}

botaoExpandirTudo.addEventListener("click", () => {
  arvoreVisivel().querySelectorAll("li[aria-expanded]").forEach((item) => definirRecolhido(item, false));
});
botaoRecolherTudo.addEventListener("click", () => {
  // A raiz continua aberta, para o aluno ver o primeiro nível.
  arvoreVisivel().querySelectorAll("li[aria-expanded]").forEach((item, i) => definirRecolhido(item, i !== 0));
});

// ---------- Construção da AST passo a passo ----------

function irParaPassoArvore(indice) {
  passoArvore = indice;
  const total = nosAst.length;
  for (const no of nosAst) {
    const rotulo = elementoDoNo.get(no.id);
    rotulo.classList.toggle("pendente", indice >= 0 && no.id > indice + 1);
    rotulo.classList.toggle("no-atual", indice >= 0 && no.id === indice + 1);
  }

  if (indice < 0) {
    explicacaoArvore.textContent =
      `A AST tem ${total} nó(s). Clique em "Próximo" para ver a ordem em que o parser os constrói: ` +
      "primeiro as folhas (valores e nomes), depois as operações que as juntam e, por último, o programa.";
    destacarNoCodigo(null);
  } else {
    const no = nosAst[indice];
    explicacaoArvore.textContent =
      `Passo ${indice + 1} de ${total}: o parser reconheceu ${no.rotulo} pela regra ${no.regra}, ` +
      `a partir do trecho "${resumir(trechoDoCodigo(no))}".`;
    // Garante que o nó atual esteja visível, abrindo os pais recolhidos.
    const itemAtual = elementoDoNo.get(no.id).closest("li");
    for (let item = itemAtual.parentElement.closest("li"); item; item = item.parentElement.closest("li")) {
      definirRecolhido(item, false);
    }
    destacarNoCodigo(no);
  }

  botaoArvoreAnterior.disabled = indice < 0;
  botaoArvoreProximo.disabled = indice >= total - 1;
  botaoArvoreReproduzir.disabled = total === 0;
}

function pararArvore() {
  clearInterval(temporizadorArvore);
  temporizadorArvore = null;
  botaoArvoreReproduzir.textContent = "▶ Reproduzir";
}

botaoArvoreAnterior.addEventListener("click", () => {
  pararArvore();
  irParaPassoArvore(passoArvore - 1);
});

botaoArvoreProximo.addEventListener("click", () => {
  pararArvore();
  irParaPassoArvore(passoArvore + 1);
});

botaoArvoreReproduzir.addEventListener("click", () => {
  if (temporizadorArvore) {
    pararArvore();
    return;
  }
  if (passoArvore >= nosAst.length - 1) irParaPassoArvore(-1); // chegou ao fim: recomeça
  botaoArvoreReproduzir.textContent = "⏸ Pausar";
  temporizadorArvore = setInterval(() => {
    irParaPassoArvore(passoArvore + 1);
    if (passoArvore >= nosAst.length - 1) pararArvore();
  }, INTERVALO_REPRODUCAO_MS);
});
