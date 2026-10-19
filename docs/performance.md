# Performance e carga

## Metas medidas (não garantias comerciais)

Cenários: 100 e depois 500 streams simultâneos com provedor sintético de latência
controlada, ambiente declarado, réplicas independentes. Registrar p50/p95/p99,
throughput, tempo até primeiro evento/token, event-loop lag, CPU, RSS, conexões
e taxa de erro.

## Evidência deste MVP

- `poetry run python scripts/load_streams.py --streams 100 --base-url ...` mede
  SSE com dados sintéticos e imprime percentis/erros.
- `poetry run python scripts/profile_memory.py` usa Memray em um cenário
  sintético de contexto + streaming, sem dados reais.
- `tests/load/README.md` define o procedimento com duas réplicas de conversation
  atrás de proxy sem buffering.

## Resultados medidos (2026-10-19, ambiente local)

Máquina Linux; Docker Compose; 2 réplicas de conversation (8010, 8012), identity
com 2 workers e pool 10+10; gerador fake sem latência externa; 500 requisições
disparadas simultaneamente contra duas réplicas.

| Cenário | Sucesso | p50 TTFB | p95 TTFB | p99 TTFB | Throughput | Erros |
|---|---|---|---|---|---|---|
| 100 streams, 1 réplica | 100/100 | 1,31 s | 1,90 s | 2,28 s | 41,9/s | 0 |
| 500 streams, 2 réplicas | 498/500 | 9,21 s | 13,52 s | 14,00 s | 32,3/s | 2 × 504 |

Gargalo observado: rajada de 500 streams satura o identity/PostgreSQL antes do
provedor sintético; timeouts de 5 s em `/internal/*` produzem `504
provider_timeout`. Mitigação aplicada: 2 workers e pool explícito. Mitigação
futura: mais réplicas de identity, revisão do orçamento de conexões e agrupamento
de autorização+reserva. Não foi feita otimização além do MVP.

## Memray

`poetry run python scripts/profile_memory.py` executou 50 operações sequenciais
com 50 registros sintéticos e streaming completo. `memray stats`:

- alocações: 13.426; total alocado: 10,36 MB;
- pico: 1,56 MB; maior alocação isolada: 1,05 MB;
- nenhum crescimento proporcional ao número de iterações, compatível com
  liberação de buffers após cada operação.

O arquivo `memray-stream.bin` é local e não é versionado.

## Limites de projeto

- Até 50 registros/50.000 caracteres de contexto por operação.
- Até 4 chamadas MCP por operação; nenhuma recursão.
- Até 16.000 tokens estimados por resposta (limite do identity).
- Áudio: 10 MiB e 120 s; TTS: 4.000 caracteres.
- Pool PostgreSQL calculado por réplicas × processos × pool; defaults baixos.
- Sem SQL por token; sem threads indiscriminadas; CPU-bound em worker/subprocesso.
- Fila de logs limitada; backpressure explícita em vez de fila ilimitada.

## Escala horizontal

Conversation e speech não guardam estado de sessão/contexto. Memory MCP é
stateless. Duas réplicas podem receber chamadas sem afinidade; a credencial de
contexto viaja na requisição. Revogação é aplicada via identity em até 15 s.

## Como reproduzir

```bash
docker compose -f ops/compose.yaml up -d --scale conversation=2
poetry run python scripts/load_streams.py --streams 100
poetry run python scripts/profile_memory.py
```

Registrar versão do commit, hardware, imagem, latência do provedor e datas.
