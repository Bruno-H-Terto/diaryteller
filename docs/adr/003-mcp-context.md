# ADR 003 — Contexto MCP vinculado à operação

- **Status:** aceito
- **Data:** 2026-10-19

## Contexto

O servidor MCP não pode consultar o celular atrás de NAT nem armazenar o diário.
O modelo não pode escolher usuário, sessão ou conjunto de registros.

## Decisão

O celular seleciona registros e os envia na requisição de IA. O serviço
`conversation` hospeda o cliente MCP; `memory_mcp` é um servidor MCP interno via
Streamable HTTP, sem estado de conteúdo.

Para cada operação, o cliente MCP gera um JWE de curta duração com audiência
`memory-mcp`, `operation_id`, permissões, usuário/sessão pseudonimizados, prazo e
o conjunto de registros. O campo interno `context_token` é injetado pelo código
do cliente em toda chamada; argumentos do modelo nunca o substituem. O servidor
valida assinatura/criptografia, audiência, prazo, permissão e IDs.

Ferramentas: `search_memories`, `get_memory`, `organize_ideas`, `build_timeline`
e `summarize_period`. `search_memories` é lexical determinística no MVP. As
demais usam LLM com schema validado, sem recursão de ferramentas.

## Consequências

- Não há cache ou banco de memórias no servidor.
- IDs fora do conjunto são rejeitados; cobertura e fontes são explícitas.
- Para mais histórico, o celular precisa enviar novo contexto.
- MCP público para terceiros exigiria autorização/consentimento próprios e fica
  fora do MVP.
