*** Settings ***
Documentation     Garantias de infraestrutura da plataforma de servidores de jogo.
...               Duas instancias dividem a mesma porta: se as duas subirem,
...               uma falha e os jogadores caem.
Library           resources/PlataformaLibrary.py
Force Tags        infraestrutura

*** Test Cases ***
Servicos de apoio no ar
    [Documentation]    Bot de operacao e servidor de downloads precisam estar sempre ativos.
    [Tags]    critico
    ${quantos}=    Os Servicos De Apoio Devem Estar Ativos
    Log    ${quantos} servicos de apoio verificados

Apenas uma instancia de jogo por vez
    [Documentation]    As duas engines usam a mesma porta; so uma pode estar no ar.
    [Tags]    critico    regressao
    ${ativas}=    Deve Haver No Maximo Uma Instancia De Jogo
    Log    instancias ativas: ${ativas}

Exclusao mutua declarada nos dois sentidos
    [Documentation]    Conflicts= em um lado so nao protege contra inicio manual.
    [Tags]    regressao
    As Instancias Devem Se Excluir

Limite de memoria preservado
    [Documentation]    Regressao real: remover um drop-in apagou o limite sem aviso.
    [Tags]    regressao
    ${valor}=    O Limite De Memoria Deve Existir
    Log    MemoryHigh=${valor}
