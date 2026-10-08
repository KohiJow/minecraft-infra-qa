# Incidentes

Defeitos reais encontrados nesta plataforma. Cada um tem sintoma, investigação,
causa raiz, correção e o teste que impede a volta. Nenhum é hipotético.

---

## 1. Servidor morto pelo watchdog durante a sessão

**Sintoma.** O mapa parava de carregar e o jogo congelava. O relato do usuário
foi "travou", o que apontava para o cliente.

**Investigação.** O log do servidor mostrava
`Can't keep up! Running 59960ms or 1199 ticks behind`, seguido de
`ServerHangWatchdog detected that a single server tick took 120.00 seconds`.
O servidor não travou: ele foi **morto**. O relatório de crash trouxe a pilha:

```
incontrol.SpawnerSystem.executeRule
  → CollisionGetter.noCollision
    → LithiumEntityCollisions.doesBoxCollideWithBlocks
      → Level.getChunk
        → ServerChunkCache.getChunkBlocking   ← bloqueia a thread principal
          → Unsafe.park
```

**Causa raiz.** A regra de spawn de mobs podia nascer até 128 blocos do
jogador, mas a distância de simulação carrega 128 blocos, na borda, a checagem
de colisão caía num chunk **ainda não gerado**. O mod pediu o chunk de forma
bloqueante e a thread principal ficou esperando a geração de uma cidade inteira.

**Correção.** Distância máxima de spawn reduzida para 80 blocos em 33 das 35
regras, folga do watchdog ampliada de 2 para 5 minutos, e pré-geração de 22.801
chunks num raio de 1.200 blocos (18 min, 22 chunks/s). Depois disso, zero
avisos de atraso.

**Lição.** "O cliente travou" e "o servidor morreu" produzem o mesmo sintoma na
tela. Só o log do lado do servidor distingue.

---

## 2. Código inalcançável que passava no teste

**Sintoma.** Comandos novos do bot "não faziam nada". Sem erro, sem resposta.

**Investigação.** O log não registrava **nenhuma** chamada desses comandos,
enquanto registrava outros do mesmo usuário. Logo, o despachante não os
conhecia. O arquivo tinha 85 linhas depois de `client.run(TOKEN)`.

**Causa raiz.** As definições estavam **depois do entrypoint**. Em produção o
processo bloqueia em `client.run()` e aquelas linhas nunca executam. Os testes
usavam `import`, que **não** executa o bloco `__main__`, então tudo era
definido e tudo passava. Divergência entre ambiente de teste e de produção.

Um segundo efeito: uma função auxiliar também ficou órfã, e o comando que
iniciava mundos quebrava com `NameError`. O usuário via "o RPG não inicia".

**Correção.** Código movido para antes do entrypoint.

**Teste.** `test_bot_code.test_nada_definido_depois_do_entrypoint` compara, via
AST, a linha de cada definição com a do bloco `__main__`. É o tipo de defeito
que teste de importação nunca pega.

---

## 3. `await` em função síncrona

**Sintoma.** Um comando quebrava com `TypeError: object bool can't be used in
'await' expression`.

**Causa raiz.** A função verificava uma porta TCP lendo `/proc`, operação
síncrona, e foi chamada com `await`.

**Correção.** Removido o `await`.

**Teste.** `test_bot_code.test_sem_await_em_funcao_sincrona` caminha a AST,
monta o conjunto de funções declaradas sem `async` e acusa qualquer `await`
sobre elas.

---

## 4. Whitelist desligada sozinha, com a porta aberta

**Sintoma.** Nenhum, foi encontrado por inspeção durante a instalação.

**Investigação.** O arquivo de configuração escrito antes do primeiro boot
voltou aos padrões: `white-list=false`, `online-mode=true`, dificuldade normal.
O servidor já estava escutando na porta pública.

**Causa raiz.** O jogo regenera o arquivo no primeiro boot quando o formato não
casa, descartando o conteúdo anterior.

**Correção.** Configuração reescrita e também alinhada no arquivo padrão que o
pacote usa como modelo, para não se repetir.

**Teste.** `test_security.test_whitelist_ligada` e
`test_modo_offline_tem_autenticacao_compensatoria`, este último porque o grupo
usa clientes não autenticados, o que permite personificação se não houver mod
de senha.

---

## 5. Backup falhando em silêncio

**Sintoma.** Nenhum, por dias.

**Causa raiz.** O backup diário subia para uma nuvem de terceiro cuja cota
estourou. O script tratava o erro, mantinha a cópia local e seguia com código de
saída zero. Ninguém era avisado.

**Correção.** Destino passou a ser local, publicado por HTTP, com rotação de 3
por mundo e índice gerado automaticamente.

**Testes.** `test_backups` cobre idade máxima (48h), rotação, integridade do
`.tar.gz`, presença de dados de jogador e publicação no índice.
`test_services.test_backup_nao_depende_mais_de_nuvem_externa` impede a volta.

---

## 6. Download de 720 MB sem retomada

**Sintoma.** Previsto, não sofrido, pego antes de publicar o pacote grande.

**Causa raiz.** O servidor de arquivos era o módulo HTTP padrão do Python, que
ignora `Range`. Qualquer queda de conexão recomeçaria o download do zero.

**Correção.** Handler próprio com `206 Partial Content`, `Accept-Ranges`,
sufixo de bytes e `416` correto.

**Teste.** `test_http.test_retomada_de_download` pede 100 bytes do meio de um
arquivo e exige `206` com `Content-Range` e `Content-Length` coerentes.

---

## 7. Cliente recusado por conflito de registro em dependência aninhada

**Sintoma.** Jogador recusado na conexão com
`The server sent registries with unknown keys`.

**Causa raiz.** Uma biblioteca **dentro** de outro arquivo de mod registrava um
serializador próprio. A verificação olhava só o nível de cima.

**Correção.** Verificação passou a abrir arquivos aninhados até 4 níveis.

**Lição.** Em ecossistema de plugins, a árvore de dependências é parte da
superfície de teste. O que quebrou não estava na lista de instalação.

---

## 8. Operação em recurso não carregado falhando em silêncio

**Sintoma.** Uma construção automatizada de 4 estruturas produziu só 1.

**Causa raiz.** O comando de preenchimento de blocos só funciona em região
carregada em memória. Sem jogadores, só a região inicial está carregada, as
outras três ficaram fora e os comandos retornaram sem efeito e **sem erro**.

**Correção.** Forçar o carregamento antes de operar, e liberar depois.

**Lição.** Ausência de erro não é prova de sucesso. A verificação passou a ler
o estado de volta em vez de confiar no código de retorno.

---

## 9. Efeito colateral de uma correção minha

**Sintoma.** Nenhum, pego antes de chegar ao jogador.

**O que houve.** Ao investigar "não aparecem inimigos", encontrei o mod de
spawn do pacote inteiramente desligado e liguei. Estava errado: o pacote spawna
por **outro** sistema, com 35 regras próprias, e o autor desligou aquele de
propósito. Ligar os dois dobraria o spawn e agravaria justamente o travamento
do incidente 1.

**Correção.** Revertido o spawn; mantidos apenas os efeitos de dano, que são
baratos.

**Lição.** "Está desligado" às vezes é decisão de projeto. A ausência de
inimigos era **sintoma** do servidor 60 segundos atrasado, não causa.

---

## 10. Remoção de um arquivo de configuração levou junto um limite de memória

**Sintoma.** Nenhum, pego por auditoria.

**Causa raiz.** Um arquivo de *drop-in* do systemd tinha dois propósitos
acumulados. Removê-lo pelo primeiro motivo apagou silenciosamente o limite de
memória do serviço de jogo.

**Correção.** Limite restaurado em arquivo próprio, com comentário explicando
por que existe.

**Teste.** `test_services.test_limite_de_memoria_preservado`.

---

## 11. Falso positivo numa verificação de segurança

**Sintoma.** O teste que garante que a API não expõe dado pessoal falhou na
primeira execução, acusando "endereço IP exposto".

**Investigação.** O trecho acusado era `5.0.2.517`, número de versão de um
arquivo no catálogo de downloads.

**Causa raiz.** O padrão de reconhecimento de endereço era
`\b(?:\d{1,3}\.){3}\d{1,3}\b`, que não valida faixa de octeto. Qualquer coisa
com quatro grupos de até três dígitos passava: número de versão, build, data.

**Correção.** Padrão com octeto restrito a 0–255, aplicado tanto no teste
quanto no sanitizador, que tinha o **mesmo** defeito e estaria redigindo
números de versão nos relatórios.

**Teste.** `test_security.test_versao_nao_e_confundida_com_endereco` e
`test_ip_publico_e_redigido`: um garante que não redige o que não deve, o outro
que continua redigindo o que deve.

**Lição.** Falso positivo em teste de segurança custa caro de um jeito
diferente: ensina o time a ignorar o alerta. A correção precisa provar os dois
lados, que não acusa à toa e que continua acusando o caso real.
