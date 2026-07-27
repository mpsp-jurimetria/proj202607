"""De-para curado entre entidades do CNMP e unidades da planilha da SAP-SP.

Mapeia entidade_id_api (dim_unidade / dim_entidade) -> valor exato da coluna
"Unidade Prisional" da planilha (tabela sap_unidade no silver). Usado na carga
do gold para enriquecer dim_unidade com município, código IBGE, regional, RAJ
e comarca. Entidades sem correspondente na SAP (unidades militares, cadeias
públicas fora da planilha etc.) ficam fora do dict e recebem NULL.

Um mesmo nome SAP pode atender mais de uma entidade CNMP: a planilha agrega
unidades ("Penit. X + PC de Andradina") que o CNMP cadastra separadas.

Gerado inicialmente por scripts/gerar_depara_unidades_sap.py e curado à mão:
- linhas com "REVISAR ambíguo" trazem a melhor aposta do matching, mas o
  segundo colocado está no comentário; confirme ou corrija.
- linhas comentadas com "REVISAR score baixo" não tiveram match confiável;
  descomente com o nome certo ou exclua se não houver correspondente.
O script não sobrescreve este arquivo; rode-o de novo apenas para comparar.
"""

DEPARA: dict[int, str] = {
    71300: 'Penit. II + APP de São Vicente',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CPP + PC de São Vicente') — Centro de Progressão Penitenciária de São Vicente
    71301: 'Penit. + PRSA de Registro',  # PENITENCIÁRIA DE REGISTRO
    71308: 'Penit. “Bruno Luiz Airoldi Leite” de Caiuá',  # PENITENCIÁRIA DE CAIUÁ
    71328: 'Penit. "ASP Joaquim Fonseca Lopes" de Parelheiros de São Paulo + APP',  # PENITENCIÁRIA "ASP JOAQUIM FONSECA LOPES" DE PARELHEIROS
    71329: 'Penit. II "Dr. Antônio de Souza Neto" + PRSA + PC de Sorocaba',  # PENITENCIÁRIA II "DR. ANTONIO DE SOUZA NETO"
    71330: 'Penit. I "Dr. Antônio de Queiróz Filho" + PRSA de Itirapina',  # PENITENCIÁRIA "DR. ANTÔNIO DE QUEIROZ FILHO"
    71331: 'CPP II "Dr. Eduardo de Oliveira Vianna" de Bauru',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA II "DR. EDUARDO DE OLIVEIRA VIANNA"
    71332: 'Penit. II "Maurício Henrique Guimarães Pereira" de Presidente Venceslau',  # PENITENCIÁRIA II "MAURÍCIO HENRIQUE GUIMARÃES PEREIRA"
    71333: 'Penit. I "Rodrigo dos Santos Freitas" de Balbinos',  # PENITENCIÁRIA I "RODRIGO DOS SANTOS FREITAS"
    71334: 'Penit. "Tacyan Menezes de Lucena" de Martinópolis',  # PENITENCIÁRIA "TACYAN MENEZES DE LUCENA"
    71348: 'Penit. + PC de Florínea',  # PENITENCIÁRIA DE FLORÍNEA
    71381: 'Penit. "ASP. Anísio Aparecido de Oliveira" + PC de Andradina',  # PENITENCIÁRIA ?ASP ANÍSIO APARECIDO DE OLIVEIRA? DE ANDRADINA
    71382: 'Penit. II "Luiz Aparecido Fernandes" de Lavínia',  # PENITENCIÁRIA II "LUIS APARECIDO FERNANDES"
    71386: 'Penit. II "ASP Lindolfo Terçariol Filho" de Mirandópolis',  # PENITENCIÁRIA II "ASP LINDOLFO TERÇARIOL FILHO"
    71387: 'Penit. I "Frederico Geometti" de Lavínia',  # PENITENCIÁRIA I "VEREADOR FREDERICO GEOMETTI"
    71390: 'CDP + PC de Nova Independência',  # CENTRO DE DETENÇÃO PROVISÓRIA DE NOVA INDEPENDÊNCIA
    71397: 'CDP "Dr. Félix Nobre de Campos" de Taubaté',  # CENTRO DE DETENÇÃO PROVISÓRIA "DR. FÉLIX NOBRE DE CAMPOS"
    71398: 'CDP I "ASP Ederson Vieira de Jesus" de Osasco',  # CENTRO DE DETENÇÃO PROVISÓRIA I "EDERSON VIEIRA DE JESUS"
    71399: 'CR + RSA - Regime: fechado e semiaberto de Limeira',  # CENTRO DE RESSOCIALIZAÇÃO DE LIMEIRA
    71405: 'Penit. I "Jairo de Almeida Bueno" + APP do Complexo Penal de Itapetininga',  # PENITENCIÁRIA I "JAIRO DE ALMEIDA BUENO"
    71406: 'Penit. II "ASP Maria Filomena de Sousa Dias" + APP do Complexo Penal de Itapetininga',  # PENITENCIÁRIA II "ASP MARIA FILOMENA DE SOUSA DIAS"
    71427: 'Penit. + PC de Itatinga',  # Penitenciária_de Itatinga
    71429: 'Penit. II + APP de São Vicente',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. I "Dr. Geraldo de Andrade Vieira" + APP + PC de São Vicente') — Penitenciária II de São Vicente
    71430: 'Penit. de Taquarituba',  # PENITENCIÁRIA DE TAQUARITUBA
    71431: 'Penit. Feminina + APP + PC de Mogi Guaçu',  # Penitenciária Feminina de Mogi Guaçu
    # 71474: 'Penit. II + PRSA + PC de Gália',  # REVISAR score baixo (0.25) — PRESÍDIO ESPECIAL DA POLÍCIA CIVIL I
    71480: 'Penit. I "Tenente PM José Alfredo Cintra Borin" de Reginópolis',  # PENITENCIÁRIA I "TENENTE PM JOSÉ ALFREDO CINTRA BORIN"
    71481: 'Penit. I "Dr. Danilo Pinheiro" + PRSA de Sorocaba',  # PENITENCIÁRIA I "DR. DANILO PINHEIRO"
    71482: 'Penit. Compacta "João Augustinho Panucci" de Marabá Paulista',  # PENITENCIÁRIA "JOÃO AUGUSTINHO PANUCCI"
    71483: 'Penit. "João Batista de Santana" de Riolândia',  # PENITENCIÁRIA "JOÃO BATISTA DE SANTANA"
    71484: 'Penit. I "Dr. Walter Faria Pereira de Queiróz" + PRSA de Pirajuí',  # PENITENCIÁRIA I "DR. WALTER FARIA PEREIRA DE QUEIRÓZ"
    71485: 'Penit. I "Mário Moura Albuquerque" + APP + PRSA de Franco da Rocha',  # PENITENCIÁRIA I "MÁRIO DE MOURA ALBUQUERQUE"
    71486: 'Penit. I "Nestor Canoa" + PRSA de Mirandópolis',  # PENITENCIÁRIA I "NESTOR CANOA"
    71487: 'Penit. "Odon Ramos Maranhão" + APP + ADP de Iperó',  # PENITENCIÁRIA "ODON RAMOS MARANHÃO"
    71488: 'Penit. "Osiris Souza e Silva" de Getulina',  # PENITENCIÁRIA "OSÍRIS SOUZA E SILVA"
    71489: 'Penit. II "Sgto. PM Antonio Luiz de Souza" + PC de Reginópolis',  # PENITENCIÁRIA II "SARGENTO LUIZ ANTONIO DE SOUZA"
    71490: 'Penit. III "ASP Paulo Guimarães" de Lavínia',  # PENITENCIÁRIA III "ASP PAULO GUIMARÃES"
    71491: 'Penit. II "Adriano Marrey" + APP de Guarulhos',  # PENITENCIÁRIA II "DESEMBARGADOR ADRIANO MARREY"
    71495: 'Penit. "Cabo PM Marcelo Pires da Silva" + APP de Itaí',  # PENITENCIÁRIA "CABO PM MARCELO PIRES DA SILVA"
    71498: 'Penit. RSA de Assis',  # PENITENCIÁRIA DE ASSIS
    71499: 'Penit. "José Luiz Mansur" + PRSA de Marília',  # PENITENCIÁRIA DE MARÍLIA
    71500: 'Penit. "Ozias Lúcio dos Santos" de Pacaembu',  # PENITENCIÁRIA "OZIAS LÚCIO DOS SANTOS"
    71501: 'Penit. Compacta + PC de Paraguaçu Paulista',  # PENITENCIÁRIA DE PARAGUAÇU PAULISTA
    71506: 'Penit. de Valparaíso',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CPP de Valparaíso') — PENITENCIÁRIA DE VALPARAÍSO
    71513: 'Penit. "Dr. Sebastião Martins Silveira" + PRSA + ADP + PC de Araraquara',  # PENITENCIÁRIA "DR. SEBASTIÃO MARTINS SILVEIRA"
    71531: 'CDP IV de Pinheiros de São Paulo',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP III de Pinheiros de São Paulo + APP') — CENTRO DE DETENÇAO PROVISÓRIA III DE PINHEIROS
    71532: 'Penit. de Pontal',  # PENITENCIARIA_DE PONTAL
    71533: 'CDP "ASP Nayan Xavier Ribeiro" de Ribeirão Preto',  # CENTRO DE DETENÇÃO PROVISÓRIA ?ASP NAYAN XAVIER RIBEIRO? DE RIBEIRÃO PRETO
    71534: 'CDP "Dr. José Eduardo Mariz de Oliveira" + PRSA de Caraguatatuba',  # CENTRO DE DETENÇÃO PROVISÓRIA "DR. JOSÉ EDUARDO MARIZ DE OLIVEIRA"
    71535: 'CDP I "ASP Vicente Luzan da Silva" de Pinheiros de São Paulo + APP',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP "Luis Cesar Lacerda" de São Vicente') — CENTRO DE DETENÇÃO PROVISÓRIA DE SÃO VICENTE
    71536: 'Penit. de Irapuru',  # PENITENCIÁRIA DE IRAPURU
    71555: 'Penit. "Wellington Rodrigo Segura" + PRSA + PC de Presidente Prudente',  # PENITENCIÁRIA "WELLINGTON RODRIGO SEGURA"
    71556: 'Penit. I "Zwinglio Ferreira" + APP de Presidente Venceslau',  # PENITENCIÁRIA I "ZWINGLIO FERREIRA"
    71557: 'Penit. "Orlando Brando Filinto" + APP de Iaras',  # PENITENCIÁRIA "ORLANDO BRANDO FILINTO"
    71560: 'Penit. "AEVP Cristiano Oliveira" de Flórida Paulista',  # PENITENCIÁRIA ?AEVP CRISTIANO DE OLIVEIRA? DE FLÓRIDA PAULISTA
    71561: 'Penit. Feminina + APP + PC de Tupi Paulista',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. "Vanderlei Tartari Monteiro" + PC de Tupi Paulista') — PENITENCIÁRIA DE TUPI PAULISTA
    71572: 'Penit. Feminina RSA de Campinas',  # PENITENCIÁRIA FEMININA DE CAMPINAS
    71574: 'CDP "Tácio Aparecido Santana" + PC de Caiuá',  # CENTRO DE DETENÇÃO PROVISÓRIA "TÁCIO APARECIDO SANTANA"
    71581: 'Penit. I "Dr. Geraldo de Andrade Vieira" + APP + PC de São Vicente',  # PENITENCIÁRIA I "DR. GERALDO DE ANDRADE VIEIRA"
    71584: 'Centro de Readaptação Penitenciária "Dr. José Ismael Pedrosa" (M e F) de Presidente Bernardes',  # CENTRO DE READAPTAÇÃO "DR. JOSÉ ISMAEL PEDROSA"
    71587: 'CR "ASP Gláucio Reinaldo Mendes Pereira" + RSA + PC - Regime: fechado e semiaberto de Presidente Prudente',  # CENTRO DE RESSOCIALIZAÇÃO ?ASP GLÁUCIO REINALDO MENDES PEREIRA? DE PRESIDENTE PRUDENTE
    71590: 'CPP I "Dr. Alberto Brocchieri" de Bauru',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA I "DR. ALBERTO BROCCHIERI"
    71591: 'Penit. I "Dr. Paulo Luciano de Campos" de Avaré',  # PENITENCIÁRIA I "DR. PAULO LUCIANO DE CAMPOS"
    71592: 'Penit. I “AEVP Jair Guimarães de Lima” de Potim',  # PENITENCIÁRIA I "AEVP JAIR GUIMARÃES DE LIMA"
    71593: 'Penit. II "Nelson Marcondes do Amaral" + PRSA de Avaré',  # PENITENCIÁRIA II "NELSON MARCONDES DO AMARAL"
    71594: 'Penit. II + PC do Complexo Penal de Guareí',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. I "Nelson Vieira" do Complexo Penal de Guareí') — PENITENCIÁRIA DE GUAREÍ II
    71595: 'Penit. + APP + PC de Lucélia',  # PENITENCIÁRIA DE LUCÉLIA
    71596: 'Penit. II "Dr. José Augusto César Salgado" + APP + PC de Tremembé',  # PENITENCIÁRIA II "DR. JOSÉ AUGUSTO CÉSAR SALGADO"
    71608: 'Penit. III de Hortolândia do Complexo Penal de Hortolândia',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. II "Odete Leite de Campos Critter" RSA de Hortolância') — PENITENCIÁRIA III DE HORTOLÂNDIA
    71611: 'Penit. II "João Batista de Arruda Sampaio" + APP + PC de Itirapina',  # PENITENCIÁRIA II "JOÃO BATISTA DE ARRUDA SAMPAIO"
    71616: 'Penit. Feminina I "Santa Maria Eufrásia Pelletier" + APP de Tremembé',  # PENITENCIÁRIA FEMININA I "SANTA MARIA EUFRASIA PELLETIER"
    71624: 'Penit. III "ASP Sandro Alves da Silva" de Serra Azul',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. II + PRSA de Serra Azul') — Penit. III "ASP Sandro Alves da Silva" de Serra Azul
    71625: 'CDP + APP do Complexo Penal de Sorocaba',  # CENTRO DE DETENÇÃO PROVISÓRIA DE SOROCABA
    71626: 'CDP "Dr. Calixto Antonio" de São Bernardo do Campo + APP',  # CENTRO DE DETENÇÃO PROVISÓRIA "DR. CALIXTO ANTÔNIO"
    71627: 'CDP de São José do Rio Preto',  # CENTRO DE DETENÇÃO PROVISÓRIA DE SÃO JOSÉ DO RIO PRETO
    71628: 'Penit. + PRSA de Taiúva',  # Penitenciária_de Taiúva
    71631: 'Penit. Feminina + APP de Ribeirão Preto',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. + APP de Ribeirão Preto') — PENITENCIÁRIA FEMININA DE RIBEIRÃO PRETO
    71633: 'Penit. Feminina II de Tremembé',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. Feminina I "Santa Maria Eufrásia Pelletier" + APP de Tremembé') — PENITENCIÁRIA FEMININA II DE TREMEMBÉ
    71635: 'Penit. Feminina Sant´Ana de São Paulo + PC',  # PENITENCIÁRIA FEMININA DE SANT?ANA
    71637: 'Penit. III "ASP Sandro Alves da Silva" de Serra Azul',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. II + PRSA de Serra Azul') — PENITENCIÁRIA I DE SERRA AZUL
    71638: 'Penit. II "Gilmar Monteiro de Souza" de Balbinos',  # PENITENCIÁRIA II "GILMAR MONTEIRO DE SOUZA"
    71639: 'Penit. II + APP de Potim',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. I “AEVP Jair Guimarães de Lima” de Potim') — PENITENCIÁRIA II DE POTIM
    71642: 'Penit. I "José Parada Neto" + PRSA de Guarulhos',  # PENITENCIÁRIA I "JOSÉ PARADA NETO"
    71651: 'Penit. II "Nilton Silva" de Franco da Rocha',  # PENITENCIÁRIA II "NILTON SILVA"
    71666: 'Penit. + PRSA de Mairinque',  # Penitenciária Masculina de Mairinque
    71673: 'CR "Prefeito João Missaglia" RSA - Regime: semiaberto de Mogi Mirim',  # Centro de Ressocialização Prefeito João Misságlia
    71674: 'Penit. “ASP Luís Ricardo Jock Stoduto” + PRSA de Piracicaba',  # PENITENCIÁRIA DE PIRACICABA
    71717: 'CPP de Guariba',  # Centro_de Progressão Penitenciária de Guariba
    71744: 'Penit. Feminina “Oscar Garcia Machado” + APP + PC de Votorantim',  # PENITENCIÁRIA FEMININA "OSCAR GARCIA MACHADO"
    71767: 'Penit. III "José Aparecido Ribeiro" de Franco da Rocha',  # PENITENCIÁRIA III "JOSÉ APARECIDO RIBEIRO"
    71772: 'CR - Regime: semiaberto de Atibaia',  # CENTRO DE RESSOCIALIZAÇÃO DE ATIBAIA
    71774: 'CR RSA + PC - Regime: semiaberto de Sumaré',  # CENTRO DE RESSOCIALIZAÇÃO DE SUMARÉ
    71776: 'CR Feminino + RSA + PC - Regime: fechado e semiaberto de São José do Rio Preto',  # CENTRO DE RESSOCIALIZAÇÃO FEMININO DE SÃO JOSÉ DO RIO PRETO
    71841: 'Penit. de Junqueirópolis',  # PENITENCIÁRIA DE JUNQUEIRÓPOLIS
    71842: 'Penit. RSA de Osvaldo Cruz',  # PENITENCIÁRIA DE OSVALDO CRUZ
    71843: 'Penit. Compacta de Pracinha',  # PENITENCIÁRIA DE PRACINHA
    71865: 'Penit. Feminina + APP + PC de Tupi Paulista',  # PENITENCIÁRIA FEMININA DE TUPI PAULISTA
    71872: 'CDP de Paulo de Faria',  # CENTRO DE DETENÇÃO PROVISÓRIA DE PAULO DE FARIA
    71875: 'Penit. Feminina "Sandra Aparecida Lario Vianna" + APP + PC de Pirajuí',  # PENITENCIÁRIA FEMININA "SANDRA APARECIDA LARIO VIANNA"
    71890: 'CDP I "ASP Vicente Luzan da Silva" de Pinheiros de São Paulo + APP',  # CENTRO DE DETENÇÃO PROVISÓRIA I "ASP VICENTE LUZAN DA SILVA" DE PINHEIROS
    71891: 'CDP II "ASP Paulo Gilberto de Araújo" de Chácara Belém + APP de São Paulo',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP I de Chácara Belém + APP de São Paulo') — CENTRO DE DETENÇÃO PROVISÓRIA I DE CHÁCARA BELÉM
    71892: 'Penit. II "Luiz Gonzaga Vieira" de Pirajuí',  # PENITENCIÁRIA II "LUIZ GONZAGA VIEIRA"
    71893: 'Penit. "Silvio Yoshihiko Hinohara" + APP de Presidente Bernardes',  # PENITENCIÁRIA "SILVIO YOHIHIKO HINOHARA"
    71900: 'Penit. II "Dr. Enio Mendes Junior" + PRSA + PC do Complexo Penal de Capela do Alto',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. I + PRSA do Complexo Penal de Capela do Alto') — PENITENCIÁRIA DE CAPELA DO ALTO
    71901: 'Penit. II de Cerqueira Cesar',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. I + APP de Cerqueira César') — Penitenciária I de Cerqueira César/SP
    71902: 'Penit. III "ASP Sandro Alves da Silva" de Serra Azul',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. II + PRSA de Serra Azul') — PENITENCIÁRIA II DE SERRA AZUL
    71905: 'CR + RSA - Regime: fechado e semiaberto de Bragança Paulista',  # CENTRO DE RESSOCIALIZAÇÃO ?ENF. ANGELO FERNANDO BARATELLA? DE BRAGANÇA PAULISTA
    71907: 'Penit. I "Nelson Vieira" do Complexo Penal de Guareí',  # PENITENCIÁRIA I "NELSON VIEIRA"
    71909: 'CDP de Diadema + APP',  # CENTRO DE DETENÇÃO PROVISÓRIA DE DIADEMA
    71910: 'Penit. + PRSA de Franca',  # PENITENCIÁRIA DE FRANCA
    71911: 'CDP + APP de Mogi das Cruzes',  # CENTRO DE DETENÇÃO PROVISÓRIA DE MOGI DAS CRUZES
    71926: 'Penit. "ASP Adriano Aparecido de Pieri" de Dracena',  # PENITENCIÁRIA "ASP ADRIANO APARECIDO DE PIERI"
    71929: 'Penit. + APP + PC de Bernardino de Campos',  # Penitenciária de Bernardino de Campos
    71935: 'CDP "ASP Cláudio Chaves do Nascimento" + PC de Lavínia',  # REVISAR ambíguo (0.80 vs 0.75, 2º: 'CDP de Diadema + APP') — Centro de Detenção Provisória de Lavínia/SP (CDP)
    71940: 'CDP Feminino + PC de Franco da Rocha',  # CENTRO DE DETENÇÃO PROVISÓRIA FEMININO DE FRANCO DA ROCHA
    71942: 'CDP IV de Pinheiros de São Paulo',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP III de Pinheiros de São Paulo + APP') — CENTRO DE DETENÇÃO PROVISÓRIA IV DE PINHEIROS
    71948: 'CPP Feminino de São Miguel Paulista de São Paulo (DESATIVADO)',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA FEMININO DE SÃO MIGUEL PAULISTA
    71949: 'Penit. "Joaquim de Sylos Cintra" de Casa Branca',  # PENITENCIÁRIA "JOAQUIM DE SYLOS CINTRA"
    71950: 'Penit. II "Odete Leite de Campos Critter" RSA de Hortolância',  # PENITENCIÁRIA II "ODETE LEITE DE CAMPOS CRITTER"
    71951: 'Penit. "Valentim Alves da Silva" + APP de Álvaro de Carvalho',  # PENITENCIÁRIA "VALENTIM ALVES DA SILVA"
    71953: 'Penit. "Valdic Junio Alves Primo" + PC de Avanhandava',  # PENITENCIÁRIA ?VALDIC JUNIO ALVES PRIMO? DE AVANHANDAVA
    71955: 'Penit. Feminina + APP de Ribeirão Preto',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. + APP de Ribeirão Preto') — PENITENCIÁRIA DE RIBEIRÃO PRETO
    71957: 'Penit. I "Dr. Tarcizo Leonce Pinheiro Cintra" + APP + PC de Tremembé',  # PENITENCIÁRIA I "DR. TARCIZO LEONCE PINHEIRO CINTRA"
    71962: 'Penit. da Capital RSA de São Paulo',  # PENITENCIÁRIA DA CAPITAL
    71968: 'Penit. II "Dr. Enio Mendes Junior" + PRSA + PC do Complexo Penal de Capela do Alto',  # Penitenciária II "Dr. Enio Mendes Junior" de Capela do Alto
    # 71971: 'Penit. II + PRSA + PC de Gália',  # REVISAR score baixo (0.67) — Penitenciária II de Gália/SP
    # 71975: 'Penit. II + PRSA + PC de Gália',  # REVISAR score baixo (0.67) — Penitenciária I de Gália/SP
    71983: 'CDP  Hortolândia do Complexo Penal de Campinas/Hortolândia',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP  Campinas do Complexo Penal de Campinas/Hortolândia') — CENTRO DE DETENÇÃO PROVISÓRIA DE CAMPINAS
    71985: 'CR "Dr. Mauro de Macedo" + RSA - Regime: fechado e semiaberto de Avaré',  # CENTRO DE RESSOCIALIZAÇÃO "DR. MAURO DE MACEDO"
    71990: 'CR + RSA - Regime: fechado e semiaberto de Ourinhos',  # CENTRO DE RESSOCIALIZAÇÃO DE OURINHOS
    71991: 'CDP "AEVP Renato Gonçalves Rodrigues" de Americana',  # CENTRO DE DETENÇÃO PROVISÓRIA "AEVP RENATO GONÇALVES RODRIGUES"
    71992: 'CDP “ASP Francisco Carlos Caneschi” de Bauru',  # CENTRO DE DETENÇÃO PROVISÓRIA "ASP FRANCISCO CARLOS CANESCHI"
    # 72000: 'CR - Regime: semiaberto de Mococa',  # REVISAR score baixo (0.33) — CENTRO HOSPITALAR DO SISTEMA PENITENCIÁRIO
    # 72009: 'Hospital de Custódia e Tratamento Psiquiatrico I de Franco da Rocha',  # REVISAR score baixo (0.67) — HOSPITAL DE CUSTÓDIA E TRATAMENTO PSIQUIÁTRICO "PROFESSOR ANDRÉ TEIXEIRA LIMA" I
    # 72011: 'Hospital de Custódia e Tratamento Psiquiatrico I de Franco da Rocha',  # REVISAR score baixo (0.67) — HOSPITAL DE CUSTÓDIA E TRATAMENTO PSIQUIÁTRICO "DR. ARNALDO AMADO FERREIRA"
    72013: 'Hospital de Custódia e Tratamento Psiquiátrico II (M) de Franco da Rocha',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Hospital de Custódia e Tratamento Psiquiatrico I de Franco da Rocha') — HOSPITAL DE CUSTÓDIA E TRATAMENTO PSIQUIÁTRICO II
    72072: 'CR - Regime: fechado e semiaberto de Birigui',  # CENTRO DE RESSOCIALIZAÇÃO DE BIRIGUI
    72073: 'CPP "Dr. Walter Erwin Hoffgen" de Porto Feliz',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA DE PORTO FELIZ
    72076: 'Penit. de Valparaíso',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CPP de Valparaíso') — CENTRO DE PROGRESSÃO PENITENCIÁRIA DE VALPARAÍSO
    72077: 'CPP "Dr. Rubens Aleixo Sendin" de Mongaguá',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA "DR. RUBENS ALEIXO SENDIN"
    72083: 'CPP "Dr. Javert de Andrade" de São José do Rio Preto',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA "DR. JAVERT DE ANDRADE"
    72098: 'CPP III "Prof. Noé Azevedo" de Bauru',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA III "PROF. NOÉ AZEVEDO"
    72099: 'CPP (Penit. I) de Hortolândia do Complexo Penal de Hortolândia',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA DE HORTOLÂNDIA
    # 72100: 'Penit. II + PRSA + PC de Gália',  # REVISAR score baixo (0.25) — PRESÍDIO ESPECIAL DA POLÍCIA CIVIL II
    72114: 'CPP de Pacaembu',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA DE PACAEMBU
    72116: 'CR Feminino - Regime: semiaberto Rio Claro',  # CENTRO DE RESSOCIALIZAÇÃO FEMININO DE RIO CLARO
    72117: 'CR "Dr Luis Gonzaga da Arruda Campos" + RSA - Regime: fechado e semiaberto de Rio Claro',  # CENTRO DE RESSOCIALIZAÇÃO "DR. LUIS GONZAGA DE ARRUDA CAMPOS"
    72118: 'CR + RSA - Regime: fechado e semiaberto de Araçatuba',  # CENTRO DE RESSOCIALIZAÇÃO DE ARAÇATUBA
    72132: 'CR "Dr. Manoel Carlos Muniz" + RSA - Regime: fechado e semiaberto de Lins',  # CENTRO DE RESSOCIALIZAÇÃO "DR. MANOEL CARLOS MUNIZ"
    72133: 'CR - Regime: semiaberto de Marília',  # CENTRO DE RESSOCIALIZAÇÃO DE MARÍLIA
    72134: 'CR "Dr. João Eduardo Franco Perlati" + RSA - Regime: fechado e semiaberto de Jaú',  # CENTRO DE RESSOCIALIZAÇÃO "DR. JOÃO EDUARDO FRANCO PERLATI"
    72135: 'CR Feminino "Carlos Sidnes de Souza Cantarelli" - Regime: semiaberto de Piracicaba',  # CENTRO DE RESSOCIALIZAÇÃO FEMININO "CARLOS SIDNES DE SOUZA CANTARELLI"
    72136: 'CR Feminino + RSA - Regime: fechado e semiaberto de Araraquara',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CR + RSA - Regime: fechado e semiaberto de Araraquara') — CENTRO DE RESSOCIALIZAÇÃO FEMININO DE ARARAQUARA
    72137: 'CR - Regime: semiaberto do Complexo Penal de Itapetininga',  # CENTRO DE RESSOCIALIZAÇÃO DE ITAPETININGA
    72138: 'CR Feminino + RSA + PC - Regime: fechado e semiaberto de São José do Rio Preto',  # REVISAR ambíguo (0.83 vs 0.75, 2º: 'CR Feminino + RSA - Regime: fechado e semiaberto de Araraquara') — CENTRO DE RESSOCIALIZAÇÃO FEMININO DE SÃO JOSÉ DOS CAMPOS
    72146: 'CR - Regime: semiaberto de Mococa',  # CENTRO DE RESSOCIALIZAÇÃO DE MOCOCA
    72152: 'CR Feminino + RSA - Regime: fechado e semiaberto de Araraquara',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CR + RSA - Regime: fechado e semiaberto de Araraquara') — CENTRO DE RESSOCIALIZAÇÃO DE ARARAQUARA
    72154: 'CPP de Jardinópolis',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA DE JARDINÓPOLIS
    72157: 'CPP "Prof. Ataliba Nogueira" de Campinas',  # REVISAR ambíguo (0.83 vs 0.75, 2º: 'CPP de Valparaíso') — CENTRO DE PROGRESSÃO PENITENCIÁRIA "PROFESSOR ATALIBA NOGUEIRA"
    72158: 'CPP "Dr. Edgard Magalhães Noronha" de Tremembé',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA "DR. EDGARD MAGALHÃES NORONHA"
    72160: 'CPP "ASP Moises Marcos Braga" de Franco da Rocha (DESATIVADO)',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA DE FRANCO DA ROCHA
    73388: 'Penit. II de Álvaro de Carvalho',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. "Valentim Alves da Silva" + APP de Álvaro de Carvalho') — Penitenciária II de Álvaro de Carvalho
    73469: 'CDP "ASP Valdecir Fabiano" de Riolândia',  # CENTRO DE DETENÇÃO PROVISÓRIA "ASP VALDECIR FABIANO"
    73472: 'CDP - Vila Independência de São Paulo',  # CENTRO DE DETENÇÃO PROVISÓRIA DE VILA INDEPENDÊNCIA
    73480: 'CDP II "ASP Willians Nogueira Benjamin" de Pinheiros de São Paulo',  # REVISAR ambíguo (0.88 vs 0.75, 2º: 'CDP de Diadema + APP') — CENTRO DE DETENÇÃO PROVISÓRIA II "ASP WILLIANS NOGUEIRA BENJAMIM" DE PINHEIROS
    # 73493: 'Penit. + PRSA de Registro',  # REVISAR score baixo (0.50) — CADEIA PÚBLICA DE REGISTRO
    # 73509: 'Penit. Feminina I "Santa Maria Eufrásia Pelletier" + APP de Tremembé',  # REVISAR score baixo (0.20) — Cadeia Pública de Santa Rosa de Viterbo
    # 73516: 'Penit. + PRSA de Franca',  # REVISAR score baixo (0.50) — CADEIA PÚBLICA DE FRANCA
    73566: 'CDP + APP de Mauá',  # CENTRO DE DETENÇÃO PROVISÓRIA DE MAUÁ
    73567: 'CDP II "ASP Paulo Gilberto de Araújo" de Chácara Belém + APP de São Paulo',  # REVISAR ambíguo (1.00 vs 0.86, 2º: 'CDP I de Chácara Belém + APP de São Paulo') — CENTRO DE DETENÇÃO PROVISÓRIA II "ASP PAULO GILBERTO DE ARAUJO" DE CHÁCARA BELÉM
    73568: 'CDP "ASP Nilton Celestino" + APP de Itapecerica da Serra',  # CENTRO DE DETENÇÃO PROVISÓRIA "ASP NILTON CELESTINO"
    73569: 'CDP "Nelson Furlan" + APP de Piracicaba',  # CENTRO DE DETENÇÃO PROVISÓRIA "NELSON FURLAN"
    73583: 'CDP "Marcos Antônio Alves Bezerra" de Jundiaí',  # CENTRO DE DETENÇÃO PROVISÓRIA "MARCOS ANTÔNIO ALVES BEZERRA"
    73585: 'CDP "ASP Charles Demitre Teixeira" + APP de Praia Grande',  # CENTRO DE DETENÇÃO PROVISÓRIA "ASP CHARLES DEMITRE TEIXEIRA"
    # 73589: 'Penit. “Bruno Luiz Airoldi Leite” de Caiuá',  # REVISAR score baixo (0.00) — CADEIA PÚBLICA DE ADAMANTINA
    73654: 'CDP de Santo André + APP',  # CENTRO DE DETENÇÃO PROVISÓRIA DE SANTO ANDRÉ
    73656: 'CDP + APP de Suzano',  # CENTRO DE DETENÇÃO PROVISÓRIA DE SUZANO
    73710: 'Penit. + PRSA + PC de Limeira',  # PENITENCIÁRIA DE LIMEIRA
    73757: 'CDP “Marcos Amilton Raysaro de Icém',  # CENTRO DE DETENÇÃO PROVISÓRIA "MARCOS AMILTON RAYSARO"
    73895: 'CDP  Hortolândia do Complexo Penal de Campinas/Hortolândia',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP  Campinas do Complexo Penal de Campinas/Hortolândia') — CENTRO DE DETENÇÃO PROVISÓRIA DE HORTOLÂNDIA
    73930: 'Penit. II de Cerqueira Cesar',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'Penit. I + APP de Cerqueira César') — Penitenciária II de Cerqueira César/SP
    73931: 'CDP II "ASP Vanda Rita Brito do Rego" de Osasco',  # CENTRO DE DETENÇÃO PROVISÓRIA II "ASP VANDA RITA BRITO DO REGO"
    73936: 'CDP + APP de São José dos Campos',  # CENTRO DE DETENÇÃO PROVISÓRIA DE SÃO JOSÉ DOS CAMPOS
    73942: 'CDP II de Pacaembu',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP I + PC de Pacaembu') — Centro de Detenção Provisória I de Pacaembu
    73943: 'CDP II de Pacaembu',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP I + PC de Pacaembu') — Centro de Detenção Provisória II de Pacaembu
    73954: 'CDP II + APP + PC de Guarulhos',  # REVISAR ambíguo (1.00 vs 1.00, 2º: 'CDP I "ASP Giovani Martins Rodrigues" de Guarulhos + PRSA') — CENTRO DE DETENÇÃO PROVISÓRIA II DE GUARULHOS
    73955: 'CDP I "ASP Giovani Martins Rodrigues" de Guarulhos + PRSA',  # CENTRO DE DETENÇÃO PROVISÓRIA I "ASP GIOVANI MARTINS RODRIGUES"
    73971: 'CDP de Aguaí',  # Centro de Detenção Provisória de Aguaí
    83147: 'CPP Feminino "Dra. Marina Marigo Cardoso de Oliveira" de Butantan de São Paulo',  # CENTRO DE PROGRESSÃO PENITENCIÁRIA FEMININO "DRA. MARINA MARINO CARDOSO DE OLIVEIRA" DO BUTANTAN
}

# automáticos: 143, ambíguos p/ revisar: 35, score baixo (comentados): 11
