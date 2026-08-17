# Aprendizados — construção de relatórios Power BI no Microsoft Fabric via PBIR

Registro do que aprendemos construindo o relatório `res_277_v2` (projeto `proj202607`),
editando o item Report do Fabric diretamente como arquivos (formato PBIR), sem passar
pelo Power BI Desktop. Documento pensado para reuso em outros projetos — não é
específico da Resolução 277/CNMP, só usa esse relatório como exemplo.

## Contexto: por que editar arquivo em vez de usar o Desktop

O Fabric, desde 2024/2025, guarda cada relatório como uma pasta de arquivos JSON
(formato PBIR — Power BI Enhanced Report Format), sincronizada via git integration.
Isso torna possível criar/editar páginas, visuais e temas por código, sem clicar no
Power BI Desktop. O modelo semântico (TMDL) já era editável como texto há mais tempo.

Limitação real, não teórica: quem edita esses arquivos **não tem como rodar ou
renderizar o relatório**. Todo JSON e DAX é escrito "às cegas" — só é validado por:

1. Sintaxe (JSON bem formado — sempre rodar `json.load` antes de commitar).
2. Semântica contra documentação real (nunca supor formato de chave por analogia).
3. Confirmação visual do usuário depois de um "Update" no workspace do Fabric.

Isso muda o processo de trabalho: compensa ir incremental (uma medida, um visual, um
ajuste por vez, cada um commitado separadamente) porque quando algo quebra, isolar a
causa é rápido — o commit anterior mostra exatamente o que mudou.

## Fontes que funcionaram (documentação oficial é incompleta)

A documentação oficial da Microsoft sobre o schema de `visual.json` é fragmentada —
o schema principal só referencia um schema embutido que não é servido publicamente.
As fontes que realmente deram a estrutura certa:

- [Report definition - Microsoft Fabric REST APIs](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/report-definition) — estrutura de pastas do PBIR, payload de criação via API, exemplo real de `report.json`/`page.json`/`visual.json`.
- [Create a Power BI report in enhanced report format](https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format) — contexto sobre o PBIR ser formato público/documentado.
- Repositório da comunidade `data-goblin/power-bi-agentic-development` (skill `pbip/skills/pbir-format`, arquivos `references/visual-json.md`, `references/report.md`, `references/enumerations.md`) — a fonte mais prática, feita especificamente para agentes de IA editarem PBIR. Tem a lista de `visualType` válidos e os *gotchas* de sintaxe (ver abaixo). Buscar o conteúdo raw no GitHub (`raw.githubusercontent.com/.../references/...md`), não a página renderizada.
- [Automate Git integration by using APIs](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-automation) e [Automate git integration with a service principal in Azure DevOps](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/automate-git-integration-with-service-principal) — API de Git integration do workspace (não usada neste projeto por decisão própria, ver seção final, mas documentação sólida se for necessário no futuro).

## Estrutura de um item Report (PBIR)

```
NomeDoRelatorio.Report/
├── .platform                    # displayName + logicalId (GUID) do item no Fabric
├── definition.pbir              # referência ao modelo semântico (datasetReference.byPath)
├── definition/
│   ├── report.json              # tema, configurações gerais, visuais customizados públicos
│   ├── version.json
│   └── pages/
│       ├── pages.json           # ordem das páginas e página ativa
│       └── {pageId}/
│           ├── page.json        # displayName, altura/largura da página
│           └── visuals/
│               └── {visualId}/
│                   └── visual.json   # tipo, posição, query, formatação de UM visual
└── StaticResources/
    └── RegisteredResources/     # temas customizados e imagens registrados
```

`{pageId}` e `{visualId}` são strings arbitrárias (na prática, hex de ~20 caracteres);
o nome da pasta precisa bater com o campo `"name"` dentro do JSON correspondente.

Para **duplicar** um relatório (trabalhar numa cópia sem mexer no original): copiar a
pasta inteira, e depois obrigatoriamente trocar `logicalId` no `.platform` (gerar um
GUID novo) e `displayName` — senão o Fabric entende que é o mesmo item.

### `definition.pbir`: referência ao modelo semântico

```json
{
  "datasetReference": {
    "byPath": { "path": "../NomeDoModelo.SemanticModel" }
  }
}
```

O caminho é relativo à pasta do próprio relatório. Se o relatório ou o modelo forem
movidos de pasta (reorganização dentro do workspace), esse caminho quebra
silenciosamente — o relatório carrega mas fica sem dataset. Conferir sempre que mover
pastas.

## Gotchas de `visual.json` (os que realmente nos morderam)

**Título do visual: `visualContainerObjects`, não `objects`.**
`objects` é para formatação específica do *tipo* de visual (eixo, legenda, cor de
dado). `visualContainerObjects` é para o *contêiner* — título, borda, fundo, sombra —
e vale para qualquer tipo de visual. Colocar `title` dentro de `objects` **falha em
silêncio**: nenhum erro, só o título customizado nunca aparece, some no título
automático do Power BI.

```json
"visual": {
  "visualContainerObjects": {
    "title": [{
      "properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": {"expr": {"Literal": {"Value": "'Meu título'"}}}
      }
    }]
  }
}
```

**Título automático do eixo: `objects.valueAxis` / `objects.categoryAxis`, propriedade `showAxisTitle`.**
Esse sim fica em `objects` (é formatação do tipo de visual, não do contêiner). Sem
isso, o Power BI monta um título de eixo concatenando os nomes das medidas/colunas
projetadas — em gráfico com 2+ medidas fica feio e comprido.

```json
"visual": {
  "objects": {
    "valueAxis": [{"properties": {"showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}}}],
    "categoryAxis": [{"properties": {"showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}}}]
  }
}
```

**Todo valor literal em `objects`/`visualContainerObjects` é uma string DAX, não JSON puro.**
Booleano vira `"Value": "true"` (string), texto vira `"Value": "'texto'"` (aspas
simples dentro da string). É o padrão em todo o arquivo, não só título/eixo.

**`queryState` — papéis usados por tipo de visual:**

| Tipo (`visualType`) | Papéis | Observação |
|---|---|---|
| `card` | `Values` | cartão simples (número grande + rótulo pequeno) |
| `clusteredColumnChart` / `clusteredBarChart` | `Category`, `Y`, `Series` (opcional) | duas ou mais medidas em `Y` sem `Series` já viram colunas agrupadas automaticamente |
| `lineChart` | `Category`, `Y` | `Category` aceita mais de uma coluna (cria hierarquia, ex. ano + período) |
| `tableEx` | `Values` | **só para tabela plana com um único tipo de campo** — ver gotcha abaixo |
| `pivotTable` | `Rows`, `Values` | dimensões em `Rows`, medidas em `Values` — o que normalmente se quer ao ouvir "tabela" ou "matriz" |
| `slicer` | `Values` | uma coluna só |
| `multiRowCard`, `gauge`, `donutChart`, `pieChart` | variam | não usados ainda neste projeto, conferir antes de usar |

**`tableEx` com coluna de dimensão e medida misturadas em `Values` é um anti-padrão.**
Sintoma: o cabeçalho da primeira coluna aparece, as linhas mostram só ela, as outras
colunas (dimensão ou medida) simplesmente não aparecem — sem erro. Confirmado numa
fonte oficial da Microsoft (`microsoft/skills-for-fabric`, skill de autoria Power BI).
Correção: usar `pivotTable`, com as colunas de dimensão em `Rows` e as medidas em
`Values`:

```json
"visual": {
  "visualType": "pivotTable",
  "query": { "queryState": {
    "Rows": { "projections": [
      {"field": {"Column": {...}}, "queryRef": "...", "nativeQueryRef": "NomeColuna"}
    ]},
    "Values": { "projections": [
      {"field": {"Measure": {...}}, "queryRef": "...", "nativeQueryRef": "NomeMedida"}
    ]}
  }},
  "objects": {
    "columnHeaders": [{"properties": {
      "columnAdjustment": {"expr": {"Literal": {"Value": "'growToFit'"}}},
      "autoSizeColumnWidth": {"expr": {"Literal": {"Value": "true"}}}
    }}]
  }
}
```

`tableEx` de verdade serve só para tabela plana com um tipo de campo só (todas
colunas ou todas medidas); no primeiro sinal de precisar misturar os dois, ir direto
de `pivotTable`.

**Referenciar coluna vs. medida no campo (`field`):**

```json
// coluna
{"Column": {"Expression": {"SourceRef": {"Entity": "NomeTabela"}}, "Property": "NomeColuna"}}
// medida
{"Measure": {"Expression": {"SourceRef": {"Entity": "NomeTabela"}}, "Property": "Nome Medida"}}
```

**Sincronizar slicer entre páginas: `syncGroup`, ausente do schema publicado mas funcional.**
Para um slicer em uma página filtrar as outras também, adicionar `syncGroup` dentro de
`visual` (irmão de `visualType`, `query`, `objects`):

```json
"visual": {
  "visualType": "slicer",
  "syncGroup": {
    "groupName": "SyncRegional",
    "fieldChanges": true,
    "filterChanges": true
  },
  "query": { "...": "..." }
}
```

Regras:
- Todo slicer com o mesmo `groupName` (em qualquer página) fica sincronizado — precisa
  existir um slicer de verdade (mesmo `visualType` e mesma coluna) em cada página que
  deve refletir o filtro, não é uma propriedade "global" de uma única visual.
- `fieldChanges` propaga troca de campo entre os slicers do grupo; `filterChanges`
  propaga a seleção/filtro. Normalmente os dois `true`.
- Os schemas publicados (`visualContainer/2.5.0`–`2.9.0`) não listam `syncGroup` —
  achado confirmado no schema interno (`visualConfiguration/9999.0.0`) da mesma fonte
  oficial (`microsoft/skills-for-fabric`). O Fabric/Desktop lê e grava normalmente
  mesmo não estando no schema público; não é motivo para desconfiar da sintaxe.
- Usado no `res_277_v2.Report` para os slicers de Regional e Município da página
  Unidades refletirem nas demais 5 páginas (`groupName` `SyncRegional` e
  `SyncMunicipio`).

## Registro de tema customizado

Tema **compartilhado do Microsoft** (o padrão que já vem em todo relatório) fica em
`themeCollection.baseTheme`, tipo `SharedResources`. Tema **próprio** precisa de duas
partes:

1. O arquivo do tema em si, em `StaticResources/RegisteredResources/NomeDoTema.json`
   (schema padrão de tema do Power BI: `dataColors`, `background`, `foreground`,
   `good`/`neutral`/`bad`, `visualStyles`, etc. — esse schema é antigo e bem
   documentado, não teve surpresa).
2. Duas referências no `report.json`:

```json
"themeCollection": {
  "baseTheme": { "...": "...", "type": "SharedResources" },
  "customTheme": {
    "name": "NomeDoTema.json",
    "type": "RegisteredResources"
  }
},
"resourcePackages": [
  { "name": "SharedResources", "type": "SharedResources", "items": [ /* já existe */ ] },
  {
    "name": "RegisteredResources",
    "type": "RegisteredResources",
    "items": [{"name": "NomeDoTema.json", "path": "NomeDoTema.json", "type": "CustomTheme"}]
  }
]
```

Esquecer o `resourcePackages` (só declarar em `themeCollection`) é o erro mais
provável — o arquivo existe mas o Fabric não sabe que precisa carregá-lo.

## TMDL (modelo semântico)

**Medida nova**: bloco `measure` dentro do `table` correspondente, com `lineageTag`
próprio (GUID único — gerar com `uuid.uuid4()`, nunca reaproveitar). TMDL indenta com
tab; um `grep -c "measure '"` (não `^measure`, por causa do tab) é o jeito rápido de
conferir quantas medidas existem num arquivo.

**Tabela nova**: além de criar o arquivo `tables/NomeTabela.tmdl`, é preciso adicionar
`ref table NomeTabela` no `model.tmdl` — sem isso a tabela existe como arquivo mas o
modelo não a carrega.

**Padrão "medida por categoria" sem dimensão real**: quando várias medidas
pré-calculadas precisam aparecer como se fossem categorias de um mesmo eixo (ex.:
"capacidade por regime", onde cada regime é uma medida separada, não uma linha de
tabela), o jeito certo é uma **tabela desconectada** + `SWITCH(SELECTEDVALUE(...))`:

```
table Categoria
    partition Categoria = calculated
        source = DATATABLE("Nome", STRING, "Ordem", INTEGER, {{"A", 1}, {"B", 2}, ...})

measure 'Medida (por categoria)' =
    SWITCH(SELECTEDVALUE('Categoria'[Nome]),
        "A", [Medida A],
        "B", [Medida B],
        ...)
```

Não precisa de relacionamento — é desconectada de propósito, o `SELECTEDVALUE` pega o
contexto de filtro do próprio eixo/slicer do visual.

**Referência a medida em DAX é `[Nome da Medida]`, sem aspas internas.** As aspas
simples só existem na *declaração* (`measure 'Nome da Medida' = ...`), nunca na
referência. Escrever `['Nome da Medida']` (aspas dentro dos colchetes) não dá erro de
sintaxe — o DAX interpreta como referência a uma *coluna* cujo nome inclui as aspas,
que não existe, daí o erro só aparece depois: "The value for '...' cannot be
determined. Either the column doesn't exist, or there is no current row for this
column." Fácil de cair nisso especificamente quando o nome da medida começa com um
caractere que "parece" precisar de aspas (ex.: `%`), mas a regra é sempre a mesma,
não importa o conteúdo do nome.

**Ordenar categoria por outra coluna**: propriedade `sortByColumn` na coluna que serve
de categoria (`column Nome ... sortByColumn: Ordem`), não no visual. Mais robusto que
tentar ordenação no `visual.json` — vale para qualquer visual que use essa coluna.

## Armadilhas de dado real (não hipotéticas — aconteceram)

**Coluna que devia ser numérica veio como texto.** A fonte (formulário/sistema de
origem) pode ter um campo cadastrado com o tipo errado — no nosso caso, um campo
"número de vagas" configurado como texto no formulário de origem, então a coluna gold
correspondente também é `string`. `SUM()` quebra com "The function SUM cannot work
with values of type String". Antes de somar uma coluna, **conferir o `dataType`
declarado no `.tmdl`** em vez de supor pelo nome. Correção sem depender de arrumar a
fonte:

```
SUMX('Tabela', IFERROR(VALUE('Tabela'[coluna_texto]), 0))
```

**Um erro de cálculo derruba TODAS as medidas do modelo, não só a que tem o erro.**
O motor do Power BI compila todas as medidas como um único "MdxScript(Model)"; se uma
falha ao compilar, os visuais que usam medidas completamente não relacionadas também
quebram (vimos isso: um cartão simples, sem nenhuma relação com a medida quebrada,
mostrando o mesmo erro genérico "capacity or license issue"). Isso é uma pista de
diagnóstico útil: **se vários visuais sem relação entre si quebram ao mesmo tempo com
erro genérico, suspeitar de erro de compilação em alguma medida do modelo**, não de
cada visual isoladamente. O texto real do erro (via "See details" no Power BI) quase
sempre aponta a medida certa.

**`DIVIDE` sem terceiro argumento retorna `BLANK`, não erro — mas também não `0`.**
Um cartão mostrando "(Blank)" em vez de "0" geralmente é `DIVIDE(a, b)` sem o
resultado alternativo. `DIVIDE(a, b, 0)` resolve a maioria dos casos. Quando o branco
vem de uma cadeia mais complexa (`COUNTROWS(FILTER(...))` sobre algo que pode ser
`BLANK`), envolver o resultado final em `COALESCE(..., 0)` é mais garantido do que
tentar rastrear onde exatamente o branco nasce.

**Percentual "impossível" (muito acima de 100%) pode ser denominador incompleto, não
só denominador de outra seção.** A primeira hipótese que confirmamos foi cobertura
desigual entre seções do formulário (medida A preenchida em 161 de 188 instâncias,
medida B em só 4 — dividir uma pela outra compara populações praticamente disjuntas).
Mas isso não esgotou o problema: o denominador em si (Ocupação total) estava
*subcontado*, não só pouco preenchido — ver o próximo item. Os dois efeitos se somam
e são fáceis de confundir um pelo outro; medir cobertura ([`leitura-onelake-sem-sql.md`](leitura-onelake-sem-sql.md),
contar quantas instâncias têm cada campo preenchido) resolve a primeira hipótese, mas
só demonstrar o número errado por completo — reconstruindo manualmente o valor
esperado a partir do dado bruto para uma instância específica — expõe a segunda.

**Formulário com "o mesmo campo" repetido por ramificação (tipo de unidade, sexo
etc.): conferir a seção inteira, não só a primeira variante encontrada.** Já sabíamos
disso da seção de Trabalho (perguntas 12.1–12.4 para unidade mista, 12.5–12.8 só
mulheres, 12.9–12.12 só homens) mas não tínhamos generalizado a lição: a seção de
Capacidade/Ocupação tem a mesma estrutura (3.1/3.2 ambos os sexos, 3.3/3.4 só
feminino, 3.5/3.6 só masculino) e passou batida — as medidas somavam só a primeira
variante, subcontando toda unidade de sexo único. Sintoma que expôs o problema: um
percentual de outra seção (nada a ver com capacidade) parecia proporcionalmente
grande demais, o que só fazia sentido se o denominador estivesse errado. Prevenção:
ao montar uma medida de soma sobre uma seção de formulário, buscar no metadata todo
campo cujo *rótulo* (não o id) corresponda à mesma pergunta antes de considerar a
medida completa — rótulos repetidos com ids diferentes são o sinal.

## Paleta institucional / tema visual

Quando o pedido é "parecer profissional/institucional" sem uma marca definida, os
critérios que funcionaram aqui (inspirados num protótipo de colega já aprovado):

- Paleta restrita (2-3 tons de uma cor principal + 1 cor de destaque + verde/âmbar/
  vermelho reservados só para status), não paleta "arco-íris" genérica de BI.
- Série em duas variações de intensidade da mesma cor quando as duas medidas são
  "limite" e "valor atual" da mesma grandeza (ex. capacidade clara, ocupação escura)
  — comunica a relação entre elas sem precisar de legenda extensa.
- Cor de status (`good`/`neutral`/`bad` no tema) reservada de verdade — nunca reusar
  para série de gráfico, senão perde o significado de alerta.
- Bordas finas (1-2px, cinza claro) em vez do padrão mais forte do Power BI deixa a
  interface mais "documento oficial", menos "dashboard de SaaS".

## Processo que funcionou (vale repetir)

1. Nunca supor sintaxe de chave/propriedade por analogia — toda vez que arriscamos
   (título do visual, eixo, tema), tivemos 1 erro em 3 tentativas. Buscar confirmação
   em fonte real antes de escrever é mais rápido que corrigir depois.
2. Validar todo JSON com `python3 -c "import json; json.load(...)"` antes de commitar
   — pega erro de sintaxe na hora, sem depender do usuário testar no portal.
3. Commit pequeno e frequente (uma medida/tabela/visual por vez, mensagem explicando
   o *porquê*, não só o *o quê*) — quando algo quebra no portal, dá pra apontar
   exatamente qual commit é suspeito.
4. Pedir a mensagem de erro completa do Fabric ("See details"), não só a tela — o
   texto genérico da UI ("capacity or license issue") esconde o erro real.

## Ler dado direto do OneLake quando não há rota até o SQL endpoint

Documentado à parte, por ser útil além do contexto de relatórios: ver
[`leitura-onelake-sem-sql.md`](leitura-onelake-sem-sql.md). Resumo: Warehouse
também grava as tabelas como Delta no OneLake (mesmo mecanismo do Lakehouse),
então dá pra ler sem `pyodbc`/SQL endpoint quando só há rota HTTPS. Foi assim
que diagnosticamos, neste projeto, que um percentual "impossível" no relatório
era dado incompleto (cobertura desigual entre seções do formulário), não bug.

## Decisão consciente: git integration via login pessoal, não Service Principal

Fora do escopo deste documento em detalhe (registrado no `CLAUDE.md` do projeto), mas
vale como aprendizado geral: conectar o workspace do Fabric ao git via Service
Principal e API é possível, mas exige um segredo de longa duração adicional (PAT do
Azure DevOps) só para automatizar uma ação que se faz raramente. Para a conexão
inicial do workspace, login pessoal pelo portal é a escolha mais simples — decisão já
tomada em mais de um projeto.
