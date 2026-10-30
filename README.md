# Game server platform: API, infrastructure and CI/CD QA
English | [Português](README.pt-BR.md)

![suite](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FKohiJow%2Fminecraft-infra-qa%2Fmain%2Freports%2Fbadge.json)
![CI](https://github.com/KohiJow/minecraft-infra-qa/actions/workflows/selftest.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![playwright](https://img.shields.io/badge/Playwright-API%20testing-2EAD33)
![robot framework](https://img.shields.io/badge/Robot%20Framework-7.x-00C0B5)

A real system in production: two game servers competing for the same port, an
operations bot, a status API and a backup routine. All of it is covered by a
**quality suite that runs on its own every day**, with the report published
here.

Every check came from a defect that actually happened. The root cause of each
one is in [`docs/incidents.md`](docs/incidents.md).

[Latest report](reports/latest.md) | [daily history](reports/history/)

---

## Three test layers

| Layer | Tool | What it covers | Cases |
|---|---|---|--:|
| **API / contract** | Playwright (`APIRequestContext`) + pytest | 3 JSON endpoints: status, world catalog, backup catalog, field types, coherence between fields, cache headers, 404, HEAD and **no leakage of personal data** | 11 |
| **Infrastructure and regression** | `unittest` (zero dependencies) | systemd, mutual exclusion, HTTP with `Range`, the bot's AST, configuration consistency, backup integrity, security | 41 |
| **Business** | Robot Framework | the same scenarios, in language readable by people who don't read Python | 9 |

The Robot layer **does not duplicate logic**: the keyword library imports the
same helpers from the `unittest` suite. One source of truth, three ways to
express the test case.

---

## The API under test was built here

The status endpoint did not exist. It was written as part of this work, which
puts development and testing in the same project:

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

One constraint shaped the design: the service that exposes the API runs in a
sandbox (`ProtectHome`, `ProtectSystem=strict`) and **cannot reach** the data's
source directory or talk to systemd. Instead of loosening the sandbox, the side
that does have access publishes an extract that is already clean, and the
public service only reads files. The running instance is inferred from the
log's timestamp, not from a privileged call.

---

## What this project demonstrates

| Area | How it shows up here |
|---|---|
| API and backend testing | contract tests for 3 JSON endpoints with Playwright: types, coherence, headers, errors |
| Test automation | 61 cases in three layers, one source of logic |
| CI/CD | GitHub Actions on 3 Python versions, report artifact, status badge |
| Infrastructure testing | systemd, mutual exclusion between services, memory limits |
| API/HTTP testing | status, headers, `Range` support (resuming downloads) |
| Static analysis | AST to catch defects that import tests miss |
| Security and privacy | mandatory sanitization + a test that fails if a secret leaks |
| Data validation | consistency across three configuration sources |
| Reliability | backup integrity and rotation, maximum age |
| Observability | daily report in JSON and Markdown, history, badge |
| Root cause analysis | [`docs/incidents.md`](docs/incidents.md), real defects and what changed |

## Why each test exists

The suite does not test the obvious: every check came from **a real incident**.

- **Two instances, one port.** If both start together, one fails and the
  players get disconnected. The test requires `Conflicts=` declared in both
  directions, because one side alone gives no protection.
- **Resuming downloads.** Without `Range`, a 720 MB package makes anyone with a
  bad connection start over from scratch. The test requests a chunk and
  requires `206`.
- **Unreachable code.** Functions written after the *entrypoint* get registered
  under `import` but **not** in production. The import test passed, and the
  user got no response from the command. Now it is an AST test.
- **Backup to a third-party cloud.** It went over quota and failed silently for
  days. The test forbids the external destination and checks the file's
  integrity.
- **Whitelist switched itself off.** The game regenerated the configuration
  file and went back to the open default, with the server already listening.
  That became a test.

Details on each one in [`docs/incidents.md`](docs/incidents.md).

## Two layers on top of the same logic

The `unittest` core has no dependencies at all. It runs on the server machine
itself, which has no development environment, without needing `pip install`.

On top of it there is a **Robot Framework** layer, for the cases that need to
be read by people who don't read Python. The keyword library
(`robot/resources/PlataformaLibrary.py`) **imports the same helpers** from the
suite: there is no duplicated logic, just a second way to express the test
case.

```robot
Apenas uma instancia de jogo por vez
    [Documentation]    As duas engines usam a mesma porta; so uma pode estar no ar.
    [Tags]    critico    regressao
    ${ativas}=    Deve Haver No Maximo Uma Instancia De Jogo
```

## How to run

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

> The Robot HTML reports are kept out of version control on purpose: they
> record the machine's real paths. In CI they come out as an artifact.

## Daily run

A systemd *timer* runs the suite in the early hours of the morning, writes the
report and commits the result. A failure turns into a notification.
Installation: [`scripts/install-timer.sh`](scripts/install-timer.sh).

```
suite/runner.py ─> reports/latest.json   (dados)
                ─> reports/latest.md     (leitura)
                ─> reports/badge.json    (selo)
                ─> reports/history/      (série diária)
```

## Structure

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

## Privacy

What **never** gets out of here: the server address, the bot's token and
webhooks, player names and identifiers, password hashes, paths that contain a
username.

How this is guaranteed, and not just promised:

1. The list of secrets is built **at runtime** from the server itself and is
   never written to disk.
2. Every report goes through the sanitizer before it is written.
3. `test_security.py` scans **every file in the repository** for the forbidden
   patterns and **fails** if it finds any. The test runs along with the
   others, every day.
