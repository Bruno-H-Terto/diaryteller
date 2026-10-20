# Documentação

Este índice descreve o backend do diário local-first. O celular guarda o diário;
o servidor autentica, autoriza, controla assinatura e consumo, processa conteúdo
apenas durante a requisição e devolve resultados.

## Produto e decisões

- [Escopo do MVP](scope.md)
- [Arquitetura e fronteiras](architecture.md)
- [Dependências e versões](dependencies.md)
- [Política de dados e retenção](data-policy.md)
- [Modelo de ameaças](threat-model.md)
- [Controle de custos](cost-controls.md)

## Contratos

- [Contrato mobile e exemplos](mobile-contract.md)
- [Streaming e idempotência](streaming-contract.md)
- [MCP e contexto local](mcp-contract.md)
- [Endpoints de identidade](endpoints-auth.md)
- [Endpoints de IA e voz](endpoints-ai.md)
- [Endpoints de operações e assinatura](endpoints-operations.md)
- [Cobrança e entitlements](billing.md)

## Operação

- [Operação, retenção e backups](operations.md)
- [Testes e critérios de qualidade](testing.md)
- [Performance e carga](performance.md)
- [Ambiente de desenvolvimento e painel](dev-environment.md)

## App Android

- [Traduções por arquivo YAML](i18n.md)
- [Design system](design-system.md)

## Decisões arquiteturais

- [ADR 001 — dados locais](adr/001-local-data.md)
- [ADR 002 — modelo de sessão](adr/002-session-model.md)
- [ADR 003 — contexto MCP](adr/003-mcp-context.md)
- [ADR 004 — processamento efêmero](adr/004-ephemeral-processing.md)

## Limites conhecidos

- Não há aplicativo mobile, site público, sincronização de diário, mídia
  remota, busca semântica no servidor, clonagem de voz, vídeo, identificação de
  falantes, chamadas em tempo real nem MCP público para terceiros.
- Os prazos de retenção são decisões de engenharia, não conclusões jurídicas.
- Metadados administrativos também podem ser dados pessoais.
