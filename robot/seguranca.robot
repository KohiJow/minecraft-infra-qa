*** Settings ***
Documentation     Seguranca do servidor e privacidade do que e publicado.
Library           resources/PlataformaLibrary.py
Force Tags        seguranca

*** Test Cases ***
Whitelist ligada
    [Documentation]    Regressao real: o jogo regerou a config e abriu o servidor.
    [Tags]    critico    regressao
    A Propriedade Do Servidor Deve Ser    white-list    true

Sanitizador redige cada classe de segredo
    [Documentation]    E o que torna seguro publicar o relatorio num portfolio.
    [Tags]    critico    privacidade
    O Sanitizador Deve Redigir    endereco 203.0.113.45
    O Sanitizador Deve Redigir    jogador 06eefc19-32d5-39fc-8499-024d3bac6945
    O Sanitizador Deve Redigir    contato pessoa@exemplo.com.br
    O Sanitizador Deve Redigir    arquivo em /home/alguem/bot.py

Todo mundo tem instrucao de instalacao publicada
    [Documentation]    O jogador precisa saber o que baixar para cada mundo.
    Todo Mundo Deve Ter Instrucao De Instalacao
