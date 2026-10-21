# Registro de testes

Cada execução relevante fica registrada aqui, da mais recente para a mais antiga.

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
