# Registro de testes

Cada execução relevante fica registrada aqui, da mais recente para a mais antiga.

---

## 2026-10-21: Etapa 2B, tela principal, exemplos e testes de navegador

**Tipos:** implantação, interface, integração e ponta a ponta (Playwright/Chromium), além da
regressão do backend.

**Comandos:**

```bash
docker compose up --build -d
docker compose --profile testes run --rm testes   # navegador
docker compose run --rm backend pytest -v         # regressão do backend (Etapa 2A)
```

**Resultado:**

| Conjunto | Aprovados | Reprovados |
| --- | --- | --- |
| Navegador (`testes/`) | 38 | 0 |
| Backend (`backend/tests/`), regressão | 48 | 0 |
| **Total** | **86** | **0** |

| Arquivo | O que cobre | Testes |
| --- | --- | --- |
| `test_implantacao.py` | Página e arquivos estáticos servidos; `/api/saude` e `/api/analisar` acessíveis *pelo Nginx* (comunicação entre containers) | 4 |
| `test_interface.py` | Título e linguagem; campo, botão, resultado e seletor; fonte monoespaçada; ≥3 exemplos; digitar, editar, substituir; caracteres especiais; código preservado após analisar; cada exemplo carrega seu código; novo exemplo substitui o anterior e o código digitado; exemplo editável; opção vazia não apaga; selecionar exemplo não envia requisição | 17 |
| `test_ponta_a_ponta.py` | Digitar → analisar → mensagem com contagem; corpo enviado igual ao campo (acentos, emoji, tab); cada exemplo aceito pelo backend; editar exemplo e analisar; vazio/espaços orientam e **não** enviam requisição; validação não bloqueia entrada válida depois; erro 400 do backend exibido (limite de tamanho); falha de rede (mensagem, botão reabilitado, código preservado) e recuperação; erro 500 sem expor detalhes; botão desabilitado durante o envio; geração do print | 17 |

**Evidência:** `docs/evidencias/interface.png`, gerado pelo teste `test_gera_print_da_interface`.

**Falhas encontradas:** nenhuma nos testes. Um problema de ambiente: o download da imagem do Playwright
(921 MB comprimidos) foi interrompido uma vez e retomado, sem impacto no código.

**Mudança intencional:** a tela "Hello, World!" da Etapa 1 foi substituída pela tela principal. A
pendência registrada na Etapa 2A (a tela antiga chamando `/api/hello`) foi resolvida.

**Limitações / pendências:**
- os testes de navegador usam só o Chromium (Firefox e WebKit não foram testados);
- não há testes de acessibilidade nem de layout em telas pequenas;
- a lista de exemplos aparece em dois lugares (`frontend/site/exemplos.js` e `testes/test_interface.py`). Se um exemplo mudar, o teste falha e avisa.

---

## 2026-10-21: Etapa 2A, backend (`/api/analisar`, `/api/saude`, validações)

**Tipos:** unitário (`tests/test_validacao.py`) e endpoints (`tests/test_api.py`).

**Comando:**

```bash
docker compose run --rm backend pytest -v
```

**Resultado:** 48 aprovados, 0 reprovados.

| Arquivo | O que cobre | Testes |
| --- | --- | --- |
| `test_validacao.py` | Código aceito (válido, com erro intencional, caracteres especiais, limite exato), código preservado sem alteração, vazio/espaços, tipos errados, campo ausente, corpo que não é objeto, acima do limite | 26 |
| `test_api.py` | `/api/saude`; 200 com formato e contagem; caracteres especiais; 400 para sem corpo, JSON malformado, Content-Type errado, JSON que não é objeto, campo ausente, tipo errado, vazio, espaços e acima do limite; 405 no GET; 404; remoção de `/api/hello`; 500 genérico sem vazar detalhes | 22 |

**Verificação de implantação (manual, via `curl` pelo Nginx em `localhost:8080`):**
- `docker compose up --build -d`: o backend fica `healthy` e o frontend sobe depois dele;
- `GET /api/saude` → 200;
- `POST /api/analisar` com `idade = 17` → 200;
- `POST /api/analisar` com espaços → 400.

**Falhas encontradas:** nenhuma.

**Mudança intencional:** `/api/hello` (Etapa 1) foi removido. O teste `test_hello_da_etapa_1_foi_removido`
documenta essa decisão.

**Pendências:** a tela da Etapa 1 ainda chama `/api/hello`, que não existe mais. Ela será substituída
na Etapa 2B, junto com os testes de interface e ponta a ponta.
