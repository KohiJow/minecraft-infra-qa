# Plataforma de servidores de jogo: QA de API, infraestrutura e CI/CD

![suite](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FKohiJow%2Fminecraft-infra-qa%2Fmain%2Freports%2Fbadge.json)
![CI](https://github.com/KohiJow/minecraft-infra-qa/actions/workflows/selftest.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![playwright](https://img.shields.io/badge/Playwright-API%20testing-2EAD33)
![robot framework](https://img.shields.io/badge/Robot%20Framework-7.x-00C0B5)

Sistema real em produção: dois servidores de jogo que disputam a mesma porta, um
bot de operação, uma API de status e rotina de backup. Tudo coberto por uma
**suite de qualidade que roda sozinha todo dia**, com o relatório publicado aqui.

Cada verificação nasceu de um defeito que aconteceu de verdade. A causa raiz de
cada um está em [`docs/incidents.md`](docs/incidents.md).

[Último relatório](reports/latest.md) | [histórico diário](reports/history/)

---

## Três camadas de teste

| Camada | Ferramenta | O que cobre | Casos |
|---|---|---|--:|
| **API / contrato** | Playwright (`APIRequestContext`) + pytest | 3 endpoints JSON: status, catálogo de mundos, catálogo de backups, tipos, coerência entre campos, cabeçalhos de cache, 404, HEAD e **não vazamento de dado pessoal** | 11 |
| **Infraestrutura e regressão** | `unittest` (zero dependências) | systemd, exclusão mútua, HTTP com `Range`, AST do bot, consistência de configuração, integridade de backup, segurança | 41 |
| **Negócio** | Robot Framework | os mesmos cenários em linguagem legível por quem não lê Python | 9 |

A camada do Robot **não duplica lógica**: a biblioteca de palavras-chave importa
os mesmos helpers da suite em `unittest`. Uma fonte de verdade, três formas de
expressar o caso de teste.

---

## A API testada foi construída aqui

O endpoint de status não existia. Foi escrito como parte deste trabalho, o que
põe desenvolvimento e teste no mesmo projeto:

```http
GET /api/status
{
  "no_ar": true,
  "instancia": "principal",
  "versao_jogo": "1.21.1",
  "mundo": "Vanilla+",
  "vagas": 16,
  "consultado_em": 1791479915
}
```

Uma restrição moldou o desenho: o serviço que expõe a API roda em sandbox
(`ProtectHome`, `ProtectSystem=strict`) e **não alcança** o diretório de origem
dos dados nem fala com o systemd. Em vez de afrouxar o sandbox, quem tem acesso
publica um recorte já limpo, e o serviço público só lê arquivo. A instância viva
é deduzida do horário do log, não de uma chamada privilegiada.

---

## O que este projeto demonstra

| Área | Como aparece aqui |
|---|---|
| Teste de API e backend | contrato de 3 endpoints JSON com Playwright: tipos, coerência, cabeçalhos, erros |
| Automação de testes | 61 casos em três camadas, uma fonte de lógica |
| CI/CD | GitHub Actions em 3 versões de Python, artefato de relatório, selo de estado |
| Teste de infraestrutura | systemd, exclusão mútua entre serviços, limites de memória |
| Teste de API/HTTP | status, cabeçalhos, suporte a `Range` (retomada de download) |
| Análise estática | AST para pegar defeito que testes de importação não pegam |
| Segurança e privacidade | sanitização obrigatória + teste que falha se vazar segredo |
| Validação de dados | consistência entre três fontes de configuração |
| Confiabilidade | integridade e rotação de backup, idade máxima |
| Observabilidade | relatório diário em JSON e Markdown, histórico, selo |
| Análise de causa raiz | [`docs/incidents.md`](docs/incidents.md), defeitos reais e o que mudou |

## Por que cada teste existe

A suite não testa o óbvio: cada verificação nasceu de **um incidente real**.

- **Duas instâncias, uma porta.** Se as duas subirem juntas, uma falha e os
  jogadores caem. O teste exige `Conflicts=` declarado nos dois sentidos, porque
  um lado só não protege.
- **Retomada de download.** Um pacote de 720 MB sem `Range` faz quem tem
  internet ruim recomeçar do zero. O teste pede um trecho e exige `206`.
- **Código inalcançável.** Funções escritas depois do *entrypoint* registram sob
  `import` mas **não** em produção. O teste de importação passava e o usuário via
  o comando não responder. Hoje é um teste de AST.
- **Backup em nuvem de terceiro.** Estourou a cota e falhou em silêncio por
  dias. O teste proíbe o destino externo e verifica integridade do arquivo.
- **Whitelist desligada sozinha.** O jogo regerou o arquivo de configuração e
  voltou ao padrão aberto, com o servidor já escutando. Virou teste.

Detalhe de cada um em [`docs/incidents.md`](docs/incidents.md).

## Duas camadas sobre a mesma lógica

O núcleo em `unittest` não tem dependência nenhuma. Roda na própria máquina do
servidor, que não tem ambiente de desenvolvimento, sem precisar de `pip install`.

Por cima dele há uma camada em **Robot Framework**, para os casos que precisam
ser lidos por quem não lê Python. A biblioteca de palavras-chave
(`robot/resources/PlataformaLibrary.py`) **importa os mesmos helpers** da suite:
não existe lógica duplicada, só uma segunda forma de expressar o caso de teste.

```robot
Apenas uma instancia de jogo por vez
    [Documentation]    As duas engines usam a mesma porta; so uma pode estar no ar.
    [Tags]    critico    regressao
    ${ativas}=    Deve Haver No Maximo Uma Instancia De Jogo
```

## Como rodar

```bash
git clone https://github.com/KohiJow/minecraft-infra-qa
cd minecraft-infra-qa

# núcleo, contra fixtures, sem servidor nem instalação (é o que o CI faz)
QA_CI=1 QA_SERVER_DIR=fixtures/servidor QA_BOT_DIR=fixtures/bot \
  python3 -m unittest discover -s suite/checks -t . -v

# camada Robot Framework
pip install robotframework
robot --outputdir robot/results robot/

# contra a infraestrutura real (precisa do qa.local.env)
python3 suite/runner.py
```

> Os relatórios HTML do Robot ficam fora do versionamento de propósito: eles
> registram os caminhos reais da máquina. No CI saem como artefato.

## Execução diária

Um *timer* do systemd roda a suite de madrugada, grava o relatório e faz commit
do resultado. Falha vira notificação. Instalação em
[`scripts/install-timer.sh`](scripts/install-timer.sh).

```
suite/runner.py ─> reports/latest.json   (dados)
                ─> reports/latest.md     (leitura)
                ─> reports/badge.json    (selo)
                ─> reports/history/      (série diária)
```

## Estrutura

```
suite/
  config.py        alvos, tudo sobrescrevível por ambiente
  sanitize.py      redação de IP, UUID, e-mail, token, webhook, nomes
  base.py          utilidades (systemd, HTTP, JSON) e skip automático
  runner.py        execução + publicação do relatório
  checks/          os seis módulos de verificação
docs/              arquitetura, incidentes, runbook
reports/           resultados publicados
```

## Privacidade

O que **nunca** sai daqui: endereço do servidor, token e webhooks do bot, nomes
e identificadores de jogadores, hashes de senha, caminhos com nome de usuário.

Como isso é garantido, e não só prometido:

1. A lista de segredos é montada **em tempo de execução** a partir do próprio
   servidor e nunca é gravada em disco.
2. Todo relatório passa pelo sanitizador antes de ser escrito.
3. `test_security.py` varre **todo arquivo do repositório** procurando os
   padrões proibidos e **falha** se achar algum. O teste roda junto com os
   outros, todo dia.
