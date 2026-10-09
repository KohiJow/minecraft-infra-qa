# Relatório da suite

**Saudável**. 41 verificações em 3.15s, em 2026-10-09T04:34:12.

| Módulo | ✅ | ❌ | 💥 | ⏭️ |
|---|--:|--:|--:|--:|
| `test_backups` | 5 | 0 | 0 | 0 |
| `test_bot_code` | 5 | 0 | 0 | 0 |
| `test_http` | 5 | 0 | 0 | 0 |
| `test_meta` | 3 | 0 | 0 | 0 |
| `test_security` | 10 | 0 | 0 | 0 |
| `test_services` | 7 | 0 | 0 | 0 |
| `test_worlds` | 6 | 0 | 0 | 0 |

## Todas as verificações

| | Verificação | O que garante | ms |
|---|---|---|--:|
| ✅ | `test_backups.test_arquivos_nao_estao_corrompidos` | Backup que não abre não é backup. | 15 |
| ✅ | `test_backups.test_backup_contem_dados_de_jogador` | Backup sem playerdata não protege o progresso de ninguém. | 2718 |
| ✅ | `test_backups.test_existe_backup_recente` | Mais de 48h sem backup é falha operacional. | 0 |
| ✅ | `test_backups.test_indice_publicado_e_atual` | - | 0 |
| ✅ | `test_backups.test_rotacao_respeitada` | Sem rotação o disco enche e o servidor para. | 0 |
| ✅ | `test_bot_code.test_codigo_compila` | - | 67 |
| ✅ | `test_bot_code.test_comandos_registram_em_producao` | - | 39 |
| ✅ | `test_bot_code.test_nada_definido_depois_do_entrypoint` | DEFEITO REAL: comandos escritos depois de client.run() nunca | 32 |
| ✅ | `test_bot_code.test_sem_await_em_funcao_sincrona` | DEFEITO REAL: `await` numa função que devolve bool quebrava o | 121 |
| ✅ | `test_bot_code.test_sem_segredo_escrito_no_codigo` | Token tem de vir do ambiente, não do arquivo. | 32 |
| ✅ | `test_http.test_indice_de_backups_publicado` | - | 4 |
| ✅ | `test_http.test_pagina_explica_cada_mundo` | Antes era listagem crua de diretório e ninguém sabia o que baixar. | 1 |
| ✅ | `test_http.test_pagina_inicial_responde` | - | 1 |
| ✅ | `test_http.test_retomada_de_download` | Range/206: sem isso, queda de internet recomeça o download. | 2 |
| ✅ | `test_http.test_todos_os_pacotes_publicados_baixam` | - | 4 |
| ✅ | `test_meta.test_codigo_correto_passa_limpo` | - | 0 |
| ✅ | `test_meta.test_acusa_await_em_funcao_sincrona` | Incidente 3: await sobre função que devolve bool. | 1 |
| ✅ | `test_meta.test_acusa_codigo_depois_do_entrypoint` | Incidente 2: comando definido após o entrypoint. | 0 |
| ✅ | `test_security.test_ip_privado_e_preservado` | Redigir 127.0.0.1 só atrapalharia a leitura do relatório. | 2 |
| ✅ | `test_security.test_ip_publico_e_redigido` | - | 0 |
| ✅ | `test_security.test_nenhum_arquivo_do_repositorio_contem_segredo` | O teste que torna seguro publicar isto. | 16 |
| ✅ | `test_security.test_relatorio_publicado_passa_pelo_sanitizador` | - | 2 |
| ✅ | `test_security.test_sanitizador_cobre_cada_classe_de_segredo` | - | 0 |
| ✅ | `test_security.test_versao_nao_e_confundida_com_endereco` | Regressão: a primeira versão do padrão de IP acusava "5.0.2.517", | 0 |
| ✅ | `test_security.test_backup_de_mundo_nao_vai_para_nuvem_de_terceiros` | - | 0 |
| ✅ | `test_security.test_modo_offline_tem_autenticacao_compensatoria` | O grupo usa clientes não-originais, então online-mode fica false. | 1 |
| ✅ | `test_security.test_pasta_publica_nao_expoe_dado_de_jogador` | Só pacote de mods e backup podem estar publicados por HTTP. | 0 |
| ✅ | `test_security.test_whitelist_ligada` | Regressão real: o jogo regerou o server.properties e voltou a | 0 |
| ✅ | `test_services.test_backup_nao_depende_mais_de_nuvem_externa` | O backup ia para um Drive que estourou a cota e falhava calado. | 0 |
| ✅ | `test_services.test_exatamente_uma_instancia_de_jogo` | As duas instâncias dividem a porta: nunca podem rodar juntas. | 17 |
| ✅ | `test_services.test_exclusao_mutua_declarada_nos_dois_sentidos` | Conflicts= precisa existir dos dois lados; só um lado não protege. | 17 |
| ✅ | `test_services.test_limite_de_memoria_preservado` | Regressão real: apagar um drop-in removeu o MemoryHigh sem aviso. | 9 |
| ✅ | `test_services.test_scripts_de_operacao_executaveis` | - | 0 |
| ✅ | `test_services.test_servicos_de_apoio_ativos` | Bot e servidor de downloads precisam estar sempre no ar. | 15 |
| ✅ | `test_services.test_timer_de_backup_armado` | - | 7 |
| ✅ | `test_worlds.test_conjunto_mapeado_existe_no_disco` | - | 1 |
| ✅ | `test_worlds.test_molde_existe_para_mundo_resetavel` | Mundos de partida precisam poder voltar ao estado inicial. | 0 |
| ✅ | `test_worlds.test_nenhuma_configuracao_aponta_para_mundo_inexistente` | - | 0 |
| ✅ | `test_worlds.test_todo_mundo_tem_ajustes_proprios` | difficulty/pvp são globais no server.properties: sem ajuste por | 0 |
| ✅ | `test_worlds.test_todo_mundo_tem_conjunto_de_mods_mapeado` | - | 0 |
| ✅ | `test_worlds.test_todo_mundo_tem_instrucao_de_instalacao` | O jogador precisa saber o que baixar para cada mundo. | 0 |
