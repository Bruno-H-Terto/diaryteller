# ADR 004 — Processamento efêmero e limites rígidos

- **Status:** aceito
- **Data:** 2026-10-19

## Contexto

Python mantém objetos em memória por tempo indeterminado e bibliotecas podem
gravar uploads em disco. Guardar conteúdo pessoal em logs, filas ou dumps
ampliaria o risco sem necessidade de produto.

## Decisão

- Conteúdo existe apenas em memória durante a requisição, com limites por
  operação: JSON 256 KiB, mensagem 8.000 caracteres, 50 registros, 50.000
  caracteres de contexto, áudio 10 MiB/120 s e TTS 4.000 caracteres.
- Upload binário é lido em streaming com corte no limite. Adaptadores que exigem
  arquivo usam área temporária limitada, removida em `finally`.
- `Cache-Control: no-store`; sem captura de corpo em proxy/APM/SDK; erros
  sanitizados.
- Logs vão para Mongo com allowlist, buffer limitado, descarte contado e TTL.
  Falha do Mongo não bloqueia o processamento.
- Recibos de operação guardam metadados e digest HMAC do payload, nunca o texto.
- Não há fila durável de conteúdo entre requisição e provedor.

## Consequências

- Não é possível reprocessar uma resposta sem novo envio e nova chave.
- Swap, core dump e memória do provedor estão fora do controle da aplicação e
  precisam de configuração de ambiente.
- Cancelamento é cooperativo e o provedor pode ter cobrado a chamada.
- Backups contêm apenas dados administrativos.
