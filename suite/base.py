"""Base dos testes: utilidades que todo módulo usa."""
import json
import os
import subprocess
import unittest
import urllib.error
import urllib.request

from suite import config


def systemctl(*args, timeout=15):
    try:
        r = subprocess.run(["systemctl", *args], capture_output=True,
                           text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def unidade_ativa(nome):
    return systemctl("is-active", "--quiet", nome)[0] == 0


def propriedade(unidade, prop):
    return systemctl("show", unidade, "-p", prop, "--value")[1]


def http(caminho, metodo="GET", headers=None, timeout=20):
    url = config.HTTP_BASE.rstrip("/") + "/" + caminho.lstrip("/")
    req = urllib.request.Request(url, method=metodo, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(2048)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), b""
    except Exception:
        return 0, {}, b""


def ler_json(caminho):
    with open(caminho) as f:
        return json.load(f)


def porta_escutando(porta):
    alvo = f":{porta:04X}"
    for arq in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(arq) as f:
                for linha in f.readlines()[1:]:
                    c = linha.split()
                    if len(c) > 3 and c[1].endswith(alvo) and c[3] == "0A":
                        return True
        except OSError:
            pass
    return False


class CasoBase(unittest.TestCase):
    """Guardas separados por tipo de dependência.

    Assim o CI roda contra fixtures tudo que é sistema de arquivos, e pula só o
    que precisa de systemd ou de um servidor HTTP no ar.
    """

    def exigir_servidor(self):
        """Precisa de uma árvore de servidor, fixture serve."""
        if not os.path.isdir(config.SERVER_DIR):
            self.skipTest("árvore de servidor ausente")

    def exigir_systemd(self):
        if config.MODO_CI or not os.path.isdir("/run/systemd/system"):
            self.skipTest("sem systemd neste ambiente")

    def exigir_http(self):
        if config.MODO_CI:
            self.skipTest("sem servidor HTTP neste ambiente")
