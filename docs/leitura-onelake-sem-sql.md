# Lendo Warehouse e Lakehouse do Fabric via OneLake, sem SQL endpoint

Como ler tabelas do Fabric quando não há rota de rede até a porta do SQL
endpoint (comum em ambientes de desenvolvimento em sandbox, VMs restritas etc.),
mas há rota HTTPS normal. Documento pensado para reuso em qualquer projeto
Fabric, não é específico do `proj202607`.

## A ideia central

Todo dado estruturado do Fabric — de Warehouse **e** de Lakehouse — é gravado
fisicamente como tabelas Delta (Parquet + log de transação) dentro do OneLake,
o armazenamento único do workspace. O SQL endpoint do Warehouse é só *um dos
jeitos* de ler esse dado; o próprio Direct Lake do Power BI lê os arquivos
Delta direto, sem passar pelo motor SQL. Ou seja: se a porta do SQL (1433/TDS)
está bloqueada mas HTTPS (443) não está, ainda dá para ler o dado — só não
dá para usar `pyodbc`/T-SQL.

Isso vale tanto para Lakehouse (óbvio, é o caso de uso normal) quanto para
Warehouse (menos óbvio, mas funciona igual — testado e confirmado neste
projeto).

## Passo 1: descobrir o id do item (não o host de conexão SQL)

O caminho no OneLake usa o **id do item no Fabric** (um GUID), não o host de
conexão SQL (`xxxx.datawarehouse.fabric.microsoft.com`) nem o nome de
exibição. São coisas diferentes — um Warehouse tem os dois, e é fácil
confundir.

Se não tiver o id salvo em lugar nenhum, a Fabric REST API lista todos os
warehouses do workspace com os ids certos:

```bash
TOKEN=$(az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.fabric.microsoft.com/v1/workspaces/$FABRIC_WORKSPACE_ID/warehouses" | python3 -m json.tool
```

(Equivalente para Lakehouse: troque `/warehouses` por `/lakehouses`.) Requer
login prévio (`az login --service-principal -u $CLIENT_ID -p $CLIENT_SECRET
--tenant $TENANT_ID`) com um Service Principal que tenha acesso ao workspace.

**Cuidado**: itens renomeados no portal mantêm o id antigo, mas é fácil um
`.env` ficar com o id de um item que foi descontinuado/recriado com outro
nome, apontando pro lugar errado. Se a listagem por OneLake vier vazia onde
deveria ter dado, confirmar o id por aqui antes de suspeitar de outra causa.

## Passo 2: estrutura de pastas no OneLake

```
{workspace_id}/{item_id}/
├── Files/           # não estruturado — Lakehouse principalmente
├── Tables/
│   └── {schema}/    # normalmente "dbo"
│       └── {tabela}/    # uma pasta Delta por tabela (Parquet + _delta_log/)
└── Audit/           # só em Warehouse
```

O cliente é o mesmo `azure.storage.filedatalake.DataLakeServiceClient` já
usado para Lakehouse (`account_url="https://onelake.dfs.fabric.microsoft.com"`,
autenticado com Service Principal via `azure-identity`). A diferença é só o
prefixo do caminho: em vez de `{item_id}/Files/...`, usar `{item_id}/Tables/{schema}/...`.

## Passo 3: listar e ler tabelas

Funções prontas em `python/src/infra/warehouse.py`:

```python
from infra.warehouse import listar_tabelas_onelake, ler_tabela_gold_onelake

tabelas = listar_tabelas_onelake(warehouse_id="...")  # lista as tabelas físicas
df = ler_tabela_gold_onelake("fato_visita_1322", colunas=["ano", "periodo", "numero_de_presos_estudando"])
```

Por baixo, `ler_tabela_onelake` usa o pacote `deltalake` (`uv add deltalake
pyarrow`) apontando pro caminho `abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{item_id}/Tables/{schema}/{tabela}`,
autenticado com as mesmas credenciais de Service Principal (`CLIENT_ID`,
`CLIENT_SECRET`, `TENANT_ID`) via `storage_options`.

## Limitação conhecida: `columnMapping` / `deletionVectors`

Tabelas gravadas com esses recursos do protocolo Delta (comum em Warehouse do
Fabric, que os usa por padrão em alguns casos) dão erro
`DeltaProtocolError: The table has set these reader features: {...} but these
are not yet supported by the deltalake reader` — a versão do pacote Python
`deltalake` usada aqui (1.6.2) ainda não lê esses recursos. **Listar as
tabelas/pastas funciona sempre** (é só navegação de arquivo); é a leitura do
*conteúdo* Parquet que pode esbarrar nisso.

Não investigamos ainda uma solução definitiva. Alternativas para quando isso
bloquear:
- Conferir se uma versão mais nova do `deltalake` já suporta (o suporte a
  `deletionVectors`/`columnMapping` no delta-rs vem evoluindo).
- Ler via um motor que já suporta esses recursos (DuckDB com a extensão
  `delta`, ou Spark num notebook do próprio Fabric).
- Se houver rota de rede até o SQL endpoint (não é o caso deste projeto em
  ambiente de desenvolvimento, mas pode ser em produção/CI), usar
  `get_gold_engine`/`get_silver_engine` normalmente — não tem essa limitação.

## Por que isso importa

Sem essa rota, qualquer diagnóstico de dado (“esse número está certo?”, “por
que essa medida deu um valor absurdo?”) dependia de pedir para alguém com
acesso ao portal rodar uma consulta SQL e colar o resultado de volta — lento e
sujeito a mal-entendido sobre qual consulta rodar. Com acesso direto ao
OneLake, é possível investigar a fonte (inclusive o bronze, arquivo JSON por
arquivo) sem esse intermediário. Foi assim que se confirmou, neste projeto,
que um percentual "impossível" (6156%) num cartão do relatório não era bug de
DAX nem duplicata de dado — era a comparação entre duas seções do formulário
com cobertura de preenchimento muito desigual (4 de 188 instâncias com dado de
ocupação, 161 de 188 com dado de trabalho).
