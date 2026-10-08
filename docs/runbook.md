# Runbook

## A suite acusou falha

1. `reports/latest.md`, qual módulo e qual verificação.
2. O nome do teste diz o que ele garante; a docstring diz por quê.
3. `docs/incidents.md`, se o teste nasceu de um incidente, a correção
   original está descrita lá.

## Falhas mais prováveis e o que fazer

| Teste | Significa | Ação |
|---|---|---|
| `test_services.test_exatamente_uma_instancia_de_jogo` | duas instâncias no ar | parar uma; conferir `Conflicts=` nas duas unidades |
| `test_services.test_limite_de_memoria_preservado` | drop-in de limites sumiu | restaurar o arquivo de limites |
| `test_backups.test_existe_backup_recente` | +48h sem backup | ver o timer e o log da última execução |
| `test_backups.test_arquivos_nao_estao_corrompidos` | `.tar.gz` ilegível | apagar o corrompido e rodar backup na mão |
| `test_http.test_retomada_de_download` | sem `Range` | o servidor de arquivos voltou ao módulo padrão |
| `test_security.test_whitelist_ligada` | servidor aberto | religar whitelist **antes** de qualquer outra coisa |
| `test_bot_code.*` | defeito estrutural no bot | ver incidentes 2 e 3 |
| `test_security.test_nenhum_arquivo_do_repositorio_contem_segredo` | vazamento | **não publicar**; achar e redigir |

## Operação rotineira

- **Trocar de mundo ou de instância:** pelo bot. A troca cuida de parar o outro
  serviço, aplicar os ajustes do mundo e esperar ficar realmente pronto.
- **Zerar um mundo de partida:** restaura o molde.
- **Publicar pacote de mods novo:** colocar na pasta pública e atualizar o
  arquivo de instruções; o índice se regenera sozinho.

## Antes de publicar o repositório

```bash
python3 -m unittest suite.checks.test_security -v
```

Esse módulo varre todo arquivo versionado atrás de token, webhook, UUID, hash
de senha e e-mail. Se ele passar, é seguro publicar.
