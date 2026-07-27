# CNMP — Modelo semântico sobre o mp_gold (Resolução 277)

Especificação do modelo semântico do Power BI construído sobre o Warehouse
`mp_gold`. O modelo é criado uma vez pelo portal do Fabric; este documento
registra as decisões (tabelas, relacionamentos, medidas) para que ele possa ser
recriado ou auditado.

**Pré-requisito:** rodar o `02_carga_gold.ipynb` com o pacote atualizado
(commit com `dim_campo_alias` e o `SELECT DISTINCT` em `dim_unidade`). Sem a
recarga, `dim_unidade` tem `entidade_id_api` duplicado e o Power BI recusa os
relacionamentos muitos-para-um.

## 1. Criação

A criação é automatizada pelo notebook `03_modelo_semantico.ipynb`, com
`semantic-link-labs`: ele descobre as tabelas largas e as partes
(`fato_visita_{id}_p2`, ...) no warehouse, cria o modelo Direct Lake
(`generate_direct_lake_semantic_model`, com `overwrite=True`), aplica os
relacionamentos das seções 3, oculta as chaves da seção 4 e cria as medidas
da seção 5. Rodar o notebook inteiro é idempotente; personalizações manuais
no modelo são perdidas na recriação, então ajustes duradouros devem ser
incorporados ao notebook.

Requisito além dos da carga: o endpoint XMLA da capacidade em leitura e
escrita, que é como o TOM aplica relacionamentos e medidas.

O modelo fica em modo Direct Lake: lê os arquivos delta do Warehouse
diretamente, sem cópia nem refresh agendado de dados.

## 2. Tabelas incluídas

| Tabela | Papel |
|---|---|
| dim_unidade | dimensão: unidade prisional (uma linha por entidade), enriquecida com município, cod_ibge, regional, RAJ e comarca da planilha da SAP-SP via de-para curado (`python/src/modulos/sap/depara_unidades.py`) |
| dim_formulario | dimensão: formulário e periodicidade |
| fato_visita | fato "cabeçalho": uma linha por visita (instância), todos os formulários |
| fato_visita_1322 | fato largo: visita semestral, uma coluna por campo |
| fato_visita_1342 | fato largo: inspeção semestral, uma coluna por campo |

Se existirem partes (`fato_visita_1342_p2`, `_p3`, ...), inclua todas; elas se
relacionam 1:1 com a tabela principal do formulário via `instancia_id_api`.

Ficam fora do modelo (uso ad hoc via SQL, não em relatório):

- `dim_campo`, `dim_campo_opcao`, `dim_campo_alias`: dicionário de campos;
  incluir só se algum relatório genérico por campo for necessário.
- `fato_resposta_tipada`: EAV completo; útil para os campos de TABELA_DINAMICA,
  que não entram nas tabelas largas. Incluir junto com `dim_campo` quando esse
  caso de uso aparecer.
- `sap_unidade` (silver) e `dim_unidade_sap` (de-para): a planilha completa da
  SAP (população, capacidade, mortes, equipe de saúde) fica fora do modelo por
  decisão de escopo; as colunas geográficas já entram via `dim_unidade`.
- Tabelas largas dos formulários militares (ambiente 282): incluir quando os
  aliases deles forem curados e houver demanda de relatório.

## 3. Relacionamentos

Todos muitos-para-um, filtro em direção única (da dimensão para o fato), exceto
onde indicado:

| De (muitos) | Para (um) | Observação |
|---|---|---|
| fato_visita[entidade_id_api] | dim_unidade[entidade_id_api] | |
| fato_visita[formulario_id_api] | dim_formulario[formulario_id_api] | |
| fato_visita_1322[entidade_id_api] | dim_unidade[entidade_id_api] | |
| fato_visita_1342[entidade_id_api] | dim_unidade[entidade_id_api] | |
| fato_visita_1342_p2[instancia_id_api] | fato_visita_1342[instancia_id_api] | 1:1, se a parte existir |

As tabelas largas não precisam de relação com `fato_visita`: já carregam
`entidade_id_api`, `ano`, `periodo` e `status_atual`. Para segmentar ano e
período entre formulários diferentes numa mesma página, crie segmentações
sobre as colunas da própria tabela larga da página (ou, se isso se tornar
frequente, adicione uma `dim_periodo` no gold; ver seção 6).

## 4. Colunas ocultas

Ocultar nos fatos e dimensões as chaves técnicas, para não poluir a lista de
campos: `instancia_id_api`, `entidade_id_api`, `formulario_id_api`,
`ambiente_id_api`. Renomear no modelo, se quiser, `descricao` de `dim_unidade`
para "Unidade" e `nome` de `dim_formulario` para "Formulário".

## 5. Medidas iniciais (DAX)

Gerais, criadas em `fato_visita`:

```dax
Visitas = COUNTROWS(fato_visita)

Unidades visitadas = DISTINCTCOUNT(fato_visita[entidade_id_api])
```

Do formulário 1322 (seção III, capacidade 3.1.x e ocupação 3.2.x, ambos os
sexos), criadas em `fato_visita_1322`:

```dax
Capacidade total (1322) =
    SUM(fato_visita_1322[q3_1_1_regime_fechado_feminino])
  + SUM(fato_visita_1322[q3_1_2_regime_fechado_masculino])
  + SUM(fato_visita_1322[q3_1_3_regime_semiaberto_feminino])
  + SUM(fato_visita_1322[q3_1_4_regime_semiaberto_masculino])
  + SUM(fato_visita_1322[q3_1_5_regime_aberto_feminino])
  + SUM(fato_visita_1322[q3_1_6_regime_aberto_masculino])
  + SUM(fato_visita_1322[q3_1_7_prisao_provisoria_feminino])
  + SUM(fato_visita_1322[q3_1_8_prisao_provisoria_masculino])
  + SUM(fato_visita_1322[q3_1_9_medida_de_seguranca_feminino])
  + SUM(fato_visita_1322[q3_1_10_medida_de_seguranca_masculino])

Ocupação total (1322) =
    SUM(fato_visita_1322[q3_2_1_regime_fechado_feminino])
  + SUM(fato_visita_1322[q3_2_2_regime_fechado_masculino])
  + SUM(fato_visita_1322[q3_2_3_regime_semiaberto_feminino])
  + SUM(fato_visita_1322[q3_2_4_regime_semiaberto_masculino])
  + SUM(fato_visita_1322[q3_2_5_regime_aberto_feminino])
  + SUM(fato_visita_1322[q3_2_6_regime_aberto_masculino])
  + SUM(fato_visita_1322[q3_2_7_prisao_provisoria_feminino])
  + SUM(fato_visita_1322[q3_2_8_prisao_provisoria_masculino])
  + SUM(fato_visita_1322[q3_2_9_medida_de_seguranca_feminino])
  + SUM(fato_visita_1322[q3_2_10_medida_de_seguranca_masculino])

Taxa de ocupação (1322) =
    DIVIDE([Ocupação total (1322)], [Capacidade total (1322)])
```

Formatar a taxa como percentual. O mesmo padrão vale para as colunas de
capacidade/ocupação por sexo (3.3 a 3.6) e para o formulário 1342, consultando
os aliases em `python/src/modulos/cnmp/etl/aliases_campos.py`.

## 6. Evoluções previstas

- `dim_periodo` no gold (ano, periodo, rótulo "2026-1º sem") compartilhada
  entre os fatos, se a análise temporal cruzando formulários crescer.
- Curadoria dos aliases dos formulários militares e inclusão das tabelas
  largas deles no modelo.
- Automatizar a criação do modelo via `semantic-link-labs` em notebook, se a
  recriação manual se tornar frequente.

## 7. Cuidados operacionais

- A carga do gold recria as tabelas largas com DROP + CREATE. Em Direct Lake o
  modelo se reenquadra (reframing) sozinho, mas se colunas mudarem de nome
  (edição de alias) os visuais que as usavam quebram; trate alias como
  contrato estável depois que entrar em relatório.
- Ao adicionar campos novos curados, reabra o modelo e marque as colunas novas
  como visíveis/ocultas conforme a seção 4.
