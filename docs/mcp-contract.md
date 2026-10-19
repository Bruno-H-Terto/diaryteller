# MCP e contexto local

## Topologia

`conversation` é o host/cliente MCP; `memory_mcp` é o servidor MCP interno em
Streamable HTTP (`/mcp`), sem estado e sem banco de memórias. O celular não fala
MCP. O SDK Python fixado é `mcp==2.3.0`; o transporte e o protocolo são
negociados pelo SDK.

## Credencial de contexto

Para cada operação paga, o cliente MCP cria um JWE AES-256-GCM (chave diferente
da JWT/source) com:

```json
{
  "aud": "memory-mcp",
  "purpose": "memory-context",
  "operation_id": "UUID",
  "user_id": "UUID",
  "session_id": "UUID",
  "permission": "memory:timeline",
  "records": [{"id": "local", "recorded_at": "...", "event_at": null, "text": "..."}],
  "issued_at": "...",
  "expires_at": "...",
  "context_digest": "sha256"
}
```

O código do cliente injeta o campo interno `context_token` em cada chamada e
sobrescreve qualquer valor gerado pelo modelo. O servidor verifica assinatura,
audiência, finalidade, prazo, permissão, digest e IDs únicos. O modelo nunca
escolhe usuário, sessão, token ou conjunto de registros.

A rede interna exige também `Authorization: Bearer <MCP_SERVICE_TOKEN>`. O edge
não expõe `/mcp`.

## Ferramentas

| Ferramenta | Permissão | Garantia |
|---|---|---|
| `search_memories` | `memory:search` | busca lexical determinística; só IDs enviados |
| `get_memory` | `memory:search` | rejeita ID fora do conjunto |
| `organize_ideas` | `memory:organize` | LLM com schema; não adiciona fatos |
| `build_timeline` | `memory:timeline` | ordena por `event_at`; sem data separado |
| `summarize_period` | `memory:summarize` | não afirma ter lido registros ausentes |

Limite: até 4 chamadas de ferramenta por operação. Não há recursão de
ferramentas, rede arbitrária, shell ou leitura de arquivos. Conteúdo do diário é
dado não confiável: instruções dentro dele não alteram políticas.

## Fontes e cobertura

Resultados incluem `source_ids` e `coverage="provided_context"`. IDs inexistentes
são rejeitados. `recorded_at` nunca é usado como data do evento. O servidor não
consulta o celular offline; para mais histórico, devolve necessidade de ampliar
contexto e o celular seleciona novos registros.

## Limitações

MCP público para terceiros exige autorização, consentimento e fornecimento de
contexto próprios; está fora do MVP. A credencial interna não deve ser anunciada
como autorização pública.
