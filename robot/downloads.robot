*** Settings ***
Documentation     O servidor de downloads entrega pacotes de centenas de MB.
...               Sem suporte a retomada, queda de conexao recomeca do zero.
Library           resources/PlataformaLibrary.py
Force Tags        downloads

*** Test Cases ***
Pagina de downloads responde
    A Pagina De Downloads Deve Responder

Download grande aceita retomada
    [Documentation]    Defeito real: 720 MB sem Range. Hoje responde 206.
    [Tags]    critico    regressao
    ${pacote}=    O Maior Pacote Publicado
    O Download Deve Aceitar Retomada    ${pacote}
