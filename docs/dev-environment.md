# Ambiente de desenvolvimento e painel local

Este documento descreve o ambiente global de teste: um comando sobe a pilha,
migra e popula o banco, inicia o emulador, instala o app de debug e expõe as
portas usadas pelo app e pelo painel.

## Comando único

```bash
make test-env        # pilha + banco + emulador + app
make studio          # painel em http://127.0.0.1:8099
make test-env-status # o que está no ar
make test-env-down   # encerra pilha e emulador
```

## Emulador realista

O perfil padrão `callme_api36` é 320×640 e serve para ver o app caber em telas
pequenas. Para validar como num aparelho de verdade use o AVD de 1080×2400:

```bash
DIARY_AVD=Medium_Phone_API_36 DIARY_WINDOW=1 make test-env
```

| Variável | Padrão | Para que serve |
|---|---|---|
| `DIARY_AVD` | `callme_api36` | nome do AVD |
| `DIARY_WINDOW` | `0` | `1` abre a janela do emulador |
| `DIARY_AVD_MEMORY` | `3072` | RAM do convidado; 1080p não sobe com 2 GB |
| `DIARY_AVD_GPU` | `swiftshader_indirect` | renderização por software |

O script passa `-skip-adb-auth` (uma imagem recém-criada pediria autorização de
adb, que a automação não consegue aceitar) e aplica `adb reverse` em **8001,
8010 e 5556**. A porta 5556 é o provedor OIDC: sem ela o navegador abre o login e
falha com `ERR_CONNECTION_REFUSED`.

Login: `demo@example.com` / `password`. Na primeira vez o Chrome mostra o
assistente inicial (escolha "Use without an account") e depois a tela de
consentimento do Dex.

### Tamanho da tela e automação

`adb exec-out screencap` devolve a imagem no tamanho físico, mas ferramentas de
visualização reduzem a imagem. Para tocar em um elemento use os limites reais:

```bash
adb shell uiautomator dump /sdcard/ui.xml
adb shell cat /sdcard/ui.xml | tr '>' '>\n' | grep -oE 'text="[^"]*"[^>]*bounds="\[[0-9,]+\]\[[0-9,]+\]"'
```

Se o host estiver sem memória o convidado dispara ANR em `systemui` e o app
"não conclui a inicialização". Dê RAM ao AVD e evite rodar build e emulador ao
mesmo tempo.

`make test-env` executa, nesta ordem:

1. cria `.env` a partir de `.env.example` quando necessário e gera chaves locais;
2. sobe os pods com `docker compose`;
3. espera o PostgreSQL, roda `alembic upgrade head` e o seed de planos;
4. inicia o AVD `callme_api36` sem janela quando não há dispositivo ligado;
5. compila o APK de debug, instala, aplica `adb reverse` em `8001`/`8010` e
   `adb forward` em `5557` e abre o app.

Login do Dex: `demo@example.com` / `password`. Na primeira vez o Chrome mostra o
assistente inicial; escolha "Use without an account" e depois conceda o acesso.

## Painel (studio)

`ops/studio` é uma ferramenta de desenvolvimento, não um pod. Ela nunca é
implantada e escuta apenas em loopback.

| Aba | O que faz |
|---|---|
| Mapa | arrasta os nós; "Salvar layout" grava as posições no aparelho |
| Pessoas | renomeia e troca o avatar de um cadastro |
| Diário | lista registros, data do acontecimento e presença de áudio |
| Eventos | lista acontecimentos com precisão de data e estado de revisão |
| Stack | estado dos serviços e leitura das tabelas do banco de desenvolvimento |
| Idiomas | arquivos de tradução e chaves pendentes |

O painel fala com o app pelo *bridge* de debug (`DevBridge`), que existe apenas
em builds `debug` e só aceita conexões de `127.0.0.1`. Ele expõe três rotas de
escrita deliberadamente pequenas: renomear/avatar, fixar posição e limpar layout.
Registros, versões e mídias continuam somente leitura: o painel organiza o mapa,
não reescreve a história.

Posições são normalizadas pelo raio do anel (-1..1). A tabela `map_pins` guarda
`entityId`, `x` e `y`; sem linha, o nó volta para o anel calculado. Por isso o
arranjo feito no painel vale para qualquer tamanho de tela.

## MCP

`.vscode/mcp.json` registra o servidor `diaryteller-studio` (stdio, iniciado por
`poetry run python -m ops.studio.mcp_server`). Ferramentas disponíveis:

- `app_state`, `move_map_node`, `reset_map_layout`, `rename_entity`;
- `stack_status`, `backend_tables_tool`, `translation_status`, `run_checks`.

Requisições de teste rápido:

```bash
curl -s http://127.0.0.1:5557/health
curl -s http://127.0.0.1:5557/state | head -c 400
curl -s http://127.0.0.1:8099/api/status
```

## Limites

- O bridge não lê mídias nem segredos; apenas estado e identificadores.
- O painel lê o banco de desenvolvimento em modo somente leitura e mascara
  colunas com `password`, `hash`, `token`, `secret` ou `key`.
- Nenhuma porta é publicada além de loopback ou do compose local.
