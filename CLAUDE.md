# Projeto MP — Coleta de Dados do Sistema Penal

## Objetivo
Automatizar a coleta de dados de múltiplas fontes sobre o sistema prisional
para subsidiar o trabalho do Ministério Público.

## Módulos
| Módulo | Fonte         | Tipo de acesso     | Status |
|--------|---------------|--------------------|--------|
| cnmp   | CNMP          | Login + scraping   | 🔧 em construção |
| bnmp   | BNMP          | API/scraping       | 📋 planejado |
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