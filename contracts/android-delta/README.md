# Contrato Android (referência)

Snapshot recebido em 2026-10-19 no pacote
`call-me-ai-backend-android-refatoracao.zip`. É um contrato **proposto** para as
adições do app Android, não substitui o OpenAPI dos serviços.

- `openapi.json`: OpenAPI 3.1 com 25 caminhos e 27 operações.
- `examples/`: payloads sintéticos e `response.sse`.
- `examples/schema-map.json`: mapeamento exemplo → schema.

Arquivos gerados/recebidos: isentos do limite de 200 linhas e não devem ser
editados à mão. `scripts/check_contract.py` valida a estrutura e os exemplos.
