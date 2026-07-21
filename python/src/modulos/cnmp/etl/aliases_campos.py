"""Aliases curados para as colunas das tabelas largas do gold (fato_visita_{id}).

Mapeia formulario_id_api -> campo_id_api -> nome de coluna. Campos com alias
usam esse nome na tabela larga; campos sem alias caem no padrão automático
c{campo_id_api}_{slug do label} (ver load_gold._nome_coluna).

Regras de um alias válido (validadas na carga do gold):
- minúsculas, dígitos e underscore, começando com letra (^[a-z][a-z0-9_]{0,59}$);
- único dentro do formulário;
- diferente das colunas base da tabela larga (instancia_id_api,
  entidade_id_api, ano, periodo, status_atual).

Para gerar sugestões para novos formulários (e colar aqui):
    uv run python scripts/gerar_aliases_cnmp.py <formulario_id> ...

Este arquivo é curado à mão: o script gera um ponto de partida, mas ajustes
(nomes mais curtos ou mais claros para os campos mais usados) são bem-vindos e
não devem ser sobrescritos ao rodar o script de novo.
"""

ALIASES: dict[int, dict[int, str]] = {
    # 1322 — Formulário de Visita Semestral à Estabelecimentos Prisionais (versão 2)
    1322: {
        30133: "data_da_visita",  # 1.1 Data da visita:
        30134: "periodo_de_referencia",  # 1.2 Período de referência:
        30138: "unidade_do_ministerio_publico",  # 1.3 Unidade do Ministério Público:
        30139: "juizo_responsavel_pelo_estabelecimento",  # 1.4 Juízo responsável pelo estabelecimento:
        30140: "nome_do_responsavel_pelo_estabelecimento",  # 2.1 Nome do responsável pelo estabelecimento:
        30141: "cargo_do_responsavel",  # 2.2 Cargo do responsável:
        30142: "fonte_das_informacoes",  # 2.3 Fonte das informações:
        30143: "estabelecimento_destinado_a_presos_do_se",  # 3. Estabelecimento destinado a presos do sexo:
        30148: "q3_1_1_regime_fechado_feminino",  # 3.1.1 Regime Fechado | Feminino
        30149: "q3_1_2_regime_fechado_masculino",  # 3.1.2 Regime Fechado | Masculino
        30150: "q3_1_3_regime_semiaberto_feminino",  # 3.1.3 Regime Semiaberto | Feminino
        30151: "q3_1_4_regime_semiaberto_masculino",  # 3.1.4 Regime Semiaberto | Masculino
        30152: "q3_1_5_regime_aberto_feminino",  # 3.1.5 Regime Aberto | Feminino
        30153: "q3_1_6_regime_aberto_masculino",  # 3.1.6 Regime Aberto | Masculino
        30154: "q3_1_7_prisao_provisoria_feminino",  # 3.1.7 Prisão Provisória | Feminino
        30155: "q3_1_8_prisao_provisoria_masculino",  # 3.1.8 Prisão Provisória | Masculino
        30156: "q3_1_9_medida_de_seguranca_feminino",  # 3.1.9 Medida de Segurança | Feminino
        30157: "q3_1_10_medida_de_seguranca_masculino",  # 3.1.10 Medida de Segurança | Masculino
        30159: "q3_2_1_regime_fechado_feminino",  # 3.2.1 Regime Fechado | Feminino
        30160: "q3_2_2_regime_fechado_masculino",  # 3.2.2 Regime Fechado | Masculino
        30161: "q3_2_3_regime_semiaberto_feminino",  # 3.2.3 Regime Semiaberto | Feminino
        30162: "q3_2_4_regime_semiaberto_masculino",  # 3.2.4 Regime Semiaberto | Masculino
        30163: "q3_2_5_regime_aberto_feminino",  # 3.2.5 Regime Aberto | Feminino
        30164: "q3_2_6_regime_aberto_masculino",  # 3.2.6 Regime Aberto | Masculino
        30165: "q3_2_7_prisao_provisoria_feminino",  # 3.2.7 Prisão Provisória | Feminino
        30166: "q3_2_8_prisao_provisoria_masculino",  # 3.2.8 Prisão Provisória | Masculino
        30167: "q3_2_9_medida_de_seguranca_feminino",  # 3.2.9 Medida de Segurança | Feminino
        30168: "q3_2_10_medida_de_seguranca_masculino",  # 3.2.10 Medida de Segurança | Masculino
        30170: "q3_3_1_regime_fechado_feminino",  # 3.3.1 Regime Fechado | Feminino
        30171: "q3_3_2_regime_semiaberto_feminino",  # 3.3.2 Regime Semiaberto | Feminino
        30172: "q3_3_3_regime_aberto_feminino",  # 3.3.3 Regime Aberto | Feminino
        30173: "q3_3_4_prisao_provisoria_feminino",  # 3.3.4 Prisão Provisória | Feminino
        30174: "q3_3_5_medida_de_seguranca_feminino",  # 3.3.5 Medida de Segurança | Feminino
        30176: "q3_4_1_regime_fechado_feminino",  # 3.4.1 Regime Fechado | Feminino
        30177: "q3_4_2_regime_semiaberto_feminino",  # 3.4.2 Regime Semiaberto | Feminino
        30178: "q3_4_3_regime_aberto_feminino",  # 3.4.3 Regime Aberto | Feminino
        30179: "q3_4_4_prisao_provisoria_feminino",  # 3.4.4 Prisão Provisória | Feminino
        30180: "q3_4_5_medida_de_seguranca_feminino",  # 3.4.5 Medida de Segurança | Feminino
        30181: "ha_homens_sob_custodia",  # 3.4.6 Há homens sob custódia?
        30184: "quantos_homens_estao_sob_custodia",  # 3.4.6.1 Quantos homens estão sob custódia?
        30186: "q3_5_1_regime_fechado_masculino",  # 3.5.1 Regime Fechado | Masculino
        30187: "q3_5_2_regime_semiaberto_masculino",  # 3.5.2 Regime Semiaberto | Masculino
        30188: "q3_5_3_regime_aberto_masculino",  # 3.5.3 Regime Aberto | Masculino
        30189: "q3_5_4_prisao_provisoria_masculino",  # 3.5.4 Prisão Provisória | Masculino
        30190: "q3_5_5_medida_de_seguranca_masculino",  # 3.5.5 Medida de Segurança | Masculino
        30192: "q3_6_1_regime_fechado_masculino",  # 3.6.1 Regime Fechado | Masculino
        30193: "q3_6_2_regime_semiaberto_masculino",  # 3.6.2. Regime Semiaberto | Masculino
        30194: "q3_6_3_regime_aberto_masculino",  # 3.6.3 Regime Aberto | Masculino
        30195: "q3_6_4_prisao_provisoria_masculino",  # 3.6.4 Prisão Provisória | Masculino
        30196: "q3_6_5_medida_de_seguranca_masculino",  # 3.6.5 Medida de Segurança | Masculino
        30197: "ha_mulheres_sob_custodia",  # 3.6.6 Há mulheres sob custódia?
        30200: "quantas_mulheres_estao_sob_custodia",  # 3.6.6.1 Quantas mulheres estão sob custódia?
        30201: "ha_presos_maiores_de_60_anos_de_idade",  # 4.1 Há presos maiores de 60 anos de idade?
        30204: "q4_1_1_quantos",  # 4.1.1 Quantos?
        30205: "data_mais_antiga_de_prisao",  # 4.2 Data mais antiga de prisão:
        30206: "ha_adolescentes_no_estabelecimento",  # 4.3 Há adolescentes no estabelecimento?
        30209: "q4_3_1_quantos",  # 4.3.1 Quantos?
        30210: "ha_decisao_judicial_determinando_a_inter",  # 4.3.2 Há decisão judicial determinando a internação?
        30213: "houve_providencia_do_ministerio_publico",  # 4.3.2.1 Houve providência do Ministério Público para internação em estabelecimento adequado?
        30216: "ha_presas_internas_gestantes",  # 4.4 Há presas/internas gestantes?
        30219: "q4_4_1_quantas",  # 4.4.1 Quantas?
        30220: "ha_criancas_no_estabelecimento",  # 4.5 Há crianças no estabelecimento?
        30223: "q4_5_1_quantas",  # 4.5.1 Quantas?
        30224: "ha_criancas_lactantes",  # 4.5.2 Há crianças lactantes?
        30227: "q4_5_2_1_quantas",  # 4.5.2.1 Quantas?
        30228: "ha_presos_com_deficiencia_fisica",  # 4.6 Há presos com deficiência física?
        30231: "q4_6_1_quantos",  # 4.6.1 Quantos?
        30232: "ha_presos_que_necessitam_de_ajuda_para_r",  # 4.7 Há presos que necessitam de ajuda para realizar as atividades da vida diária (alimentação, locomoção, banho)
        30235: "q4_7_1_quantos",  # 4.7.1 Quantos?
        30236: "ha_presos_com_deficiencia_mental_diagnos",  # 4.8 Há presos com deficiência mental diagnosticada?
        30239: "q4_8_1_quantos",  # 4.8.1 Quantos?
        30240: "ha_presos_com_deficiencia_mental_aparent",  # 4.9 Há presos com deficiência mental aparente e não diagnosticada?
        30243: "q4_9_1_quantos",  # 4.9.1 Quantos?
        30244: "ha_presos_indigenas",  # 4.10 Há presos indígenas?
        30247: "q4_10_1_quantos",  # 4.10.1 Quantos?
        30248: "ha_presos_estrangeiros",  # 4.11 Há presos estrangeiros?
        30251: "q4_11_1_quantos",  # 4.11.1 Quantos?
        30252: "ha_presos_em_cela_de_protecao_seguro",  # 4.12 Há presos em cela de proteção/seguro?
        30255: "q4_12_1_quantos",  # 4.12.1 Quantos?
        30256: "ha_mulheres_mantidas_no_mesmo_espaco_de",  # 4.13 Há mulheres mantidas no mesmo espaço de convivência com homens?
        30259: "q4_13_1_quantas",  # 4.13.1 Quantas?
        30260: "os_presos_provisorios_sao_mantidos_separ",  # 5.1 Os presos provisórios são mantidos separados dos presos em cumprimento de pena?
        30263: "os_presos_que_cumprem_pena_em_regimes_di",  # 5.2 Os presos que cumprem pena em regimes distintos são mantidos separados?
        30266: "os_maiores_de_60_anos_sao_mantidos_separ",  # 5.3 Os maiores de 60 anos são mantidos separados dos demais?
        30269: "os_presos_primarios_sao_mantidos_separad",  # 5.4 Os presos primários são mantidos separados dos presos reincidentes?
        30272: "os_presos_sao_mantidos_separados_conform",  # 5.5 Os presos são mantidos separados conforme a natureza do delito cometido?
        30275: "ha_grupos_ou_faccoes_criminosas_identifi",  # 5.6 Há grupos ou facções criminosas identificados no estabelecimento?
        30278: "quais_nome_e_sigla",  # 5.6.1 Quais (nome e sigla)?
        30279: "os_presos_sao_mantidos_separados_de_acor",  # 5.6.2 Os presos são mantidos separados de acordo com a identificação de grupos ou facções criminosas?
        30280: "os_presos_portadores_de_doencas_infectoc",  # 5.7 Os presos portadores de doenças infectocontagiosas são mantidos separados dos demais?
        30283: "os_policiais_agentes_de_seguranca_na_qua",  # 5.8 Os policiais/agentes de segurança, na qualidade de preso, são mantidos separados dos demais presos?
        30286: "ha_camas_para_todos_os_presos",  # 6.1 Há camas para todos os presos?
        30290: "ha_colchoes_para_todos_os_presos",  # 6.2 Há colchões para todos os presos?
        30294: "a_administracao_fornece_roupa_de_cama_pa",  # 6.3 A administração fornece roupa de cama para todos os presos?
        30298: "a_administracao_fornece_toalha_de_banho",  # 6.4 A administração fornece toalha de banho para todos os presos?
        30302: "a_administracao_fornece_uniforme_para_to",  # 6.5 A administração fornece uniforme para todos os presos?
        30306: "ha_possibilidade_de_banho_para_todos_os",  # 6.6 Há possibilidade de banho para todos os presos?
        30310: "ha_limitacao_de_acesso_ao_banho_que_prej",  # 6.7 Há limitação de acesso ao banho que prejudique o asseio?
        30313: "a_temperatura_da_agua_e_adequada_ao_clim",  # 6.8 A temperatura da água é adequada ao clima predominante da região?
        30316: "numero_de_presos_por_vaso_sanitario_latr",  # 6.9 Número de presos por vaso sanitário/latrina:
        30317: "a_administracao_fornece_material_de_higi",  # 6.10 A administração fornece material de higiene para todos os presos?
        30321: "numero_de_refeicoes_diarias",  # 7.1 Número de refeições diárias
        30328: "os_presos_reclamam_da_quantidade_de_alim",  # 7.2 Os presos reclamam da quantidade de alimento fornecida por refeição?
        30331: "os_presos_reclamam_da_qualidade_das_refe",  # 7.3 Os presos reclamam da qualidade das refeições fornecidas?
        30334: "ha_assistencia_medica",  # 8.1 Há assistência médica?
        30338: "ha_assistencia_odontologica",  # 8.2 Há assistência odontológica?
        30342: "ha_farmacia_no_estabelecimento",  # 8.3 Há farmácia no estabelecimento?
        30346: "ha_atendimento_medico_emergencial",  # 8.4 Há atendimento médico emergencial?
        30350: "ha_atendimento_pre_natal_as_presas_gesta",  # 8.5 Há atendimento pré-natal às presas gestantes?
        30354: "ha_espaco_para_banho_de_sol",  # 8.6 Há espaço para banho de sol?
        30358: "o_banho_de_sol_dura_2_horas_ou_mais",  # 8.7 O banho de sol dura 2 horas ou mais?
        30361: "houve_mortes_no_semestre_de_referencia",  # 9.1 Houve mortes no semestre de referência?
        30364: "q9_1_1_quantas",  # 9.1.1 Quantas
        30366: "homicidio",  # 9.1.1.1 Homicídio:
        30367: "suicidio",  # 9.1.1.2 Suicídio:
        30368: "causa_natural",  # 9.1.1.3 Causa Natural:
        30369: "causa_indeterminada",  # 9.1.1.4 Causa Indeterminada:
        30370: "numero_de_presos_vitimas_de_lesoes_corpo",  # 9.2 Número de presos vítimas de lesões corporais no semestre de referência:
        30371: "houve_registro_de_maus_tratos_a_preso_po",  # 9.3 Houve registro de maus tratos a preso por servidores no semestre de referência?
        30374: "q9_3_1_quantos",  # 9.3.1 Quantos?
        30375: "a_defensoria_publica_presta_assistencia",  # 10.1 A Defensoria Pública presta assistência jurídica e gratuita aos presos hipossuficientes?
        30379: "ha_outras_instituicoes_que_prestam_assis",  # 10.2 Há outras instituições que prestam assistência jurídica?
        30383: "ha_assistencia_educacional",  # 11.1 Há assistência educacional?
        30387: "numero_de_vagas_oferecidas",  # 11.1.1 Número de vagas oferecidas:
        30388: "numero_de_presos_estudando",  # 11.1.2 Número de presos estudando:
        30389: "ha_atendimento_pelo_servico_de_assistenc",  # 11.2 Há atendimento pelo serviço de assistência social?
        30393: "ha_atendimento_psicologico_na_unidade",  # 11.3 Há atendimento psicológico na unidade?
        30397: "ha_assistencia_religiosa",  # 11.4 Há assistência religiosa?
        30400: "q12_1_trabalho_interno",  # 12.1 Trabalho Interno
        30403: "q12_1_1_total_de_homens_trabalhando",  # 12.1.1 Total de homens trabalhando:
        30404: "q12_1_2_total_de_mulheres_trabalhando",  # 12.1.2 Total de mulheres trabalhando:
        30405: "q12_2_trabalho_externo",  # 12.2 Trabalho Externo
        30408: "q12_2_1_total_de_homens_trabalhando",  # 12.2.1 Total de homens trabalhando:
        30409: "q12_2_2_total_de_mulheres_trabalhando",  # 12.2.2 Total de mulheres trabalhando:
        30410: "q12_3_trabalho_remunerado",  # 12.3 Trabalho Remunerado
        30413: "q12_3_1_total_de_homens_trabalhando",  # 12.3.1 Total de homens trabalhando:
        30414: "q12_3_2_total_de_mulheres_trabalhando",  # 12.3.2 Total de mulheres trabalhando:
        30415: "q12_4_trabalho_voluntario",  # 12.4 Trabalho Voluntário
        30418: "q12_4_1_total_de_homens_trabalhando",  # 12.4.1 Total de homens trabalhando:
        30419: "q12_4_2_total_de_mulheres_trabalhando",  # 12.4.2 Total de mulheres trabalhando:
        30420: "q12_5_trabalho_interno",  # 12.5 Trabalho Interno
        30421: "q12_5_1_total_de_mulheres_trabalhando",  # 12.5.1 Total de mulheres trabalhando:
        30422: "q12_6_trabalho_externo",  # 12.6 Trabalho Externo
        30423: "q12_6_1_total_de_mulheres_trabalhando",  # 12.6.1 Total de mulheres trabalhando:
        30424: "q12_7_trabalho_remunerado",  # 12.7 Trabalho Remunerado
        30425: "q12_7_1_total_de_mulheres_trabalhando",  # 12.7.1 Total de mulheres trabalhando
        30426: "q12_8_trabalho_voluntario",  # 12.8 Trabalho Voluntário
        30427: "q12_8_1_total_de_mulheres_trabalhando",  # 12.8.1 Total de mulheres trabalhando:
        30428: "q12_9_trabalho_interno",  # 12.9 Trabalho Interno
        30429: "q12_9_1_total_de_homens_trabalhando",  # 12.9.1 Total de homens trabalhando:
        30430: "q12_10_trabalho_externo",  # 12.10 Trabalho Externo
        30431: "q12_10_1_total_de_homens_trabalhando",  # 12.10.1 Total de homens trabalhando:
        30432: "q12_11_trabalho_remunerado",  # 12.11 Trabalho Remunerado
        30433: "q12_11_1_total_de_homens_trabalhando",  # 12.11.1 Total de homens trabalhando:
        30434: "q12_12_trabalho_voluntario",  # 12.12 Trabalho Voluntário
        30435: "q12_12_1_total_de_homens_trabalhando",  # 12.12.1 Total de homens trabalhando:
        30436: "os_presos_sao_cientificados_das_normas_d",  # 13.1 Os presos são cientificados das normas disciplinares no início da execução da pena?
        30437: "existe_comissao_tecnica_de_classificacao",  # 13.2 Existe comissão técnica de classificação dos condenados?
        30438: "ha_registro_de_imposicao_de_sancao_disci",  # 13.3 Há registro de imposição de sanção disciplinar?
        30439: "a_aplicacao_da_sancao_disciplinar_observ",  # 13.4 A aplicação da sanção disciplinar observa o devido processo legal?
        30440: "sao_executadas_sancoes_coletivas",  # 13.5 São executadas sanções coletivas?
        30441: "ha_cela_escura_aplicada_como_sancao_disc",  # 13.6 Há cela escura aplicada como sanção disciplinar?
        30442: "numero_de_sancoes_de_isolamento_aplicada",  # 13.7 Número de sanções de isolamento aplicadas no semestre de referência:
        30443: "numero_de_presos_em_regime_disciplinar_d",  # 13.8 Número de presos em regime disciplinar diferenciado (RDD):
        30444: "numero_de_armas_de_fogo_apreendidas_no_s",  # 13.9 Número de armas de fogo apreendidas no semestre de referência:
        30445: "numero_de_aparelhos_de_comunicacao_e_ou",  # 13.10 Número de aparelhos de comunicação e/ou acessórios apreendidos no semestre de referência:
        30446: "houve_apreensao_de_drogas",  # 13.11 Houve apreensão de drogas?
        30448: "houve_fugas_no_semestre_de_referencia",  # 13.12 Houve fugas no semestre de referência?
        30449: "q13_12_1_quantas",  # 13.12.1 Quantas:
        30450: "desse_total_de_fugas_quantas_se_deram_pe",  # 13.12.2 Desse total de fugas, quantas se deram pelo não retorno de saída autorizada?
        30451: "houve_movimento_coletivo_para_subverter",  # 13.13 Houve movimento coletivo para subverter a ordem ou disciplina no semestre de referência?
        30452: "q13_13_1_quantos",  # 13.13.1 Quantos
        30453: "houve_falta_grave_individual_para_subver",  # 13.14 Houve falta grave individual para subverter a ordem ou a disciplina no semestre de referência?
        30454: "q13_14_1_quantas",  # 13.14.1 Quantas?
        30455: "e_garantida_a_visitacao_social",  # 14.1 É garantida a visitação social?
        30456: "duracao_da_visitacao_social_em_minutos",  # 14.1.1 Duração da visitação social (em minutos):
        30457: "periodicidade_da_visitacao_social_em_dia",  # 14.1.2 Periodicidade da visitação social (em dias):
        30458: "e_garantida_a_visitacao_intima",  # 14.2 É garantida a visitação íntima?
        30459: "duracao_da_visitacao_intima_em_minutos",  # 14.2.1 Duração da visitação íntima (em minutos):
        30460: "periodicidade_da_visitacao_intima_em_dia",  # 14.2.2 Periodicidade da visitação íntima (em dias):
        30461: "ha_pessoas_submetidas_a_medida_de_segura",  # 15.1 Há pessoas submetidas a medida de segurança?
        30462: "q15_1_1_quantas",  # 15.1.1 Quantas
        30463: "deste_total_quantas_cumprem_medida_de_in",  # 15.1.1.1 Deste total, quantas cumprem medida de internação?
        30464: "deste_total_quantas_cumprem_medida_de_tr",  # 15.1.1.2 Deste total quantas cumprem medida de tratamento ambulatorial?
        30465: "deste_total_quantos_internos_estao_com_p",  # 15.1.1.3 Deste total quantos internos estão com perícias com prazo vencido?
        30466: "deste_total_quantos_internos_tiveram_a_c",  # 15.1.1.4 Deste total quantos internos tiveram a cessação de periculosidade sem a correspondente desinternação judicial?
        30467: "ha_fornecimento_de_medicacao_controlada",  # 15.2 Há fornecimento de medicação controlada?
        30471: "o_membro_confirma_que_esteve_presencialm",  # 16.1 O membro confirma que esteve presencialmente nos locais avaliados?
        30472: "consideracoes",  # 17.1 Considerações
        30473: "providencias",  # 17.2 Providências
    },
    # 1342 — Formulário de Visita de Inspeção Semestral | Estabelecimentos Prisionais (versão 1)
    1342: {
        30533: "data_da_visita",  # 1.1 Data da Visita
        30534: "forma_de_inspecao",  # 1.2 Forma de inspeção
        30554: "estabelecimento_prisional_destinado_a_pr",  # 1.3 Estabelecimento prisional destinado a presos do sexo
        30541: "o_estabelecimento_prisional_possui_ala_p",  # 1.3.1 O estabelecimento prisional possui ala/pavilhão para *PPL autodeclaradas LGBTI+?
        30717: "orgao_do_ministerio_publico_responsavel",  # 1.4 Órgão do Ministério Público responsável pela inspeção do estabelecimento prisional:
        30718: "juizo_responsavel_pelo_estabelecimento_p",  # 1.5 Juízo responsável pelo estabelecimento prisional:
        30719: "responsavel_pelo_estabelecimento_prision",  # 1.6 Responsável pelo estabelecimento prisional:
        30720: "data_de_inicio_do_funcionamento_do_estab",  # 1.6.1 Data de início do funcionamento do estabelecimento prisional:
        30721: "data_do_inicio_da_gestao_do_responsavel",  # 1.6.2 Data do início da gestão do responsável pelo estabelecimento prisional:
        30731: "responsavel_pela_seguranca_do_estabeleci",  # 1.7 Responsável pela segurança do estabelecimento prisional
        30735: "q1_8_total_de_pessoas_que_atuam_nas_atividade",  # 1.8 Total de pessoas que atuam nas atividades administrativas do estabelecimento prisional:
        30742: "deste_total_quantas_estao_afastadas_de_s",  # 1.8.1 Deste total, quantas estão afastadas de suas atividades, inclusive por motivo de saúde?
        30770: "q2_1_o_estabelecimento_prisional_possui_regim",  # 2.1 O estabelecimento prisional possui regimento ou regulamento interno?
        30771: "q2_2_o_estabelecimento_prisional_possui_regim",  # 2.2 O estabelecimento prisional possui regimento ou regulamento disciplinar?
        30772: "o_estabelecimento_prisional_possui_plano",  # 2.3 O estabelecimento prisional possui plano de prevenção e combate a incêndio?
        30773: "o_estabelecimento_prisional_possui_auto",  # 2.4 O estabelecimento prisional possui auto de vistoria do corpo de bombeiros (AVCB)?
        30774: "data_de_validade_do_avcb",  # 2.4.1 Data de validade do AVCB?
        30779: "o_estabelecimento_prisional_possui_estud",  # 2.5 O estabelecimento prisional possui estudo de análise de risco e plano de contingência?
        30944: "o_estabelecimento_prisional_possui_contr",  # 2.6 O estabelecimento prisional possui contratos vigentes de descentralização de serviços (terceirização)?
        30946: "c30946_alimentacao",  # Alimentação
        30949: "c30949_assistencia_educacional",  # Assistência Educacional
        30950: "assistencia_social",  # Assistência Social
        30951: "limpeza",  # Limpeza
        30952: "seguranca",  # Segurança
        30963: "c30963_assistencia_a_saude",  # Assistência à Saúde
        30964: "c30964_assistencia_juridica",  # Assistência Jurídica
        30965: "lavanderia",  # Lavanderia
        30971: "manutencao_predial",  # Manutenção predial
        30972: "servicos_administrativos",  # Serviços Administrativos
        31009: "total_de_funcionarios_terceirizados_que",  # 2.6.2 Total de funcionários terceirizados que atuam no estabelecimento prisional
        30548: "q3_1_1_1_homens",  # 3.1.1.1 Homens
        30549: "q3_1_1_2_mulheres",  # 3.1.1.2 Mulheres
        30558: "c30558_homens",  # 3.1.1.1 Homens
        30559: "c30559_mulheres",  # 3.1.1.2 Mulheres
        30561: "q3_1_2_1_homens",  # 3.1.2.1 Homens
        30562: "q3_1_2_2_mulheres",  # 3.1.2.2 Mulheres
        30563: "c30563_homens",  # 3.1.2.1 Homens
        30564: "c30564_mulheres",  # 3.1.2.2 Mulheres
        30567: "q3_1_3_1_homens",  # 3.1.3.1 Homens
        30568: "q3_1_3_2_mulheres",  # 3.1.3.2 Mulheres
        30569: "c30569_homens",  # 3.1.3.1 Homens
        30570: "c30570_mulheres",  # 3.1.3.2 Mulheres
        31051: "q3_1_4_1_homens",  # 3.1.4.1 Homens
        31052: "q3_1_4_2_mulheres",  # 3.1.4.2 Mulheres
        31053: "c31053_homens",  # 3.1.4.1 Homens
        31054: "c31054_mulheres",  # 3.1.4.2 Mulheres
        31056: "q3_1_5_1_homens",  # 3.1.5.1 Homens
        31058: "q3_1_5_2_mulheres",  # 3.1.5.2 Mulheres
        31057: "c31057_homens",  # 3.1.5.1 Homens
        31059: "c31059_mulheres",  # 3.1.5.2 Mulheres
        31062: "q3_2_1_1_homens",  # 3.2.1.1 Homens
        31064: "q3_2_1_2_mulheres",  # 3.2.1.2 Mulheres
        31063: "c31063_homens",  # 3.2.1.1 Homens
        31065: "c31065_mulheres",  # 3.2.1.2 Mulheres
        31067: "q3_2_2_1_homens",  # 3.2.2.1 Homens
        31069: "q3_2_2_2_mulheres",  # 3.2.2.2 Mulheres
        31068: "c31068_homens",  # 3.2.2.1 Homens
        31070: "c31070_mulheres",  # 3.2.2.2 Mulheres
        31073: "q3_2_3_1_homens",  # 3.2.3.1 Homens
        31074: "q3_2_3_2_mulheres",  # 3.2.3.2 Mulheres
        31072: "c31072_homens",  # 3.2.3.1 Homens
        31075: "c31075_mulheres",  # 3.2.3.2 Mulheres
        31077: "q3_2_4_1_homens",  # 3.2.4.1 Homens
        31078: "q3_2_4_2_mulheres",  # 3.2.4.2 Mulheres
        31079: "c31079_homens",  # 3.2.4.1 Homens
        31080: "c31080_mulheres",  # 3.2.4.2 Mulheres
        31082: "q3_2_5_1_homens",  # 3.2.5.1 Homens
        31083: "q3_2_5_2_mulheres",  # 3.2.5.2 Mulheres
        31084: "c31084_homens",  # 3.2.5.1 Homens
        31085: "c31085_mulheres",  # 3.2.5.2 Mulheres
        30572: "o_estabelecimento_prisional_e_federal",  # 3.3 O estabelecimento prisional é FEDERAL?
        30573: "o_ha_presos_originarios_da_justica_estad",  # 3.3.1 O Há presos originários da Justiça ESTADUAL?
        30574: "q3_3_1_1_quantas",  # 3.3.1.1 Quantas?
        30575: "o_ha_presos_originarios_da_justica_feder",  # 3.3.2 O Há presos originários da Justiça FEDERAL?
        30576: "q3_3_2_1_quantas",  # 3.3.2.1 Quantas?
        31358: "q3_4_1_quantos_cumprem_pena_no_estabelecimento",  # 3.4.1 Quantos cumprem pena no estabelecimento prisional?
        31359: "q3_4_2_quantos_cumprem_pena_fora_do_estabelecim",  # 3.4.2 Quantos cumprem pena fora do estabelecimento prisional, mas ainda são vinculados a este?
        31360: "q3_4_2_1_desse_total_quantas_sao_monitoradas_elet",  # 3.4.2.1 Desse total, quantas são monitoradas eletronicamente?
        31362: "q3_5_1_quantos_cumprem_pena_no_estabelecimento",  # 3.5.1 Quantos cumprem pena no estabelecimento prisional?
        31363: "q3_5_2_quantos_cumprem_pena_fora_do_estabelecim",  # 3.5.2 Quantos cumprem pena fora do estabelecimento prisional, mas ainda são vinculados a este?
        31364: "q3_5_2_1_desse_total_quantas_sao_monitoradas_elet",  # 3.5.2.1 Desse total, quantas são monitoradas eletronicamente?
        31366: "q3_6_1_quantos_cumprem_pena_no_estabelecimento",  # 3.6.1 Quantos cumprem pena no estabelecimento prisional?
        31367: "q3_6_2_quantos_cumprem_pena_fora_do_estabelecim",  # 3.6.2 Quantos cumprem pena fora do estabelecimento prisional, mas ainda são vinculados a estes?
        31368: "q3_6_2_1_desse_total_quantas_sao_monitoradas_elet",  # 3.6.2.1 Desse total, quantas são monitoradas eletronicamente?
        32195: "q4_1_1_1_amarelo",  # 4.1.1.1 Amarelo
        32196: "q4_1_1_2_branco",  # 4.1.1.2 Branco
        32197: "q4_1_1_3_indigena",  # 4.1.1.3 Indígena
        32198: "q4_1_1_4_pardo",  # 4.1.1.4 Pardo
        32199: "q4_1_1_5_preto",  # 4.1.1.5 Preto
        36674: "c36674_amarelo",  # 4.1.1.1 Amarelo
        36675: "c36675_branco",  # 4.1.1.2 Branco
        36676: "c36676_indigena",  # 4.1.1.3 Indígena
        36677: "c36677_pardo",  # 4.1.1.4 Pardo
        36678: "c36678_preto",  # 4.1.1.5 Preto
        32201: "q4_1_2_1_amarelo",  # 4.1.2.1 Amarelo
        32202: "q4_1_2_2_branco",  # 4.1.2.2 Branco
        32203: "q4_1_2_3_indigena",  # 4.1.2.3 Indígena
        32204: "q4_1_2_4_pardo",  # 4.1.2.4 Pardo
        32205: "q4_1_2_5_preto",  # 4.1.2.5 Preto
        36680: "c36680_amarelo",  # 4.1.2.1 Amarelo
        36681: "c36681_branco",  # 4.1.2.2 Branco
        36682: "c36682_indigena",  # 4.1.2.3 Indígena
        36683: "c36683_pardo",  # 4.1.2.4 Pardo
        36684: "c36684_preto",  # 4.1.2.5 Preto
        32207: "q4_1_3_1_amarelo",  # 4.1.3.1 Amarelo
        32208: "q4_1_3_2_branco",  # 4.1.3.2 Branco
        32209: "q4_1_3_3_indigena",  # 4.1.3.3 Indígena
        32210: "q4_1_3_4_pardo",  # 4.1.3.4 Pardo
        32211: "q4_1_3_5_preto",  # 4.1.3.5 Preto
        31371: "ha_ppl_com_60_anos_ou_mais",  # 4.2 Há *PPL com 60 anos ou mais?
        31373: "q4_2_1_quantas",  # 4.2.1 Quantas?
        31374: "as_ppl_com_60_anos_ou_mais_sao_mantidas",  # 4.2.2 As *PPL com 60 anos ou mais são mantidas separadas das demais?
        31375: "ha_ppl_com_deficiencia",  # 4.3 Há *PPL com deficiência?
        31376: "q4_3_1_quantas",  # 4.3.1 Quantas?
        31378: "ha_acessibilidade_para_pessoas_com_defic",  # 4.3.2 Há acessibilidade para pessoas com deficiência?
        31379: "ha_ppl_com_deficiencia_fisica",  # 4.3.3 Há *PPL com deficiência física?
        31459: "q4_3_3_1_quantas",  # 4.3.3.1 Quantas?
        31460: "ha_ppl_com_deficiencia_mental_diagnostic",  # 4.3.4 Há *PPL com deficiência mental diagnosticada?
        31464: "q4_3_4_1_quantas",  # 4.3.4.1 Quantas?
        31470: "ha_ppl_com_deficiencia_mental_aparente_e",  # 4.3.5 Há *PPL com deficiência mental aparente e/ou não diagnosticada? (segundo avaliação da direção do estabelecimento prisional)
        31473: "q4_3_5_1_quantas",  # 4.3.5.1 Quantas?
        30577: "ha_ppl_com_deficiencia_sensorial",  # 4.3.6 Há *PPL com deficiência sensorial?
        30579: "auditiva",  # 4.3.6.1.1 Auditiva
        30580: "fala",  # 4.3.6.1.2 Fala
        30581: "visual",  # 4.3.6.1.3 Visual
        31476: "ha_ppl_com_deficiencias_multiplas",  # 4.3.7 Há *PPL com deficiências múltiplas?
        31477: "q4_3_7_1_quantas",  # 4.3.7.1 Quantas?
        31990: "ha_ppl_que_necessitam_de_ajuda_para_real",  # 4.4 Há *PPL que necessitam de ajuda para realizar as atividades diárias (alimentação, banho, comunicação, locomoção etc.)?
        31991: "q4_4_1_quantas",  # 4.4.1 Quantas?
        31992: "ha_ppl_nao_nacionais",  # 4.5 Há *PPL Não Nacionais?
        32001: "q4_5_1_1_1_1_homens",  # 4.5.1.1.1.1 HOMENS
        32002: "q4_5_1_1_1_2_mulheres",  # 4.5.1.1.1.2 MULHERES
        32004: "q4_5_1_1_1_3_autodeclaradas_lgbti",  # 4.5.1.1.1.3 Autodeclaradas LGBTI+
        32006: "q4_5_1_1_2_1_homens",  # 4.5.1.1.2.1 HOMENS
        32007: "q4_5_1_1_2_2_mulheres",  # 4.5.1.1.2.2 MULHERES
        32008: "q4_5_1_1_2_3_autodeclaradas_lgbti",  # 4.5.1.1.2.3 Autodeclaradas LGBTI+
        32010: "q4_5_1_1_3_1_homens",  # 4.5.1.1.3.1 HOMENS
        32011: "q4_5_1_1_3_2_mulheres",  # 4.5.1.1.3.2 MULHERES
        32012: "q4_5_1_1_3_3_autodeclaradas_lgbti",  # 4.5.1.1.3.3 Autodeclaradas LGBTI+
        32014: "q4_5_1_1_4_1_homens",  # 4.5.1.1.4.1 HOMENS
        32015: "q4_5_1_1_4_2_mulheres",  # 4.5.1.1.4.2 MULHERES
        32016: "q4_5_1_1_4_3_autodeclaradas_lgbti",  # 4.5.1.1.4.3 Autodeclaradas LGBTI+
        32019: "q4_5_1_1_5_1_homens",  # 4.5.1.1.5.1 HOMENS
        32021: "q4_5_1_1_5_2_mulheres",  # 4.5.1.1.5.2 MULHERES
        32022: "q4_5_1_1_5_3_autodeclaradas_lgbti",  # 4.5.1.1.5.3 Autodeclaradas LGBTI+
        32031: "as_ppl_estrangeiras_sao_mantidas_separad",  # 4.5.2 As *PPL estrangeiras são mantidas separadas da demais?
        32032: "ha_fluxo_definido_para_comunicacao_com_r",  # 4.5.3 Há fluxo definido para comunicação com representantes diplomáticos e consulares dos Estados que pertençam?
        32033: "ha_ppl_indigenas",  # 4.6 Há *PPL indígenas?
        32035: "as_ppl_indigenas_sao_mantidas_separadas",  # 4.6.1 As *PPL indígenas são mantidas separadas das demais?
        32036: "a_funai_foi_comunicada_sobre_o_ingresso",  # 4.6.2 A FUNAI foi comunicada sobre o ingresso desses indígenas no estabelecimento prisional?
        32037: "ha_ppl_autodeclaradas_lgbti",  # 4.7 Há *PPL autodeclaradas LGBTI+?
        32233: "as_ppl_autodeclaradas_lgbti_sao_mantidas",  # 4.7.1 As *PPL autodeclaradas LGBTI+ são mantidas separadas das demais?
        32039: "e_permitida_a_manutencao_dos_caracteres",  # 4.7.2 É permitida a manutenção dos caracteres secundários segundo a identidade de gênero de as pessoas autodeclaradas LGBTI+?
        32043: "o_estabelecimento_prisional_fornece_kits",  # 4.7.3 O estabelecimento prisional fornece kits de higiene adaptados às necessidades específicas população LGBTI+, incluindo, mas não se limitando, itens para pessoas transgênero em processo de transição?
        32047: "q4_7_4_no_periodo_de_referencia_houve_registro",  # 4.7.4 No período de referência, houve registro de violação à garantia de utilização do nome social pela população LGBTI+?
        32048: "no_periodo_de_referencia_houve_capacitac",  # 4.7.5 No período de referência, houve capacitação dos profissionais que atuam no estabelecimento prisional na temática LGBTI+?
        32049: "o_estabelecimento_prisional_dispoe_de_pr",  # 4.7.6 O estabelecimento prisional dispõe de protocolos de atendimento específicos para a população LGBTI+, que consideram suas necessidades de saúde, segurança e bem-estar?
        32051: "medidas_para_prevenir_e_responder",  # Medidas para prevenir e responder
        32052: "ha_ppl_gestantes",  # 4.8 Há *PPL gestantes?
        32053: "q4_8_1_quantas",  # 4.8.1 Quantas?
        32054: "q4_9_ha_criancas_no_estabelecimento_prisional",  # 4.9 Há crianças no estabelecimento prisional?
        32055: "c32055_ha_criancas_no_estabelecimento_prisional",  # 4.9 Há crianças no estabelecimento prisional?
        32056: "q4_9_1_quantas",  # 4.9.1 Quantas?
        32178: "c32178_quantas",  # 4.9.1 Quantas?
        32173: "q4_9_1_1_desse_total_quantas_sao_lactentes",  # 4.9.1.1 Desse total, quantas são lactentes?
        32180: "c32180_desse_total_quantas_sao_lactentes",  # 4.9.1.1 Desse total, quantas são lactentes?
        32174: "q4_9_2_o_estabelecimento_prisional_oferece_cond",  # 4.9.2 O estabelecimento prisional oferece condições para os filhos permanecerem com suas mães? F
        32181: "c32181_o_estabelecimento_prisional_oferece_cond",  # 4.9.2 O estabelecimento prisional oferece condições para os filhos permanecerem com suas mães?
        32147: "ha_ppl_com_doencas_infectocontagiosas",  # 4.10 Há *PPL com doenças infectocontagiosas?
        32148: "q4_10_1_quantas",  # 4.10.1 Quantas?
        32149: "as_ppl_com_doencas_infectocontagiosas_sa",  # 4.10.2 As *PPL com doenças infectocontagiosas são mantidas separadas das demais?
        32150: "ha_local_de_isolamento_para_as_ppl_com_d",  # 4.10.3 Há local de isolamento para as *PPL com doenças infectocontagiosas?
        32154: "ha_ppl_em_tratamento_de_saude_continuado",  # 4.11 Há *PPL em tratamento de saúde continuado?
        32155: "quantas_em_tratamento_para_dependencia_q",  # 4.11.1 Quantas em tratamento para dependência química?
        32156: "quantas_em_tratamento_para_diabetes",  # 4.11.2 Quantas em tratamento para diabetes?
        36688: "quantas_em_tratamento_para_hipertensao",  # 4.11.3 Quantas em tratamento para hipertensão?
        32158: "quantas_em_tratamento_para_o_hiv",  # 4.11.4 Quantas em tratamento para o HIV?
        32159: "quantas_em_tratamento_para_hepatite",  # 4.11.5 Quantas em tratamento para hepatite?
        32160: "quantas_em_tratamento_para_tuberculose",  # 4.11.6 Quantas em tratamento para tuberculose?
        32161: "quantas_em_tratamento_para_outras_doenca",  # 4.11.7 Quantas em tratamento para outras doenças?
        30600: "ha_mulheres_cisgenero_mantidas_no_espaco",  # 5.1 Há mulheres cisgênero mantidas no espaço de convivência dos homens cisgêneros?
        30603: "q5_1_1_quantas",  # 5.1.1 Quantas?
        30604: "houve_providencia_do_ministerio_publico",  # 5.1.2 Houve providência do Ministério Público para adequar a situação?
        30607: "as_ppl_em_prisao_provisoria_sao_mantidas",  # 5.2 As *PPL em prisão provisória são mantidas separadas das *PPL em cumprimento de pena?
        30610: "as_ppl_em_cumprimento_de_pena_em_regimes",  # 5.3 As *PPL em cumprimento de pena em regimes distintos são mantidas separadas?
        30613: "as_ppl_primarias_sao_mantidas_separadas",  # 5.4 As *PPL primárias são mantidas separadas das reincidentes?
        30616: "as_ppl_sao_separadas_conforme_a_natureza",  # 5.5 As *PPL são separadas conforme a natureza do delito que cometeram?
        30619: "os_policiais_e_agentes_de_seguranca_na_q",  # 5.6 Os policiais e agentes de segurança, na qualidade de *PPL, são mantidos separadas dos demais?
        30622: "ha_celas_de_protecao_ou_seguro_no_estabe",  # 5.7 Há Celas de Proteção ou Seguro no estabelecimento prisional?
        30625: "total_de_ppl_nas_celas_de_protecao_ou_no",  # 5.7.1 Total de *PPL nas Celas de Proteção ou no Seguro:
        30626: "ha_grupos_ou_faccoes_criminosas_no_estab",  # 5.8 Há grupos ou facções criminosas no estabelecimento prisional?
        30629: "os_presos_sao_mantidos_separados_por_gru",  # 5.8.1 Os presos são mantidos separados por grupo ou facção criminosa?
        30633: "o_estabelecimento_prisional_possui_alas",  # 5.8.2 O estabelecimento prisional possui alas inteiramente destinadas a integrantes
        30640: "indique_quais_grupos_ou_faccoes_criminos",  # 5.8.3 Indique quais grupos ou facções criminosas estão presentes no estabelecimento prisional:
        30636: "camas",  # 6.1.1 Camas
        30641: "colchoes",  # 6.1.2 Colchões
        30645: "roupas_de_cama",  # 6.1.3 Roupas de cama
        30653: "uniformes",  # 6.1.4 Uniformes
        30661: "calcados",  # 6.1.5 Calçados
        30665: "toalhas",  # 6.1.6 Toalhas
        30673: "artigos_de_higiene_pessoal",  # 6.1.7 Artigos de higiene pessoal
        30681: "artigos_de_limpeza",  # 6.1.8 Artigos de limpeza
        30692: "q6_1_9_absorventes",  # 6.1.9 Absorventes
        30709: "c30709_absorventes",  # 6.1.9 Absorventes
        30705: "q6_1_10_fraldas_para_criancas",  # 6.1.10 Fraldas para crianças
        30713: "c30713_fraldas_para_criancas",  # 6.1.10 Fraldas para crianças
        30744: "e_permitido_que_o_visitante_leve_vestuar",  # 6.2 É permitido que o visitante leve vestuário às *PPL?
        30747: "e_permitido_que_o_visitante_leve_objetos",  # 6.3 É permitido que o visitante leve objetos de uso pessoal às *PPL?
        30750: "ha_local_destinado_a_venda_de_produtos_e",  # 6.4 Há local destinado à venda de produtos e objetos permitidos e não fornecidos pela Administração?
        30753: "houve_licitacao",  # 6.4.1 Houve licitação?
        30756: "ha_limitacao_de_acesso_ao_banho_as_ppl",  # 6.5 Há limitação de acesso ao banho às *PPL?
        30759: "ha_instalacoes_sanitarias_em_todas_as_ce",  # 6.6 Há instalações sanitárias em todas as celas?
        30762: "ha_privacidade_para_o_uso_das_instalacoe",  # 6.7 Há privacidade para o uso das instalações sanitárias?
        30783: "ha_limitacao_de_horario_para_o_uso_das_i",  # 6.8 Há limitação de horário para o uso das instalações sanitárias?
        30797: "ha_fornecimento_ininterrupto_de_agua_pot",  # 6.9 Há fornecimento ininterrupto de água potável à todas as *PPL?
        30803: "q6_10_o_estabelecimento_prisional_possui_siste",  # 6.10 O estabelecimento prisional possui sistema de tratamento de esgoto?
        30809: "q6_11_o_estabelecimento_prisional_possui_siste",  # 6.11 O estabelecimento prisional possui sistema de tratamento ou coleta de lixo regular?
        31673: "durante_a_visita_de_inspecao_foram_obser",  # 6.12 Durante a visita de inspeção, foram observados problemas visíveis nas instalações do estabelecimento prisional?
        30583: "edificacao",  # Edificação
        30584: "eletrica",  # Elétrica
        30585: "hidraulica",  # Hidráulica
        30586: "sanitarias",  # Sanitárias
        30587: "c30587_outros",  # Outros
        31678: "outros_problemas_visiveis",  # Outros problemas visíveis
        30649: "a_alimentacao_e_preparada_no_proprio_est",  # 7.1 A alimentação é preparada no próprio estabelecimento prisional?
        30657: "q7_1_1_ha_local_apropriado_para_armazenamento_d",  # 7.1.1 Há local apropriado para armazenamento dos produtos utilizados na preparação dos alimentos em relação à limpeza, ventilação, temperatura e iluminação?
        30669: "a_alimentacao_e_fornecida_por_empresa_te",  # 7.2 A alimentação é fornecida por empresa terceirizada?
        30677: "q7_2_1_ha_local_apropriado_para_armazenamento_d",  # 7.2.1 Há local apropriado para armazenamento dos produtos fornecidos em relação à limpeza, ventilação, temperatura e iluminação?
        30685: "numero_de_refeicoes_diarias",  # 7.3 Número de refeições diárias:
        30696: "q7_3_1_no_periodo_de_referencia_houve_registro",  # 7.3.1 No período de referência, houve registro de fornecimento de refeição com intervalo superior a 8 horas (privação de alimentos)?
        30699: "q7_3_2_no_periodo_de_referencia_houve_registro",  # 7.3.2 No período de referência, houve registro de fornecimento de mais de uma refeição em uma única entrega (fornecimento antecipado de alimentos)?
        30702: "ha_controle_de_qualidade_das_refeicoes",  # 7.4 Há controle de qualidade das refeições?
        30727: "quem_atesta_a_qualidade_das_refeicoes",  # 7.4.1 Quem atesta a qualidade das refeições?
        30732: "as_refeicoes_sao_adaptadas_por_motivos_r",  # 7.5 As refeições são adaptadas por motivos religiosos?
        30736: "as_refeicoes_sao_adaptadas_por_motivos_d",  # 7.6 As refeições são adaptadas por motivos de saúde?
        30739: "ha_outras_formas_de_fornecimento_de_alim",  # 7.7 Há outras formas de fornecimento de alimentos?
        30766: "familia",  # Família
        30767: "compra_no_estabelecimento_prisional",  # Compra no estabelecimento prisional
        30768: "c30768_outras",  # Outras
        30769: "outras_formas_de_fornecimento",  # Outras formas de fornecimento
        30786: "as_ppl_deslocadas_para_audiencia_ou_outr",  # 7.8 As *PPL deslocadas para audiência ou outras atividades externas recebem alimentação quando saem ou retornam, independentemente do horário?
        30825: "ha_assistencia_medica_no_estabelecimento",  # 8.1 Há assistência médica no estabelecimento prisional?
        30881: "c30881_rede_publica",  # Rede Pública
        30830: "c30830_rede_publica",  # Rede Pública
        30831: "c30831_empresa_terceirizada",  # Empresa terceirizada
        30883: "c30883_empresa_terceirizada",  # Empresa terceirizada
        30832: "c30832_profissional_terceirizado",  # Profissional terceirizado
        30887: "c30887_profissional_terceirizado",  # Profissional terceirizado
        30833: "c30833_outros",  # Outros
        30834: "c30834_outros",  # Outros
        30894: "c30894_outros",  # Outros
        32029: "c32029_outros",  # Outros
        30848: "q8_1_2_total_de_pessoas_que_atuam_nas_atividade",  # 8.1.2 Total de pessoas que atuam nas atividades de assistência à saúde prestadas no estabelecimento prisional
        30898: "c30898_total_de_pessoas_que_atuam_nas_atividade",  # 8.1.2 Total de pessoas que atuam nas atividades de assistência à saúde prestadas no estabelecimento prisional
        30855: "q8_1_2_1_desse_total_quantas_estao_afastadas_de_s",  # 8.1.2.1 Desse total, quantas estão afastadas de suas atividades, inclusive por motivo de saúde
        30899: "c30899_desse_total_quantas_estao_afastadas_de_s",  # 8.1.2.1 Desse total, quantas estão afastadas de suas atividades, inclusive por motivo de saúde
        30851: "q8_1_3_total_de_consultorios_medicos",  # 8.1.3 Total de consultórios médicos
        30901: "c30901_total_de_consultorios_medicos",  # 8.1.3 Total de consultórios médicos
        30856: "q8_1_4_total_de_medicos_clinicos",  # 8.1.4 Total de médicos clínicos
        30902: "c30902_total_de_medicos_clinicos",  # 8.1.4 Total de médicos clínicos
        30857: "q8_1_4_1_desse_total_quantos_estao_afastados_de_s",  # 8.1.4.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30903: "c30903_desse_total_quantos_estao_afastados_de_s",  # 8.1.4.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30858: "q8_1_4_2_presenca_de_medicos_clinicos",  # 8.1.4.2 Presença de médicos clínicos
        30904: "c30904_presenca_de_medicos_clinicos",  # 8.1.4.2 Presença de médicos clínicos
        30863: "q8_1_4_3_total_de_ppl_atendidas_por_medicos_clini",  # 8.1.4.3 Total de *PPL atendidas por médicos clínicos no período de referência
        30909: "c30909_total_de_ppl_atendidas_por_medicos_clini",  # 8.1.4.3 Total de *PPL atendidas por médicos clínicos no período de referência
        30910: "q8_1_5_total_de_medicos_ginecologistas_aplicave",  # 8.1.5 Total de médicos ginecologistas (aplicável aos estabelecimentos prisionais com destinação FEMININA ou AMBOS)
        30911: "c30911_total_de_medicos_ginecologistas_aplicave",  # 8.1.5 Total de médicos ginecologistas (aplicável aos estabelecimentos prisionais com destinação FEMININA ou AMBOS)
        30914: "q8_1_5_1_desse_total_quantos_estao_afastados_de_s",  # 8.1.5.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30915: "c30915_desse_total_quantos_estao_afastados_de_s",  # 8.1.5.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30918: "q8_1_5_2_presenca_de_medicos_ginecologistas",  # 8.1.5.2 Presença de médicos ginecologistas
        30923: "c30923_presenca_de_medicos_ginecologistas",  # 8.1.5.2 Presença de médicos ginecologistas
        30938: "q8_1_5_3_total_de_ppl_atendidas_por_medicos_ginec",  # 8.1.5.3 Total de *PPL atendidas por médicos ginecologistas no período de referência
        30939: "c30939_total_de_ppl_atendidas_por_medicos_ginec",  # 8.1.5.3 Total de *PPL atendidas por médicos ginecologistas no período de referência
        30942: "q8_1_6_total_de_medicos_psiquiatras",  # 8.1.6 Total de médicos psiquiatras
        30943: "c30943_total_de_medicos_psiquiatras",  # 8.1.6 Total de médicos psiquiatras
        30947: "q8_1_6_1_desse_total_quantos_estao_afastados_de_s",  # 8.1.6.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30948: "c30948_desse_total_quantos_estao_afastados_de_s",  # 8.1.6.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30966: "q8_1_6_2_presenca_de_medicos_psiquiatras",  # 8.1.6.2 Presença de médicos psiquiatras
        30973: "c30973_presenca_de_medicos_psiquiatras",  # 8.1.6.2 Presença de médicos psiquiatras
        30978: "q8_1_6_3_total_de_ppl_atendidas_por_medicos_psiqu",  # 8.1.6.3 Total de *PPL atendidas por médicos psiquiatras no período de referência
        30979: "c30979_total_de_ppl_atendidas_por_medicos_psiqu",  # 8.1.6.3 Total de *PPL atendidas por médicos psiquiatras no período de referência
        30982: "q8_1_7_total_de_enfermeiros",  # 8.1.7 Total de enfermeiros
        30983: "c30983_total_de_enfermeiros",  # 8.1.7 Total de enfermeiros
        30993: "q8_1_7_1_desse_total_quantos_estao_afastados_de_s",  # 8.1.7.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30994: "c30994_desse_total_quantos_estao_afastados_de_s",  # 8.1.7.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        30997: "q8_1_7_2_presenca_de_enfermeiros",  # 8.1.7.2 Presença de enfermeiros
        31002: "c31002_presenca_de_enfermeiros",  # 8.1.7.2 Presença de enfermeiros
        31007: "q8_1_7_3_total_de_ppl_atendidas_por_enfermeiros_n",  # 8.1.7.3 Total de *PPL atendidas por enfermeiros no período de referência
        31008: "c31008_total_de_ppl_atendidas_por_enfermeiros_n",  # 8.1.7.3 Total de *PPL atendidas por enfermeiros no período de referência
        31010: "q8_1_8_total_de_auxiliares_de_enfermagem",  # 8.1.8 Total de auxiliares de enfermagem
        31011: "c31011_total_de_auxiliares_de_enfermagem",  # 8.1.8 Total de auxiliares de enfermagem
        31012: "q8_1_8_1_desse_total_quantos_estao_afastados_de_s",  # 8.1.8.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        31013: "c31013_desse_total_quantos_estao_afastados_de_s",  # 8.1.8.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        31014: "q8_1_8_2_presenca_de_auxiliares_de_enfermagem",  # 8.1.8.2 Presença de auxiliares de enfermagem
        31019: "c31019_presenca_de_auxiliares_de_enfermagem",  # 8.1.8.2 Presença de auxiliares de enfermagem
        31024: "q8_1_8_3_total_de_ppl_atendidas_por_auxiliares_de",  # 8.1.8.3 Total de *PPL atendidas por auxiliares de enfermagem no período de referência
        31025: "c31025_total_de_ppl_atendidas_por_auxiliares_de",  # 8.1.8.3 Total de *PPL atendidas por auxiliares de enfermagem no período de referência
        31026: "ha_atendimento_medico_emergencial_24_hor",  # 8.2 Há atendimento médico emergencial 24 horas?
        31029: "ha_desfibrilador_no_estabelecimento_pris",  # 8.2.1 Há desfibrilador no estabelecimento prisional?
        31032: "quantos",  # 8.2.1.1 Quantos?
        31033: "quando_necessario_o_encaminhamento_para",  # 8.3 Quando necessário o encaminhamento para a rede de saúde local, há dificuldades para efetivação dessa medida?
        31037: "ausencia_de_veiculo_para_transporte",  # Ausência de veículo para transporte
        31038: "deficiencia_na_rede_de_saude_local",  # Deficiência na rede de saúde local
        31039: "insuficiencia_de_escolta",  # Insuficiência de escolta
        31040: "c31040_outras",  # Outras
        31041: "outras_dificuldades",  # Outras dificuldades
        31042: "ha_enfermaria",  # 8.4 Há enfermaria?
        31046: "q8_4_1_total_de_leitos_de_enfermaria",  # 8.4.1 Total de leitos de enfermaria
        31047: "c31047_total_de_leitos_de_enfermaria",  # 8.4.1 Total de leitos de enfermaria
        31048: "q8_4_1_1_desse_total_quantos_leitos_de_enfermaria",  # 8.4.1.1 Desse total, quantos leitos de enfermaria não estão em pleno funcionamento?
        31049: "c31049_desse_total_quantos_leitos_de_enfermaria",  # 8.4.1.1 Desse total, quantos leitos de enfermaria não estão em pleno funcionamento?
        31093: "ha_assistencia_odontologica",  # 8.5 Há assistência odontológica?
        31097: "q8_5_1_total_de_consultorios_odontologicos",  # 8.5.1 Total de consultórios odontológicos
        31098: "c31098_total_de_consultorios_odontologicos",  # 8.5.1 Total de consultórios odontológicos
        31099: "q8_5_1_1_desse_total_quantos_consultorios_odontol",  # 8.5.1.1 Desse total, quantos consultórios odontológicos não estão em pleno funcionamento?
        31100: "c31100_desse_total_quantos_consultorios_odontol",  # 8.5.1.1 Desse total, quantos consultórios odontológicos não estão em pleno funcionamento?
        31101: "q8_5_2_total_de_odontologos",  # 8.5.2 Total de odontólogos
        31102: "c31102_total_de_odontologos",  # 8.5.2 Total de odontólogos
        31103: "q8_5_2_1_desse_total_quantos_estao_afastados_de_s",  # 8.5.2.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        31104: "c31104_desse_total_quantos_estao_afastados_de_s",  # 8.5.2.1 Desse total, quantos estão afastados de suas atividades, inclusive por motivo de saúde
        31105: "q8_5_2_2_presenca_de_odontologos",  # 8.5.2.2 Presença de odontólogos
        31110: "c31110_presenca_de_odontologos",  # 8.5.2.2 Presença de odontólogos
        31115: "q8_5_2_3_total_de_ppl_atendidas_por_odontologos_n",  # 8.5.2.3 Total de *PPL atendidas por odontólogos no período de referência
        31116: "c31116_total_de_ppl_atendidas_por_odontologos_n",  # 8.5.2.3 Total de *PPL atendidas por odontólogos no período de referência
        31117: "os_presos_tem_acesso_a_exames_medicos_ne",  # 8.6 Os presos têm acesso a exames médicos necessários?
        31124: "q8_7_ha_unidade_materno_infantil",  # 8.7 Há unidade materno-infantil?
        31121: "c31121_ha_unidade_materno_infantil",  # 8.7 Há unidade materno-infantil?
        31127: "q8_8_ha_atendimento_pre_natal_as_ppl_gestante",  # 8.8 Há atendimento pré-natal às PPL gestantes?
        31130: "c31130_ha_atendimento_pre_natal_as_ppl_gestante",  # 8.8 Há atendimento pré-natal às PPL gestantes?
        31133: "e_garantida_a_aplicacao_de_vacina_as_ppl",  # 8.9 É garantida a aplicação de vacina às *PPL?
        31136: "ha_farmacia_no_estabelecimento_prisional",  # 8.10 Há farmácia no estabelecimento prisional?
        31139: "ha_assistencia_farmaceutica",  # 8.11 Há assistência farmacêutica?
        31142: "ha_distribuicao_de_medicamentos_de_uso_c",  # 8.12 Há distribuição de medicamentos de uso contínuo?
        31145: "ha_distribuicao_de_medicamentos_para_tra",  # 8.13 Há distribuição de medicamentos para tratamento de doenças infectocontagiosas e/ou sexualmente transmissíveis (inclusive AIDS e tuberculose)?
        31148: "ha_campanha_para_prevencao_de_doencas_in",  # 8.14 Há campanha para prevenção de doenças infectocontagiosas e/ou sexualmente transmissíveis (inclusive AIDS e tuberculose)?
        31151: "e_assegurado_o_acesso_a_tratamentos_de_s",  # 8.15 É assegurado o acesso a tratamentos de saúde específicos, incluindo, mas não se limitando, terapia hormonal, testagem e tratamento para HIV/TB e outras doenças infectocontagiosas, acompanhamento psicológico e psiquiátrico, especialmente voltados para a prevenção do suicídio e o tratamento de questões de saúde mental agravadas pela detenção?
        31154: "ha_distribuicao_de_preservativos",  # 8.16 Há distribuição de preservativos?
        31158: "as_ppl_sao_submetidas_a_exame_medico_ou",  # 8.17 As *PPL são submetidas a exame médico ou pericial antes de ingressarem no estabelecimento prisional?
        31161: "ha_prontuario_de_acompanhamento_a_saude",  # 8.18 Há prontuário de acompanhamento à saúde das *PPL?
        31164: "os_prontuarios_apresentam_historico_ante",  # 8.18.1 Os prontuários apresentam histórico anterior à chegada das *PPL ao estabelecimento prisional?
        31167: "os_prontuarios_de_saude_acompanham_as_pp",  # 8.18.2 Os prontuários de saúde acompanham as *PPL na movimentação entre estabelecimentos prisionais?
        31170: "qual_o_meio_utilizado_na_movimentacao_do",  # 8.18.2.1 Qual o meio utilizado na movimentação do prontuário de saúde?
        31174: "existe_equipe_habilitada_a_pnaisp_politi",  # 8.19 Existe equipe habilitada à PNAISP (Política Nacional de Atenção Integral à Saúde das Pessoas Privadas de Liberdade no Sistema Prisional) no estabelecimento prisional?
        30794: "ha_assistencia_juridica_e_gratuita_as_pp",  # 9.1 Há assistência jurídica e gratuita às *PPL?
        30802: "advocacia_particular",  # Advocacia particular
        30806: "defensoria_publica",  # Defensoria Pública
        30807: "nucleo_de_praticas_juridicas",  # Núcleo de Práticas Jurídicas
        30808: "c30808_outros",  # Outros
        30812: "c30812_outros",  # Outros
        30818: "parlatorio",  # Parlatório
        30819: "patio_do_banho_de_sol",  # Pátio do banho de sol
        30820: "sala_especifica",  # Sala específica
        30822: "c30822_outro_local",  # Outro local
        30824: "c30824_outro_local",  # Outro local
        30838: "ha_atendimento_de_servico_de_assistencia",  # 10.1 Há atendimento de serviço de assistência social no estabelecimento prisional?
        30841: "ha_profissionais_prestando_atendimento_d",  # 10.1.1 Há profissionais prestando atendimento de assistência social de forma permanente?
        30844: "quantos_assistentes_sociais_prestam_serv",  # 10.1.1.1 Quantos assistentes sociais prestam serviço permanente no estabelecimento prisional?
        30845: "ha_recintos_adequados_para_atividade_de",  # 10.1.2 Há recintos adequados para atividade de assistência social?
        30849: "q10_1_3_total_de_ppl_atendidas_no_periodo_de_ref",  # 10.1.3 Total de *PPL atendidas no período de referência
        30850: "total_familias_de_ppl_atendidas_no_perio",  # 10.1.4 Total famílias de *PPL atendidas no período de referência
        30864: "ha_algum_projeto_social_sendo_desenvolvi",  # 10.2 Há algum projeto social sendo desenvolvido no estabelecimento prisional?
        30867: "ha_algum_programa_ou_acao_de_assistencia",  # 10.3 Há algum programa ou ação de assistência social que atenda à PPL na ocasião da soltura?
        30870: "q10_4_o_estabelecimento_prisional_disponibiliz",  # 10.4 O estabelecimento prisional disponibiliza assistência psicológica?
        30874: "ha_psicologos_prestando_atendimento_de_f",  # 10.4.1 Há psicólogos prestando atendimento de forma permanente?
        30877: "quantos_psicologos_prestam_servico_perma",  # 10.4.1.1 Quantos psicólogos prestam serviço permanente no estabelecimento prisional?
        30878: "ha_recintos_adequados_para_atendimento_p",  # 10.4.2 Há recintos adequados para atendimento psicológico?
        30882: "q10_4_3_total_de_ppl_atendidas_no_periodo_de_ref",  # 10.4.3 Total de *PPL atendidas no período de referência
        30884: "ha_assistencia_religiosa",  # 11.1 Há assistência religiosa?
        30888: "ha_local_destinado_a_realizacao_de_culto",  # 11.1.1 Há local destinado à realização de cultos religiosos?
        30891: "as_ppl_sao_obrigadas_a_participar_das_at",  # 11.1.2 As *PPL são obrigadas a participar das atividades religiosas?
        30895: "as_ppl_tem_acesso_a_livros_religiosos",  # 11.2 As *PPL têm acesso a livros religiosos?
        31270: "ha_assistencia_educacional",  # 12.1 Há assistência educacional?
        31273: "e_oferecido_ensino_de_alfabetizacao",  # 12.1.1 É oferecido ensino de alfabetização?
        31276: "q12_1_1_1_total_de_ppl_matriculadas_no_periodo_de",  # 12.1.1.1 Total de *PPL matriculadas no período de referência
        31277: "q12_1_1_1_1_desse_total_quantas_abandonaram_os_estud",  # 12.1.1.1.1 Desse total, quantas abandonaram os estudos (antes da conclusão do ciclo)?
        31278: "q12_1_1_1_2_desse_total_quantas_estao_estudando_excl",  # 12.1.1.1.2 Desse total, quantas estão estudando, exclusivamente, na modalidade EaD (Ensino a Distância)?
        31279: "e_oferecido_ensino_fundamental",  # 12.1.2 É oferecido ensino fundamental?
        31282: "q12_1_2_1_total_de_ppl_matriculadas_no_periodo_de",  # 12.1.2.1 Total de *PPL matriculadas no período de referência
        31283: "q12_1_2_1_1_desse_total_quantas_abandonaram_os_estud",  # 12.1.2.1.1 Desse total, quantas abandonaram os estudos (antes da conclusão do ciclo)?
        31284: "q12_1_2_1_2_desse_total_quantas_estao_estudando_excl",  # 12.1.2.1.2 Desse total, quantas estão estudando, exclusivamente, na modalidade EaD (Ensino a Distância)?
        31285: "e_oferecido_ensino_medio",  # 12.1.3 É oferecido ensino médio?
        31288: "q12_1_3_1_total_de_ppl_matriculadas_no_periodo_de",  # 12.1.3.1 Total de *PPL matriculadas no período de referência
        31289: "q12_1_3_1_1_desse_total_quantas_abandonaram_os_estud",  # 12.1.3.1.1 Desse total, quantas abandonaram os estudos (antes da conclusão do ciclo)?
        31290: "q12_1_3_1_2_desse_total_quantas_estao_estudando_excl",  # 12.1.3.1.2 Desse total, quantas estão estudando, exclusivamente, na modalidade EaD (Ensino a Distância)?
        31291: "e_oferecido_ensino_profissionalizante",  # 12.1.4 É oferecido ensino profissionalizante?
        31294: "q12_1_4_1_total_de_ppl_matriculadas_no_periodo_de",  # 12.1.4.1 Total de *PPL matriculadas no período de referência
        31295: "q12_1_4_1_1_desse_total_quantas_abandonaram_os_estud",  # 12.1.4.1.1 Desse total, quantas abandonaram os estudos (antes da conclusão do ciclo)?
        31296: "q12_1_4_1_2_desse_total_quantas_estao_estudando_excl",  # 12.1.4.1.2 Desse total, quantas estão estudando, exclusivamente, na modalidade EaD (Ensino a Distância)?
        31297: "e_oferecido_ensino_superior",  # 12.1.5 É oferecido ensino superior?
        31300: "q12_1_5_1_total_de_ppl_matriculadas_no_periodo_de",  # 12.1.5.1 Total de *PPL matriculadas no período de referência
        31301: "q12_1_5_1_1_desse_total_quantas_abandonaram_os_estud",  # 12.1.5.1.1 Desse total, quantas abandonaram os estudos (antes da conclusão do ciclo)?
        31302: "q12_1_5_1_2_desse_total_quantas_estao_estudando_excl",  # 12.1.5.1.2 Desse total, quantas estão estudando, exclusivamente, na modalidade EaD (Ensino a Distância)?
        31303: "e_oferecido_ensino_de_pos_graduacao",  # 12.1.6 É oferecido ensino de pós-graduação?
        31306: "q12_1_6_1_total_de_ppl_matriculadas_no_periodo_de",  # 12.1.6.1 Total de *PPL matriculadas no período de referência
        31307: "q12_1_6_1_1_desse_total_quantas_abandonaram_os_estud",  # 12.1.6.1.1 Desse total, quantas abandonaram os estudos (antes da conclusão do ciclo)?
        31308: "q12_1_6_1_2_desse_total_quantas_estao_estudando_excl",  # 12.1.6.1.2 Desse total, quantas estão estudando, exclusivamente, na modalidade EaD (Ensino a Distância)?
        31309: "ha_local_adequado_para_ensino_consideran",  # 12.2 Há local adequado para ensino, considerando as condições de iluminação, acesso a água e banheiros, ventilação e mobiliário?
        31312: "ha_biblioteca_no_estabelecimento_prision",  # 12.3 Há biblioteca no estabelecimento prisional?
        31315: "e_garantido_o_livre_acesso_a_leitura",  # 12.4 É garantido o livre acesso à leitura?
        31318: "ha_regulamentacao_ou_programa_pedagogico",  # 12.5 Há regulamentação ou programa pedagógico de leitura para fins de remição?
        31321: "total_de_ppl_participaram_no_periodo_de",  # 12.5.1 Total de *PPL participaram no período de referência
        31322: "desse_total_quantas_concluiram_o_program",  # 12.5.1.1 Desse total, quantas concluíram o programa pedagógico?
        31323: "desse_total_quantas_abandonaram_o_progra",  # 12.5.1.2 Desse total, quantas abandonaram o programa pedagógico?
        31324: "sao_desenvolvidas_atividades_culturais_e",  # 12.6 São desenvolvidas atividades culturais e de lazer?
        31327: "sao_desenvolvidas_atividades_esportivas",  # 12.7 São desenvolvidas atividades esportivas?
        31330: "ha_espaco_para_a_pratica_esportiva",  # 12.8 Há espaço para a prática esportiva?
        30775: "q13_1_o_estabelecimento_prisional_disponibiliz",  # 13.1 O estabelecimento prisional disponibiliza vagas de trabalho às *PPL?
        30852: "q13_1_1_ha_ppl_desenvolvendo_trabalho_interno",  # 13.1.1 Há *PPL desenvolvendo trabalho interno?
        31182: "q13_1_1_1_quantas",  # 13.1.1.1 Quantas?
        32162: "c32162_ha_ppl_desenvolvendo_trabalho_interno",  # 13.1.1 Há *PPL desenvolvendo trabalho interno?
        31184: "c31184_quantas",  # 13.1.1.1 Quantas?
        31186: "q13_1_2_ha_ppl_desenvolvendo_trabalho_externo",  # 13.1.2 Há *PPL desenvolvendo trabalho externo?
        31192: "q13_1_2_1_quantas",  # 13.1.2.1 Quantas?
        31189: "c31189_ha_ppl_desenvolvendo_trabalho_externo",  # 13.1.2 Há *PPL desenvolvendo trabalho externo?
        31193: "c31193_quantas",  # 13.1.2.1 Quantas?
        31196: "q13_1_3_ha_ppl_desenvolvendo_trabalho_voluntario",  # 13.1.3 Há *PPL desenvolvendo trabalho voluntário?
        31202: "q13_1_3_1_quantas",  # 13.1.3.1 Quantas?
        31199: "c31199_ha_ppl_desenvolvendo_trabalho_voluntario",  # 13.1.3 Há *PPL desenvolvendo trabalho voluntário?
        31203: "c31203_quantas",  # 13.1.3.1 Quantas?
        31205: "q13_1_4_ha_ppl_desenvolvendo_trabalho_remunerado",  # 13.1.4 Há *PPL desenvolvendo trabalho remunerado?
        31211: "q13_1_4_1_quantas",  # 13.1.4.1 Quantas?
        31208: "c31208_ha_ppl_desenvolvendo_trabalho_remunerado",  # 13.1.4 Há *PPL desenvolvendo trabalho remunerado?
        31212: "c31212_quantas",  # 13.1.4.1 Quantas?
        31214: "q13_1_5_ha_jornada_de_trabalho_que_exceda_44_hor",  # 13.1.5 Há jornada de trabalho que exceda 44 horas semanais?
        31217: "c31217_ha_jornada_de_trabalho_que_exceda_44_hor",  # 13.1.5 Há jornada de trabalho que exceda 44 horas semanais?
        31220: "q13_1_6_ha_criterios_objetivos_para_alocacao_das",  # 13.1.6 Há critérios objetivos para alocação das *PPL nas respectivas vagas de trabalho?
        31223: "c31223_ha_criterios_objetivos_para_alocacao_das",  # 13.1.6 Há critérios objetivos para alocação das *PPL nas respectivas vagas de trabalho?
        31226: "q13_1_7_ha_cursos_ou_programas_profissionalizant",  # 13.1.7 Há cursos ou programas profissionalizantes e de qualificação técnica para o trabalho?
        31229: "c31229_ha_cursos_ou_programas_profissionalizant",  # 13.1.7 Há cursos ou programas profissionalizantes e de qualificação técnica para o trabalho?
        31232: "q13_1_8_ha_ppl_que_trabalham_e_que_estudam_conco",  # 13.1.8 Há *PPL que trabalham e que estudam concomitantemente?
        31238: "q13_1_8_1_quantas",  # 13.1.8.1 Quantas?
        31235: "c31235_ha_ppl_que_trabalham_e_que_estudam_conco",  # 13.1.8 Há *PPL que trabalham e que estudam concomitantemente?
        31253: "c31253_quantas",  # 13.1.8.1 Quantas?
        31255: "q13_1_9_idosos_e_pessoas_portadoras_de_deficienc",  # 13.1.9 Idosos e pessoas portadoras de deficiências exercem trabalho apropriado/adaptado?
        31258: "c31258_idosos_e_pessoas_portadoras_de_deficienc",  # 13.1.9 Idosos e pessoas portadoras de deficiências exercem trabalho apropriado/adaptado?
        31261: "q13_1_10_ha_oficinas_de_trabalho_no_estabelecimen",  # 13.1.10 Há oficinas de trabalho no estabelecimento prisional?
        31267: "q13_1_10_1_total_de_oficinas",  # 13.1.10.1 Total de oficinas
        31264: "c31264_ha_oficinas_de_trabalho_no_estabelecimen",  # 13.1.10 Há oficinas de trabalho no estabelecimento prisional?
        31268: "c31268_total_de_oficinas",  # 13.1.10.1 Total de oficinas
        31333: "q13_1_11_ha_industrias_instaladas_no_estabelecime",  # 13.1.11 Há indústrias instaladas no estabelecimento prisional?
        31339: "q13_1_11_1_total_de_industrias",  # 13.1.11.1 Total de indústrias
        31336: "c31336_ha_industrias_instaladas_no_estabelecime",  # 13.1.11 Há indústrias instaladas no estabelecimento prisional?
        31340: "c31340_total_de_industrias",  # 13.1.11.1 Total de indústrias
        31342: "q13_1_12_ha_parcerias_com_entidades_publicas_ou_p",  # 13.1.12 Há parcerias com entidades públicas ou privadas para oferecimento de vagas de trabalho?
        36698: "c36698_trabalho_interno",  # Trabalho Interno
        36699: "c36699_trabalho_externo",  # Trabalho Externo
        36700: "c36700_trabalho_voluntario",  # Trabalho Voluntário
        31396: "c31396_ha_parcerias_com_entidades_publicas_ou_p",  # 13.1.12 Há parcerias com entidades públicas ou privadas para oferecimento de vagas de trabalho? a
        36694: "c36694_trabalho_interno",  # Trabalho Interno
        36695: "c36695_trabalho_externo",  # Trabalho Externo
        36696: "c36696_trabalho_voluntario",  # Trabalho Voluntário
        31386: "q13_1_13_ha_registro_de_acidentes_de_trabalho_em",  # 13.1.13 Há registro de acidentes de trabalho em meio próprio pela administração do estabelecimento prisional?
        31389: "q13_1_13_1_total_de_registros_de_acidentes_de_traba",  # 13.1.13.1 Total de registros de acidentes de trabalho no período de referência - INTERNO
        31393: "q13_1_13_2_total_de_registros_de_acidentes_de_traba",  # 13.1.13.2 Total de registros de acidentes de trabalho no período de referência - EXTERNO
        31390: "c31390_ha_registro_de_acidentes_de_trabalho_em",  # 13.1.13 Há registro de acidentes de trabalho em meio próprio pela administração do estabelecimento prisional?
        31394: "c31394_total_de_registros_de_acidentes_de_traba",  # 13.1.13.1 Total de registros de acidentes de trabalho no período de referência - INTERNO
        31395: "c31395_total_de_registros_de_acidentes_de_traba",  # 13.1.13.2 Total de registros de acidentes de trabalho no período de referência - EXTERNO
        31993: "houve_registro_de_morte_no_periodo_de_re",  # 14.1 Houve registro de morte no período de referência?
        31994: "total_de_homens",  # 14.1.1 Total de HOMENS
        31996: "total_de_mulheres",  # 14.1.2 Total de MULHERES
        31997: "total_de_ppl_autodeclaradas_lgbti",  # 14.1.3 Total de *PPL autodeclaradas LGBTI+
        32023: "q14_2_1_1_homens",  # 14.2.1.1 HOMENS
        32024: "q14_2_1_2_mulheres",  # 14.2.1.2 MULHERES
        32025: "q14_2_1_3_autodeclaradas_lgbti",  # 14.2.1.3 autodeclaradas LGBTI+
        32027: "q14_2_2_1_homens",  # 14.2.2.1 HOMENS
        32028: "q14_2_2_2_mulheres",  # 14.2.2.2 MULHERES
        32030: "q14_2_2_3_autodeclaradas_lgbti",  # 14.2.2.3 autodeclaradas LGBTI+
        32074: "q14_2_3_1_homens",  # 14.2.3.1 HOMENS
        32075: "q14_2_3_2_mulheres",  # 14.2.3.2 MULHERES
        32076: "q14_2_3_3_autodeclaradas_lgbti",  # 14.2.3.3 autodeclaradas LGBTI+
        32078: "q14_2_4_1_homens",  # 14.2.4.1 HOMENS
        32079: "q14_2_4_2_mulheres",  # 14.2.4.2 MULHERES
        32080: "q14_2_4_3_autodeclaradas_lgbti",  # 14.2.4.3 autodeclaradas LGBTI+
        32082: "q14_2_5_1_homens",  # 14.2.5.1 HOMENS
        32083: "q14_2_5_2_mulheres",  # 14.2.5.2 MULHERES
        32084: "q14_2_5_3_autodeclaradas_lgbti",  # 14.2.5.3 autodeclaradas LGBTI+
        32087: "q14_3_1_1_homens",  # 14.3.1.1 HOMENS
        32088: "q14_3_1_2_mulheres",  # 14.3.1.2 MULHERES
        32089: "q14_3_1_3_autodeclaradas_lgbti",  # 14.3.1.3 autodeclaradas LGBTI+
        32091: "q14_3_2_1_homens",  # 14.3.2.1 HOMENS
        32092: "q14_3_2_2_mulheres",  # 14.3.2.2 MULHERES
        32093: "q14_3_2_3_autodeclaradas_lgbti",  # 14.3.2.3 autodeclaradas LGBTI+
        32095: "q14_3_3_1_homens",  # 14.3.3.1 HOMENS
        32096: "q14_3_3_2_mulheres",  # 14.3.3.2 MULHERES
        32097: "q14_3_3_3_autodeclaradas_lgbti",  # 14.3.3.3 autodeclaradas LGBTI+
        32099: "q14_3_4_1_homens",  # 14.3.4.1 HOMENS
        32100: "q14_3_4_2_mulheres",  # 14.3.4.2 MULHERES
        32101: "q14_3_4_3_autodeclaradas_lgbti",  # 14.3.4.3 autodeclaradas LGBTI+
        32103: "q14_3_5_1_homens",  # 14.3.5.1 HOMENS
        32104: "q14_3_5_2_mulheres",  # 14.3.5.2 MULHERES
        32105: "q14_3_5_3_autodeclaradas_lgbti",  # 14.3.5.3 autodeclaradas LGBTI+
        32108: "q14_4_1_1_homens",  # 14.4.1.1 HOMENS
        32109: "q14_4_1_2_mulheres",  # 14.4.1.2 MULHERES
        32110: "q14_4_1_3_autodeclaradas_lgbti",  # 14.4.1.3 autodeclaradas LGBTI+
        32112: "q14_4_2_1_homens",  # 14.4.2.1 HOMENS
        32113: "q14_4_2_2_mulheres",  # 14.4.2.2 MULHERES
        32114: "q14_4_2_3_autodeclaradas_lgbti",  # 14.4.2.3 autodeclaradas LGBTI+
        32116: "q14_4_3_1_homens",  # 14.4.3.1 HOMENS
        32117: "q14_4_3_2_mulheres",  # 14.4.3.2 MULHERES
        32118: "q14_4_3_3_autodeclaradas_lgbti",  # 14.4.3.3 autodeclaradas LGBTI+
        32120: "q14_4_4_1_homens",  # 14.4.4.1 HOMENS
        32121: "q14_4_4_2_mulheres",  # 14.4.4.2 MULHERES
        32122: "q14_4_4_3_autodeclaradas_lgbti",  # 14.4.4.3 autodeclaradas LGBTI+
        32124: "q14_4_5_1_homens",  # 14.4.5.1 HOMENS
        32125: "q14_4_5_2_mulheres",  # 14.4.5.2 MULHERES
        32126: "q14_4_5_3_autodeclaradas_lgbti",  # 14.4.5.3 autodeclaradas LGBTI+
        32127: "ha_fluxo_definido_para_comunicacao_notif",  # 14.5 Há fluxo definido para comunicação notificação compulsória dos casos de violência autoprovocada, incluindo tentativas de suicídio e a automutilação?
        32128: "quantos_casos_foram_registrados_no_perio",  # 14.5.1 Quantos casos foram registrados no período de referência?
        32129: "houve_registro_de_lesoes_corporais_no_pe",  # 14.6 Houve registro de lesões corporais no período de referência?
        32130: "quantos_casos_de_lesoes_corporais_foram",  # 14.6.1 Quantos casos de lesões corporais foram registrados no período de referência?
        32131: "houve_registro_de_tortura_contra_ppl_no",  # 14.7 Houve registro de tortura contra *PPL no período de referência?
        32132: "quantos_casos_de_tortura_contra_ppl_fora",  # 14.7.1 Quantos casos de tortura contra *PPL foram registrados no período de referência?
        32133: "houve_registro_de_maus_tratos_contra_ppl",  # 14.8 Houve registro de maus-tratos contra *PPL no período de referência?
        32134: "quantos_casos_de_maus_tratos_contra_ppl",  # 14.8.1 Quantos casos de maus-tratos contra *PPL foram registrados no período de referência?
        31793: "as_ppl_sao_cientificadas_das_normas_disc",  # 15.1 As *PPL são cientificadas das normas disciplinares no início da execução da pena?
        31794: "existe_comissao_tecnica_de_classificacao",  # 15.2 Existe Comissão Técnica de Classificação das *PPL?
        31795: "ha_registro_de_imposicao_de_sancao_disci",  # 15.3 Há registro de imposição de sanção disciplinar no período de referência?
        31796: "ha_sistema_de_registro_e_controle_de_oco",  # 15.4 Há sistema de registro e controle de ocorrências e sanções aplicadas?
        31797: "numero_de_procedimentos_concluidos_no_pr",  # 15.4.1 Número de procedimentos concluídos no prazo legal
        31798: "numero_de_procedimentos_em_que_houve_dec",  # 15.4.2 Número de procedimentos em que houve decurso de prazo para apuração
        31801: "e_feita_a_comunicacao_do_isolamento_prev",  # 15.4.3 É feita a comunicação do isolamento preventivo ao Juiz da execução?
        31802: "o_preso_cumpre_o_isolamento_mantendo_a_p",  # 15.4.4 O preso cumpre o isolamento mantendo a posse de todos os seus objetos pessoais?
        31803: "foram_executadas_sancoes_coletivas_no_pe",  # 15.5 Foram executadas sanções coletivas no período de referência?
        31804: "total_de_ppl_em_regime_disciplinar_difer",  # 15.6 Total de *PPL em Regime Disciplinar Diferenciado (RDD) no período de referência
        31805: "total_de_sancoes_de_isolamento_aplicadas",  # 15.7 Total de sanções de isolamento aplicadas no período de referência
        31806: "houve_fugas_no_periodo_de_referencia",  # 15.8 Houve fugas no período de referência?
        31807: "quantas_fugas_foram_registradas",  # 15.8.1 Quantas fugas foram registradas?
        31808: "desse_total_quantas_se_deram_pelo_nao_re",  # 15.8.1.1 Desse total, quantas se deram pelo não retorno de saída autorizada?
        31809: "houve_movimento_coletivo_para_subverter",  # 15.9 Houve movimento coletivo para subverter a ordem ou a disciplina no período de referência?
        31810: "quantos_ocorreram",  # 15.9.1 Quantos ocorreram?
        31811: "houve_falta_grave_individual_no_periodo",  # 15.10 Houve falta grave individual no período de referência?
        31812: "quantas_ocorreram",  # 15.10.1 Quantas ocorreram?
        31813: "houve_apreensao_de_armas_no_periodo_de_r",  # 15.11 Houve apreensão de armas no período de referência?
        31818: "q15_11_1_1_1_ppl",  # 15.11.1.1.1 *PPL
        31819: "q15_11_1_1_2_visitantes",  # 15.11.1.1.2 Visitantes
        31821: "q15_11_1_2_1_ppl",  # 15.11.1.2.1 * PPL
        31822: "q15_11_1_2_2_visitantes",  # 15.11.1.2.2 Visitantes
        31825: "q15_11_1_3_1_1_ppl",  # 15.11.1.3.1.1 *PPL
        31826: "q15_11_1_3_1_2_visitantes",  # 15.11.1.3.1.2 Visitantes
        31828: "q15_11_1_3_2_1_ppl",  # 15.11.1.3.2.1 * PPL
        31829: "q15_11_1_3_2_2_visitantes",  # 15.11.1.3.2.2 Visitantes
        31832: "q15_11_1_4_1_1_ppl",  # 15.11.1.4.1.1 * PPL
        31833: "q15_11_1_4_1_2_visitantes",  # 15.11.1.4.1.2 Visitantes
        31835: "q15_11_1_4_2_1_ppl",  # 15.11.1.4.2.1 *PPL
        31836: "q15_11_1_4_2_2_visitantes",  # 15.11.1.4.2.2 Visitantes
        31839: "q15_11_1_5_1_1_ppl",  # 15.11.1.5.1.1 *PPL
        31840: "q15_11_1_5_1_2_visitantes",  # 15.11.1.5.1.2 Visitantes
        31842: "q15_11_1_5_2_1_ppl",  # 15.11.1.5.2.1 *PPL
        31843: "q15_11_1_5_2_2_visitantes",  # 15.11.1.5.2.2 Visitantes
        31845: "tipo_da_arma_apreendida",  # Tipo da arma apreendida
        31853: "houve_apreensao_de_aparelhos_de_comunica",  # 15.12 Houve apreensão de aparelhos de comunicação e/ou acessórios no período de referência?
        31858: "q15_12_1_1_1_ppl",  # 15.12.1.1.1 *PPL
        31859: "q15_12_1_1_2_visitantes",  # 15.12.1.1.2 Visitantes
        31861: "q15_12_1_2_1_ppl",  # 15.12.1.2.1 * PPL
        31862: "q15_12_1_2_2_visitantes",  # 15.12.1.2.2 Visitantes
        31865: "q15_12_1_3_1_1_ppl",  # 15.12.1.3.1.1 *PPL
        31866: "q15_12_1_3_1_2_visitantes",  # 15.12.1.3.1.2 Visitantes
        31868: "q15_12_1_3_2_1_ppl",  # 15.12.1.3.2.1 *PPL
        31869: "q15_12_1_3_2_2_visitantes",  # 15.12.1.3.2.2 Visitantes
        31886: "houve_apreensao_de_drogas_no_periodo_de",  # 15.13 Houve apreensão de drogas no período de referência?
        31887: "numero_de_ocorrencias_de_apreensao_de_dr",  # 15.13.1 Número de ocorrências de apreensão de drogas no período de referência
        31890: "q15_13_1_1_1_1_cocaina",  # 15.13.1.1.1.1 Cocaína
        31891: "q15_13_1_1_1_2_crack",  # 15.13.1.1.1.2 Crack
        31892: "q15_13_1_1_1_3_maconha",  # 15.13.1.1.1.3 Maconha
        31893: "q15_13_1_1_1_4_outros_tipos_de_drogas",  # 15.13.1.1.1.4 Outros tipos de Drogas
        31895: "q15_13_1_1_2_1_cocaina",  # 15.13.1.1.2.1 Cocaína
        31896: "q15_13_1_1_2_2_crack",  # 15.13.1.1.2.2 Crack
        31897: "q15_13_1_1_2_3_maconha",  # 15.13.1.1.2.3 Maconha
        31898: "q15_13_1_1_2_4_outros_tipos_de_drogas",  # 15.13.1.1.2.4 Outros tipos de Drogas
        31932: "q15_13_1_2_1_1_cocaina",  # 15.13.1.2.1.1 Cocaína
        31933: "q15_13_1_2_1_2_crack",  # 15.13.1.2.1.2 Crack
        31934: "q15_13_1_2_1_3_maconha",  # 15.13.1.2.1.3 Maconha
        31935: "q15_13_1_2_1_4_outros_tipos_de_drogas",  # 15.13.1.2.1.4 Outros tipos de Drogas
        31937: "q15_13_1_2_2_1_cocaina",  # 15.13.1.2.2.1 Cocaína
        31938: "q15_13_1_2_2_2_crack",  # 15.13.1.2.2.2 Crack
        31939: "q15_13_1_2_2_3_maconha",  # 15.13.1.2.2.3 Maconha
        31940: "q15_13_1_2_2_4_outros_tipos_de_drogas",  # 15.13.1.2.2.4 Outros tipos de Drogas
        31957: "q15_13_1_3_1_1_cocaina",  # 15.13.1.3.1.1 Cocaína
        31958: "q15_13_1_3_1_2_crack",  # 15.13.1.3.1.2 Crack
        31961: "q15_13_1_3_1_3_maconha",  # 15.13.1.3.1.3 Maconha
        31963: "q15_13_1_3_1_4_outros_tipos_de_drogas",  # 15.13.1.3.1.4 Outros tipos de Drogas
        31965: "q15_13_1_3_2_1_cocaina",  # 15.13.1.3.2.1 Cocaína
        31966: "q15_13_1_3_2_2_crack",  # 15.13.1.3.2.2 Crack
        31967: "q15_13_1_3_2_3_maconha",  # 15.13.1.3.2.3 Maconha
        31968: "q15_13_1_3_2_4_outros_tipos_de_drogas",  # 15.13.1.3.2.4 Outros tipos de Drogas
        31972: "q15_13_1_4_1_1_cocaina",  # 15.13.1.4.1.1 Cocaína
        31973: "q15_13_1_4_1_2_crack",  # 15.13.1.4.1.2 Crack
        31974: "q15_13_1_4_1_3_maconha",  # 15.13.1.4.1.3 Maconha
        31975: "q15_13_1_4_1_4_outros_tipos_de_drogas",  # 15.13.1.4.1.4 Outros tipos de Drogas
        31977: "q15_13_1_4_2_1_cocaina",  # 15.13.1.4.2.1 Cocaína
        31978: "q15_13_1_4_2_2_crack",  # 15.13.1.4.2.2 Crack
        31979: "q15_13_1_4_2_3_maconha",  # 15.13.1.4.2.3 Maconha
        31980: "q15_13_1_4_2_4_outros_tipos_de_drogas",  # 15.13.1.4.2.4 Outros tipos de Drogas
        31403: "e_garantida_a_visitacao_social",  # 16.1 É garantida a visitação social?
        31407: "por_quantos_dias_a_visita_social_esta_su",  # 16.1.1 Por quantos dias a visita social está suspensa?
        31408: "q16_1_2_e_solicitado_a_declaracao_de_antecedente",  # 16.1.2 É solicitado a declaração de antecedentes criminais do(a) visitante?
        31411: "ha_controle_e_registro_da_visita_social",  # 16.1.3 Há controle e registro da visita social?
        31414: "duracao_da_visita_social_em_minutos",  # 16.1.4 Duração da visita social (em minutos)
        31433: "periodicidade_da_visita_social_em_no_de",  # 16.1.5 Periodicidade da visita social (em nº de dias por mês)
        31437: "em_area_especifica_de_visitacao",  # Em área específica de visitação
        31438: "c31438_nas_celas_ou_corredores",  # Nas celas ou corredores
        31439: "c31439_no_patio_do_banho_de_sol",  # No pátio do banho de sol
        31442: "c31442_outro_local",  # Outro local
        32213: "c32213_local",  # Local
        31443: "ha_visita_social_por_meio_de_videoconfer",  # 16.1.7 Há visita social por meio de videoconferência?
        31447: "em_dias_ou_horarios_especificos_diferent",  # Em dias ou horários específicos diferentes do fixado para visita íntima
        31448: "em_espaco_especifico_adaptado_e_ludico",  # Em espaço específico, adaptado e lúdico
        31449: "na_presenca_de_responsavel_legal",  # Na presença de responsável legal
        31450: "nao_existe_diferenciacao",  # Não existe diferenciação
        31451: "ha_visitacao_intima",  # 16.2 Há visitação íntima?
        31455: "por_quantos_dias_a_visita_intima_esta_su",  # 16.2.1 Por quantos dias a visita íntima está suspensa?
        31456: "q16_2_2_e_solicitado_a_declaracao_de_antecedente",  # 16.2.2 É solicitado a declaração de antecedentes criminais do(a) visitante íntimo(a)?
        31461: "ha_controle_e_registro_da_visita_intima",  # 16.2.3 Há controle e registro da visita íntima?
        31466: "duracao_da_visita_intima_em_minutos",  # 16.2.4 Duração da visita íntima (em minutos)
        31467: "periodicidade_da_visita_intima_em_no_de",  # 16.2.5 Periodicidade da visita íntima (em nº de dias por mês)
        31469: "em_area_especifica_de_visita_intima",  # Em área específica de visita íntima
        31471: "c31471_nas_celas_ou_corredores",  # Nas celas ou corredores
        31472: "c31472_no_patio_do_banho_de_sol",  # No pátio do banho de sol
        31474: "c31474_outro_local",  # Outro local
        32212: "c32212_local",  # Local
        31517: "o_recebimento_de_visita_intima_e_regulam",  # 16.2.7 O recebimento de visita íntima é regulamentado?
        31520: "sao_permitidas_visitas_intimas_as_ppl_au",  # 16.2.8 São permitidas visitas íntimas às *PPL autodeclaradas LGBTI+?
        31525: "da_ppl",  # Da *PPL
        31526: "do_a_visitante",  # Do(a) Visitante
        31527: "de_ambos",  # De Ambos
        31528: "de_nenhum_a",  # De Nenhum(a)
        31536: "ha_revista_dos_visitantes",  # 17.1 Há revista dos visitantes?
        31539: "a_revista_e_realizada_por_agente_do_mesm",  # 17.1.1 A revista é realizada por agente do mesmo sexo?
        31542: "a_revista_em_criancas_e_adolescentes_e_a",  # 17.1.2 A revista em crianças e adolescentes é acompanhada por responsável?
        31545: "a_revista_e_realizada_com_auxilio_de_equ",  # 17.1.3 A revista é realizada com auxílio de equipamentos eletrônicos (detectores de metais, scanners etc.)
        31548: "os_equipamentos_eletronicos_de_auxilio_a",  # 17.1.3.1 Os equipamentos eletrônicos de auxílio a revista estão em pleno funcionamento?
        31552: "ha_revista_intima_dos_visitantes",  # 17.1.4 Há revista íntima dos visitantes?
        31556: "ha_ppl_submetidas_a_medida_de_seguranca",  # 18.1 Há *PPL submetidas a medida de segurança?
        31559: "q18_1_1_quantas",  # 18.1.1 Quantas?
        31560: "desse_total_quantas_cumprem_medida_de_in",  # 18.1.1.1 Desse total, quantas cumprem medida de internação?
        31561: "desse_total_quantas_cumprem_medida_de_tr",  # 18.1.1.2 Desse total, quantas cumprem medida de tratamento ambulatorial?
        31562: "desse_total_quantas_apresentam_pericias",  # 18.1.1.3 Desse total, quantas apresentam perícias com prazo vencido?
        31563: "desse_total_quantas_tiveram_a_cessacao_d",  # 18.1.1.4 Desse total, quantas tiveram a cessação de periculosidade sem a correspondente desinternação judicial?
        31493: "e_possibilitada_as_ppl_audiencia_especia",  # 19.1 É possibilitada às *PPL audiência especial com o(a) diretor(a) do estabelecimento prisional?
        31494: "e_possibilitado_aos_oficiais_de_justica",  # 19.2 É possibilitado aos oficiais de justiça ter acesso direto às *PPL?
        31495: "ha_realizacao_de_audiencia_judicial_por",  # 19.3 Há realização de audiência judicial por meio de videoconferência?
        31496: "ha_reducao_do_efetivo_de_servidores_dura",  # 19.4 Há redução do efetivo de servidores durante finais de semana e feriados?
        31497: "servidores_da_area_administrativa",  # 19.4.1 Servidores da Área Administrativa?
        31498: "servidores_da_area_de_educacao",  # 19.4.2 Servidores da Área de Educação?
        31499: "servidores_da_area_de_saude",  # 19.4.3 Servidores da Área de Saúde?
        31500: "servidores_da_area_de_seguranca",  # 19.4.4 Servidores da Área de Segurança?
        31501: "e_permitido_as_ppl_acesso_a_meios_de_inf",  # 19.5 É permitido às *PPL acesso a meios de informação (TV, rádio, jornal, revista etc.)?
        31502: "e_permitido_as_ppl_o_envio_e_o_recebimen",  # 19.6 É permitido às *PPL o envio e o recebimento de correspondência externa escrita?
        31503: "ha_possibilidade_das_ppl_fazerem_ligacoe",  # 19.7 Há possibilidade das *PPL fazerem ligações telefônicas?
        31504: "o_estabelecimento_prisional_possui_acess",  # 19.8 O estabelecimento prisional possui acesso à internet?
        31505: "as_ppl_recebem_o_atestado_de_pena_a_cump",  # 19.9 As *PPL recebem o atestado de pena a cumprir?
        31506: "periodicidade_de_disponibilizacao_do_ate",  # 19.9.1 Periodicidade de disponibilização do atestado de pena a cumprir?
        31512: "e_garantido_as_ppl_em_prisao_provisoria",  # 19.10 É garantido às *PPL em prisão provisória o exercício do direito de voto?
        31513: "as_ppl_tem_seus_documentos_pessoais_sob",  # 19.11 As *PPL têm seus documentos pessoais sob custódia da administração do estabelecimento prisional?
        31514: "a_direcao_do_estabelecimento_prisional_a",  # 19.12 A direção do estabelecimento prisional adota providências para expedição de documentos de Identificação dos presos (RG, certidão de nascimento, CPF, retificação de registro civil etc.)?
        31515: "ha_iluminacao_natural_nas_celas",  # 19.13 Há iluminação natural nas celas?
        31516: "ha_ventilacao_natural_nas_celas",  # 19.14 Há ventilação natural nas celas?
        32214: "total_de_tempo_diario_que_as_ppl_ficam_d",  # 19.15 Total de tempo diário que as *PPL ficam dentro das celas: (Informe valores entre 00:00 e 24:00 horas)
        31530: "ha_espaco_para_o_banho_de_sol",  # 19.16 Há espaço para o banho de sol?
        31531: "ha_rodizio_para_o_banho_de_sol_por_ala_p",  # 19.16.1 Há rodízio para o banho de sol por ala/pavilhão?
        32493: "total_de_tempo_diario_que_as_ppl_ficam_n",  # 19.16.2 Total de tempo diário que as *PPL ficam no banho de sol? (Informe valores entre 00:00 e 24:00 horas)
        32499: "total_de_tempo_diario_de_atividades_educ",  # 19.17 Total de tempo diário de atividades educacionais: (Informe valores entre 00:00 e 24:00 horas)
        32500: "total_de_tempo_diario_de_atividades_reli",  # 19.18 Total de tempo diário de atividades religiosas: (Informe valores entre 00:00 e 24:00 horas)
        32501: "total_de_tempo_diario_de_atividades_espo",  # 19.19 Total de tempo diário de atividades esportivas: (Informe valores entre 00:00 e 24:00 horas)
        31566: "q20_1_1_1_manha",  # 20.1.1.1 Manhã
        31567: "q20_1_1_2_tarde",  # 20.1.1.2 Tarde
        31568: "q20_1_1_3_noite",  # 20.1.1.3 Noite
        31570: "q20_1_2_1_manha",  # 20.1.2.1 Manhã
        31571: "q20_1_2_2_tarde",  # 20.1.2.2 Tarde
        31572: "q20_1_2_3_noite",  # 20.1.2.3 Noite
        31574: "as_escalas_de_trabalho_dos_policiais_pen",  # 20.2 As escalas de trabalho dos policiais penais e pessoal de segurança são respeitadas?
        31577: "ha_utilizacao_de_uniformes_por_policiais",  # 20.3 Há utilização de uniformes por policiais penais e pessoal de segurança?
        31581: "alojamento",  # Alojamento
        31582: "refeitorio",  # Refeitório
        31583: "vestiario",  # Vestiário
        31586: "c31586_policia_civil",  # Polícia Civil
        31587: "c31587_policia_militar",  # Polícia Militar
        31588: "c31588_policia_penal",  # Polícia Penal
        31589: "c31589_terceirizado",  # Terceirizado
        31590: "c31590_outros",  # Outros
        31611: "c31611_outros",  # Outros
        31593: "alarmes",  # Alarmes
        31594: "algemas",  # Algemas
        31595: "armas_com_municao_letal",  # Armas com munição letal
        31596: "armas_com_municao_menos_letal",  # Armas com munição menos letal
        31597: "cacetete_ou_tonfa",  # Cacetete ou Tonfa
        31598: "gas_de_pimenta_ou_lacrimogenio",  # Gás de Pimenta ou Lacrimogênio
        31599: "radio_comunicador",  # Rádio Comunicador
        31600: "c31600_outros",  # Outros
        31610: "c31610_outros",  # Outros
        31603: "c31603_policia_civil",  # Polícia Civil
        31604: "c31604_policia_militar",  # Polícia Militar
        31605: "c31605_policia_penal",  # Polícia Penal
        31606: "c31606_terceirizado",  # Terceirizado
        31607: "c31607_outros",  # Outros
        31609: "c31609_outros",  # Outros
        31613: "c31613_policia_civil",  # Polícia Civil
        31614: "c31614_policia_militar",  # Polícia Militar
        31615: "c31615_policia_penal",  # Polícia Penal
        31616: "c31616_terceirizado",  # Terceirizado
        31617: "c31617_outros",  # Outros
        31618: "c31618_outros",  # Outros
        31619: "existe_grupo_de_intervencao_especial_a_d",  # 20.9 Existe grupo de intervenção especial à disposição do estabelecimento prisional?
        31622: "existem_equipamentos_eletronicos_para_o",  # 20.10 Existem equipamentos eletrônicos para o Controle de Entrada no estabelecimento prisional?
        31625: "os_equipamentos_eletronicos_para_o_contr",  # 20.10.1 Os equipamentos eletrônicos para o Controle de Entrada estão em pleno funcionamento?
        31630: "banco_detector_de_metal",  # Banco detector de metal
        31631: "body_scanner",  # Body Scanner
        31632: "espectometro",  # Espectômetro
        31633: "portal_detector_de_metal",  # Portal detector de metal
        31634: "raio_x",  # Raio-X
        31635: "raquete_detectora_de_metal",  # Raquete detectora de metal
        31636: "c31636_outros",  # Outros
        31637: "c31637_outros",  # Outros
        31639: "q20_12_o_estabelecimento_prisional_possui_siste",  # 20.12 O estabelecimento prisional possui sistema de monitoramento por vídeo?
        31642: "o_sistema_de_monitoramento_de_video_esta",  # 20.12.1 O sistema de monitoramento de vídeo está em pleno funcionamento?
        31647: "area_da_portaria",  # Área da portaria
        31648: "area_de_cercas_e_ou_muralhas",  # Área de cercas e/ou muralhas
        31649: "area_destinada_ao_convivio",  # Área destinada ao convívio
        31650: "area_destinada_as_revistas",  # Área destinada às revistas
        31651: "area_dos_pavilhoes_e_vivencias",  # Área dos pavilhões e vivências
        31652: "c31652_outros",  # Outros
        31653: "c31653_outros",  # Outros
        31656: "classificacao_da_qualidade_da_imagem_uti",  # 20.12.3 Classificação da qualidade da imagem (Utilize a escala “1 a 5”, onde “1” é baixíssima qualidade e “5” é alta qualidade)
        31657: "q20_13_o_estabelecimento_prisional_possui_siste",  # 20.13 O estabelecimento prisional possui sistema de backup de imagem?
        31693: "o_sistema_de_backup_de_imagem_esta_em_pl",  # 20.13.1 O sistema de backup de imagem está em pleno funcionamento?
        31697: "tempo_total_em_no_de_dias_do_armazenamen",  # 20.13.2 Tempo total, em nº de dias, do armazenamento das imagens
        31699: "midia_fisica",  # Mídia física
        31700: "nuvem",  # “Nuvem”
        31701: "servidor_remoto",  # Servidor remoto
        31702: "c31702_outras_formas",  # Outras formas
        31703: "c31703_outras_formas",  # Outras Formas
        31704: "o_acesso_ao_sistema_de_armazenamento_de",  # 20.13.4 O acesso ao sistema de armazenamento de imagens é franqueado ao membro do Ministério Público?
        31707: "ha_previsao_de_remessa_de_copia_das_imag",  # 20.13.5 Há previsão de remessa de cópia das imagens ao Ministério Público?
        31710: "o_estabelecimento_prisional_possui_gerad",  # 20.13.6 O estabelecimento prisional possui gerador de energia e/ou nobreak para manutenção do sistema de armazenamento de imagens?
        31715: "c31715_alimentacao",  # Alimentação
        31716: "c31716_assistencia_a_saude",  # Assistência à Saúde
        31717: "c31717_assistencia_educacional",  # Assistência Educacional
        31718: "c31718_assistencia_juridica",  # Assistência Jurídica
        31719: "assistencia_psicossocial",  # Assistência Psicossocial
        31720: "assistencia_religiosa",  # Assistência Religiosa
        31721: "banho_de_sol",  # Banho de sol
        31722: "instalacoes",  # Instalações
        31723: "lazer_e_esporte",  # Lazer e esporte
        31724: "maus_tratos_e_ou_tortura",  # Maus-tratos e/ou Tortura
        31726: "vagas_de_trabalho",  # Vagas de trabalho
        31727: "visita_intima",  # Visita íntima
        31728: "visita_social",  # Visita social
        31729: "superlotacao",  # Superlotação
        31730: "c31730_outros",  # Outros
        31731: "c31731_outros",  # Outros
        32551: "no_caso_de_maus_tratos_e_ou_tortura_ha_i",  # 21.1.1 No caso de maus-tratos e/ou tortura, há indícios visíveis dos fatos relatados?
        32538: "cancelamento_de_visita_entrada_de_grupos",  # Cancelamento de visita, entrada de grupos especiais de intervenção, ou outras movimentações atípicas nas datas dos eventos
        32539: "ferimentos_no_corpo",  # Ferimentos no corpo
        32540: "ocultacao_da_identificacao_pessoal_dos_s",  # Ocultação da identificação pessoal dos servidores
        32541: "locais_inadequados_para_o_cumprimento_de",  # Locais inadequados para o cumprimento de sanções disciplinares
        32542: "marcas_de_projeteis_nas_celas_e_ou_outro",  # Marcas de projéteis nas celas e/ou outros ambientes
        32543: "o_estabelecimento_prisional_possui_locai",  # O estabelecimento prisional possui locais característicos como ambientes de castigo (sem colchão, sem sanitário, sem iluminação, sem ventilação, sem higiene ou insalubres)
        32544: "relatos_identicos_em_diferentes_alas",  # Relatos idênticos em diferentes alas
        32545: "c32545_outros",  # Outros
        32546: "c32546_outros",  # Outros
        31773: "foi_relatado_o_uso_de_celas_escuras_como",  # 21.2 Foi relatado o uso de celas escuras como sanção disciplinar?
        31776: "o_membro_do_ministerio_publico_localizou",  # 21.2.1 O membro do Ministério Público localizou a cela escura mencionada?
        31779: "ha_relatos_de_suspensao_do_direito_de_vi",  # 21.3 Há relatos de suspensão do direito de visita como medida de sanção coletiva?
        31786: "c31786_discorra_em_linhas_gerais_o_resumo_da_en",  # Discorra, em linhas gerais, o resumo da entrevista individual
        31784: "c31784_discorra_em_linhas_gerais_o_resumo_da_en",  # Discorra, em linhas gerais, o resumo da entrevista individual
        31788: "c31788_discorra_em_linhas_gerais_o_resumo_da_en",  # Discorra, em linhas gerais, o resumo da entrevista individual
        31734: "carencia_de_equipamentos_e_materiais",  # Carência de equipamentos e materiais
        31735: "carencia_de_pessoal",  # Carência de pessoal
        31736: "carencia_de_treinamento",  # Carência de treinamento
        31737: "condicoes_de_trabalho",  # Condições de trabalho
        31738: "estrutura_fisica_do_estabelecimento_pris",  # Estrutura física do estabelecimento prisional
        31739: "sobrecarga_de_atividades",  # Sobrecarga de atividades
        31740: "c31740_outros",  # Outros
        31741: "c31741_outros",  # Outros
        31744: "c31744_discorra_em_linhas_gerais_o_resumo_da_en",  # Discorra, em linhas gerais, o resumo da entrevista individual
        31746: "c31746_discorra_em_linhas_gerais_o_resumo_da_en",  # Discorra, em linhas gerais, o resumo da entrevista individual
        31748: "c31748_discorra_em_linhas_gerais_o_resumo_da_en",  # Discorra, em linhas gerais, o resumo da entrevista individual
        31750: "foram_identificados_pontos_positivos",  # 23.1 Foram identificados Pontos Positivos?
        31754: "c31754_ao_perfil_do_estabelecimento_prisional_s",  # AO PERFIL DO ESTABELECIMENTO PRISIONAL (SEÇÃO II)
        31755: "c31755_a_capacidade_de_ocupacao_secao_iii",  # À CAPACIDADE DE OCUPAÇÃO (SEÇÃO III)
        31756: "c31756_ao_perfil_da_populacao_prisional_secao_i",  # AO PERFIL DA POPULAÇÃO PRISIONAL (SEÇÃO IV)
        31757: "c31757_a_separacao_secao_v",  # À SEPARAÇÃO (SEÇÃO V)
        31758: "c31758_a_assistencia_material_secao_vi",  # À ASSISTÊNCIA MATERIAL (SEÇÃO VI)
        31870: "c31870_a_alimentacao_secao_vii",  # À ALIMENTAÇÃO (SEÇÃO VII)
        31871: "c31871_a_assistencia_a_saude_secao_viii",  # À ASSISTÊNCIA À SAÚDE (SEÇÃO VIII)
        31872: "c31872_a_assistencia_juridica_secao_ix",  # À ASSISTÊNCIA JURÍDICA (SEÇÃO IX)
        31873: "c31873_a_assistencia_psicossocial_secao_x",  # À ASSISTÊNCIA PSICOSSOCIAL (SEÇÃO X)
        31874: "c31874_a_assistencia_religiosa_secao_xi",  # À ASSISTÊNCIA RELIGIOSA (SEÇÃO XI)
        31875: "c31875_a_assistencia_educacional_secao_xii",  # À ASSISTÊNCIA EDUCACIONAL (SEÇÃO XII)
        31876: "c31876_ao_trabalho_secao_xiii",  # AO TRABALHO (SEÇÃO XIII)
        31877: "c31877_a_integridade_fisica_secao_xiv",  # À INTEGRIDADE FÍSICA (SEÇÃO XIV)
        31878: "c31878_a_disciplina_secao_xv",  # À DISCIPLINA (SEÇÃO XV)
        31879: "c31879_as_visitas_secao_xvi",  # ÀS VISITAS (SEÇÃO XVI)
        31880: "c31880_a_revista_secao_xvii",  # À REVISTA (SEÇÃO XVII)
        31881: "c31881_as_medidas_de_seguranca_secao_xviii",  # ÀS MEDIDAS DE SEGURANÇA (SEÇÃO XVIII)
        31882: "c31882_a_organizacao_administrativa_secao_xix",  # À ORGANIZAÇÃO ADMINISTRATIVA (SEÇÃO XIX)
        31883: "c31883_aos_policiais_penais_e_seguranca_do_esta",  # AOS POLICIAIS PENAIS E SEGURANÇA DO ESTABELECIMENTO PRISIONAL (SEÇÃO XX)
        31884: "c31884_outros",  # Outros
        31885: "c31885_outros",  # Outros
        31900: "c31900_discorra_em_linhas_gerais_o_resumo_dos_p",  # Discorra, em linhas gerais, o resumo dos PONTOS POSITIVOS
        31904: "foram_identificados_pontos_negativos",  # 23.2 Foram identificados Pontos Negativos?
        31908: "c31908_ao_perfil_do_estabelecimento_prisional_s",  # AO PERFIL DO ESTABELECIMENTO PRISIONAL (SEÇÃO II)
        31909: "c31909_a_capacidade_de_ocupacao_secao_iii",  # À CAPACIDADE DE OCUPAÇÃO (SEÇÃO III)
        31910: "c31910_ao_perfil_da_populacao_prisional_secao_i",  # AO PERFIL DA POPULAÇÃO PRISIONAL (SEÇÃO IV)
        31911: "c31911_a_separacao_secao_v",  # À SEPARAÇÃO (SEÇÃO V)
        31912: "c31912_a_assistencia_material_secao_vi",  # À ASSISTÊNCIA MATERIAL (SEÇÃO VI)
        31913: "c31913_a_alimentacao_secao_vii",  # À ALIMENTAÇÃO (SEÇÃO VII)
        31914: "c31914_a_assistencia_a_saude_secao_viii",  # À ASSISTÊNCIA À SAÚDE (SEÇÃO VIII)
        31915: "c31915_a_assistencia_juridica_secao_ix",  # À ASSISTÊNCIA JURÍDICA (SEÇÃO IX)
        31916: "c31916_a_assistencia_psicossocial_secao_x",  # À ASSISTÊNCIA PSICOSSOCIAL (SEÇÃO X)
        31917: "c31917_a_assistencia_religiosa_secao_xi",  # À ASSISTÊNCIA RELIGIOSA (SEÇÃO XI)
        31918: "c31918_a_assistencia_educacional_secao_xii",  # À ASSISTÊNCIA EDUCACIONAL (SEÇÃO XII)
        31919: "c31919_ao_trabalho_secao_xiii",  # AO TRABALHO (SEÇÃO XIII)
        31920: "c31920_a_integridade_fisica_secao_xiv",  # À INTEGRIDADE FÍSICA (SEÇÃO XIV)
        31921: "c31921_a_disciplina_secao_xv",  # À DISCIPLINA (SEÇÃO XV)
        31922: "c31922_as_visitas_secao_xvi",  # ÀS VISITAS (SEÇÃO XVI)
        31923: "c31923_a_revista_secao_xvii",  # À REVISTA (SEÇÃO XVII)
        31924: "c31924_as_medidas_de_seguranca_secao_xviii",  # ÀS MEDIDAS DE SEGURANÇA (SEÇÃO XVIII)
        31925: "c31925_a_organizacao_administrativa_secao_xix",  # À ORGANIZAÇÃO ADMINISTRATIVA (SEÇÃO XIX)
        31926: "c31926_aos_policiais_penais_e_seguranca_do_esta",  # AOS POLICIAIS PENAIS E SEGURANÇA DO ESTABELECIMENTO PRISIONAL (SEÇÃO XX)
        31941: "c31941_outros",  # Outros
        31928: "c31928_outros",  # Outros
        31943: "c31943_discorra_em_linhas_gerais_o_resumo_dos_p",  # Discorra, em linhas gerais, o resumo dos PONTOS NEGATIVOS
        31945: "durante_a_visita_houve_a_necessidade_de",  # 23.3 Durante a visita, houve a necessidade de adotar algum tipo de providência?
        31949: "juntada_de_informacoes_obtidas_no_proced",  # Juntada de informações obtidas no procedimento de monitoramento de visitas em curso na unidade ministerial, referindo-se ou não a novas situações problemas de sua atribuição.
        31950: "juntada_de_informacoes_nos_autos_de_acao",  # Juntada de informações nos autos de ação judicial em trâmite sobre a situação problema.
        31952: "expedicao_de_oficio_a_outra_unidade_do_m",  # Expedição de ofício a outra unidade do Ministério Público a partir da natureza da situação problema identificada (Promotoria especializada, órgão centralizado, Promotoria vinculada a área da situação problema etc.).
        31953: "instauracao_de_procedimento_investigator",  # Instauração de procedimento investigatório criminal.
        31955: "instauracao_de_procedimento_preparatorio",  # Instauração de procedimento preparatório ou inquérito civil.
        31956: "c31956_encaminhamento_de_comunicacao_da_situaca",  # Encaminhamento de comunicação da situação problema à Secretaria de Estado respectiva.
        31959: "c31959_encaminhamento_de_comunicacao_da_situaca",  # Encaminhamento de comunicação da situação problema ao Departamento Penitenciário Nacional e/ou Estadual.
        31960: "c31960_encaminhamento_de_comunicacao_da_situaca",  # Encaminhamento de comunicação da situação problema ao órgão correcional da respectiva polícia.
        31962: "c31962_encaminhamento_de_comunicacao_da_situaca",  # Encaminhamento de comunicação da situação problema ao órgão centralizador do Ministério Público de tutela coletiva de segurança pública.
        31969: "q23_3_2_outro_s_tipo_s_de_providencia_s",  # 23.3.2 Outro(s) tipo(s) de providência(s)
        31983: "instauracao_de_procedimento_administrati",  # Instauração de procedimento administrativo no âmbito do Ministério Público.
        31984: "requisicao_de_inquerito_policial",  # Requisição de inquérito policial.
        31985: "encaminhamento_ao_orgao_do_ministerio_pu",  # Encaminhamento ao órgão do Ministério Público com a respectiva atribuição.
        31986: "q23_4_2_outro_s_tipo_s_de_providencia_s",  # 23.4.2 Outro(s) tipo(s) de providência(s):
        31988: "observacoes_finais",  # Observações Finais
    },
}
