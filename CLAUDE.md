# Projeto MP — Coleta de Dados do Sistema Penal

## Objetivo
Automatizar a coleta de dados de múltiplas fontes sobre o sistema prisional
para subsidiar o trabalho do Ministério Público.

## Módulos
| Módulo | Fonte         | Tipo de acesso     | Status |
|--------|---------------|--------------------|--------|
| cnmp   | CNMP          | Login + scraping   | 🔧 em construção |
| bnmp   | BNMP 2.0 (PDPJ/CNJ) | API REST + SSO Keycloak (usuário/senha + TOTP) | 🔧 em construção |
| esaj   | ESAJ          | Login + scraping   | 📋 planejado |
| sap    | SAP-SP        | Download direto    | 📋 planejado |

## Convenções

### Git: commits e push

Ao concluir cada tarefa lógica (uma alteração coesa e testada), fazer commit e push antes de seguir para a próxima tarefa. Não acumular mudanças não relacionadas em um único commit.

Seguir a convenção já usada no histórico do projeto para a mensagem: `Tipo: descrição`, com o tipo em inglês e inicial maiúscula, seguido de descrição em português iniciando com verbo no presente (terceira pessoa).

Tipos usados no projeto:

- `Feat`: nova funcionalidade
- `Fix`: correção de bug
- `Docs`: documentação (README, CLAUDE.md etc.)
- `Chore`: manutenção, limpeza, configuração
- `Refactor`: refatoração sem mudança de comportamento
- `Test`: testes

Exemplos: `Feat: adiciona filtro por status no app`, `Fix: corrige cálculo do prazo médio`.


### Stack e Ferramentas
- Gerenciador de pacotes: **uv** (nunca pip direto, nunca poetry)
- API: **FastAPI** com async/await
- Sempre criar/atualizar `pyproject.toml` em vez de `requirements.txt`
- Para rodar: `uv run python ...` ou `uv run fastapi dev`
- Credenciais sempre via variáveis de ambiente (.env)
- Logs em cada módulo com nível INFO por padrão
- Salvar PDFs brutos em downloads/<módulo>/
- Salvar dados extraídos em dados/<módulo>/

## Estrutura de pastas
```
proj202607/
├── R/                        # pacote R (análise e relatórios)
├── python/                   # módulos Python (coleta de dados)
│   ├── pyproject.toml
│   ├── src/
│   │   ├── infra/            # conexões Lakehouse e Warehouse
│   │   └── modulos/          # cnmp, bnmp, esaj, sap
│   └── downloads/            # PDFs e JSONs brutos (gitignore)
└── dados/                    # dados estruturados exportados
```

## Variáveis de ambiente
Ver .env.example para referência.

## Microsoft Fabric
Arquitetura: **Lakehouse** para arquivos brutos + **Warehouse** para tabelas estruturadas.

| O que guardar | Onde | Como escrever do Python |
|---|---|---|
| PDFs, JSONs brutos | Lakehouse (Files) | `azure-storage-file-datalake` |
| Tabelas estruturadas | Warehouse | `pyodbc` + `ClientSecretCredential` |

- Lakehouse sugerido: `mp_raw` — seção Files organizada por módulo (`cnmp/pdfs/`, `cnmp/json/`, etc.)
- Warehouse sugerido: `mp_warehouse`
- Autenticação local: `AzureCliCredential` (az login)
- Autenticação produção: `ClientSecretCredential` via Service Principal
- Credenciais em: `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`
- Módulos de conexão prontos em: `python/src/infra/lakehouse.py` e `python/src/infra/warehouse.py`

### Tipos T-SQL (Fabric usa T-SQL, não PostgreSQL)
- Texto longo: `VARCHAR(MAX)` — suportado, até 16 MB por célula
- Booleano: `BIT` (0/1) — não existe BOOLEAN nativo
- Auto-incremento: `INT IDENTITY(1,1)` — não existe SERIAL
- Não existe TEXT — usar `VARCHAR(MAX)`


# Novas orientações (temporárias)

- Gostaria de criar um pacote python, separado deste projeto. O nome do pacote será algo como mpexecuta(provisório). Este projeto, como mostrado acima, irá conter módulos e submódulos como a coleta das informacoes das unidades prisionais da resolução 277 do CNMP, do esaj, do SEEU, bnmp e  SAP (secretaria de administracao penitenciária).

## Módulo CNMP:

### Coleta estruturada
- Vamos inspecionar a api do cnmp com cuidado para montarmos um schema no lakehouse bem montado. Creio que devemos tomar cuidado porque existe mais de um formulário. Esse schema conterá tabelas bem estruturadas sobre as visitas às unidades prisionais. Possivelmente, teremos de montar um modelo semântico também.

- Os secredos serão obtidos, uma vez implementado o módulo, do vault via notebook. Os nomes no vault são CNMP-USUARIO E CNMP-SENHA. Esta é a url do vault: KVUri = f"https://KV-Jurimetria.vault.azure.net"

## Módulo BNMP

Coleta do Banco Nacional de Monitoramento de Prisões (BNMP 2.0, PDPJ/CNJ), a partir da mesma API REST que o frontend `bnmp-frontend` consome.

### Autenticação
- SSO do PJe (Keycloak), fluxo authorization_code sem PKCE: `https://sso.cloud.pje.jus.br/auth/realms/pje/protocol/openid-connect`, client_id `bnmp-frontend`, redirect_uri `https://bnmp.pdpj.jus.br/pagina-inicial`.
- Login browser-less em `python/src/modulos/bnmp/auth.py`: usuário e senha no formulário do Keycloak, código TOTP gerado com `pyotp`, captura do `code` no redirect e troca por tokens.
- access_token e refresh_token expiram juntos em ~8h; em coletas longas o cliente refaz o login completo sozinho.
- Segredos no Key Vault `KV-Jurimetria`: `BNMP-USUARIO`, `BNMP-SENHA`, `BNMP-OTP-SECRET`. Local: `BNMP_USER`, `BNMP_PASSWORD`, `BNMP_OTP_SECRET`, `BNMP_ORGAO_ATIVO` no .env.
- O 2º fator precisa estar **cadastrado** na conta. Se o SSO responder com a required action `CONFIGURE_TOTP`, ele gera um segredo novo a cada login e nenhum segredo salvo funciona — é preciso concluir o cadastro uma vez pelo navegador e guardar o segredo base32 exibido.

### API
Base `https://bnmp.pdpj.jus.br/v2/api`, Bearer token e header `x-orgao-ativo` (39 = MPSP). Respostas paginadas no padrão Spring (`content`, `totalElements`, `totalPages`, `last`).

| Endpoint | Conteúdo |
|---|---|
| `POST /pessoas/filter` | pessoas com registro no BNMP (~5,7 milhões no filtro nacional) |
| `POST /pecas/light-filter` | mandados de prisão, contramandados, alvarás, guias |
| `POST /eventos/light-filter` | eventos de prisão, soltura, internação |
| `GET /dominios` | ~90 listas de referência (status, tipos de peça, motivos, UFs...) |
| `GET /status-pessoas` | status possíveis de pessoa |
| `GET /usuario-logado/contexto-sessao` | órgão ativo e permissões da sessão |

Os corpos de filtro são construídos em `python/src/modulos/bnmp/filtros.py`: objeto vazio `{}` significa "sem filtro" para o backend, e cada parâmetro preenchido vira `{"id": valor}`.

### Camadas
- Bronze (`bnmp/json/` no `mp_bronze`): uma página por arquivo (`{recurso}/{consulta}/pagina_NNNNNN.json`) mais um `_manifesto.json` com o progresso. Coleta retomável: reexecutar pula as páginas já gravadas.
- Silver (`mp_silver`): `bnmp_dominio`, `bnmp_pessoa_carga` (tudo o que foi coletado) e `bnmp_pessoa` (deduplicada por `pessoa_id_api`, é a tabela de uso). Carga via CSV em partes no staging + `COPY INTO`.

### Particionamento da coleta
Quebrar por UF (e, em UF grande, por status) em vez de uma consulta nacional única: a paginação por offset degrada em milhões de registros, o recorte isola falhas e permite retomada mais granular. Como a paginação percorre dados vivos, a mesma pessoa pode cair em duas páginas — daí a deduplicação na silver.

O script `python/scripts/explorar_api_bnmp.py` mede o tamanho de página aceito, o efeito da ordenação e o limite de paginação profunda, além de sondar quais filtros de peças e eventos retornam dados (o HAR do frontend só trouxe respostas vazias desses dois).