"""Alvos da suite.

Nenhum caminho real deste servidor vive aqui, os padrões são genéricos e o
ambiente concreto entra por `qa.local.env` (fora do controle de versão) ou por
variáveis de ambiente. É isso que permite publicar o repositório sem expor a
topologia da máquina, e também o que deixa a mesma suite rodar contra
fixtures no CI.
"""
import os

_LOCAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "qa.local.env")


def _carregar_local():
    """Lê pares CHAVE=valor sem sobrescrever o que já veio do ambiente."""
    try:
        with open(_LOCAL) as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip())
    except OSError:
        pass


_carregar_local()


def _p(nome, padrao):
    return os.environ.get(nome, padrao)


# Raízes (padrões genéricos; o real vem do qa.local.env)
SERVER_DIR = _p("QA_SERVER_DIR", "/srv/minecraft")
SECOND_DIR = _p("QA_SECOND_DIR", "/srv/minecraft-secondary")
BOT_DIR    = _p("QA_BOT_DIR",    "/srv/ops-bot")
PUBLIC_DIR = _p("QA_PUBLIC_DIR", os.path.join(SERVER_DIR, "public"))

# Unidades systemd
SERVICES   = [s for s in _p("QA_SERVICES", "ops-bot,downloads").split(",") if s]
GAME_UNITS = [s for s in _p("QA_GAME_UNITS", "game-primary,game-secondary").split(",") if s]
TIMER      = _p("QA_TIMER", "backup.timer")

# HTTP (sempre local: a suite roda na própria máquina)
HTTP_BASE  = _p("QA_HTTP_BASE", "http://127.0.0.1:25580")
GAME_PORT  = int(_p("QA_GAME_PORT", "25565"))

# Regras de negócio que a suite garante
MAX_SPAWN_DIST   = int(_p("QA_MAX_SPAWN_DIST", "80"))
MIN_TICK_TIMEOUT = int(_p("QA_MIN_TICK_TIMEOUT", "300000"))
BACKUP_KEEP      = int(_p("QA_BACKUP_KEEP", "3"))

# Scripts de operação instalados em /usr/local/bin (nomes vêm do ambiente)
SCRIPTS = [s for s in _p("QA_SCRIPTS", "").split(",") if s]
MODO_CI          = os.environ.get("QA_CI") == "1"
