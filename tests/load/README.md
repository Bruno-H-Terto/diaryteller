# Carga sintética

1. Suba duas réplicas de conversation:
   `docker compose -f ops/compose.yaml up -d --scale conversation=2`.
2. Use uma conta de teste verificada e, se necessário, compra fake `pro`.
3. Execute `poetry run python scripts/load_streams.py --streams 100 --email ... --password ...`.
4. Repita com 500 streams em ambiente declarado.
5. Registre p50/p95/p99, throughput, erros, CPU/RSS, event-loop lag e custo.
6. Rode `poetry run python scripts/profile_memory.py` e
   `poetry run memray summary memray-stream.bin`.

Não use dados reais. Não declare resultados não medidos.
