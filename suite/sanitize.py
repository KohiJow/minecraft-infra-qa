"""Camada de sanitização.

Princípio: a suite LÊ dados sensíveis para poder validar o servidor, mas nada
sensível pode chegar ao relatório publicado. A lista de segredos é montada em
tempo de execução a partir do próprio servidor e **nunca** é gravada em disco.
"""
import json
import os
import re

_IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b")  # octeto 0-255: sem isso, versao de mod virava IP
_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                   r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
_WEBHOOK = re.compile(r"https://(?:discord|discordapp)\.com/api/webhooks/\S+")
_TOKEN = re.compile(r"\b[A-Za-z0-9_-]{24,28}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}\b")
# Tokens do GitHub: classico (ghp_/gho_/ghs_/ghr_) e de escopo fino (github_pat_)
_GH_TOKEN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,})\b")
_PRIVADO = re.compile(r"^(?:10\.|127\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)")


def _nomes_de_jogadores(server_dir):
    """Nomes vindos da whitelist, só em memória."""
    nomes = set()
    for arq in ("whitelist.json", "ops.json", "banned-players.json"):
        caminho = os.path.join(server_dir, arq)
        try:
            with open(caminho) as f:
                for item in json.load(f):
                    n = (item or {}).get("name")
                    if n and len(n) >= 3:
                        nomes.add(n)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return nomes


class Sanitizador:
    def __init__(self, server_dir, extras=()):
        self._nomes = sorted(_nomes_de_jogadores(server_dir), key=len, reverse=True)
        self._extras = sorted({e for e in extras if e}, key=len, reverse=True)

    def __call__(self, texto):
        if texto is None:
            return None
        if not isinstance(texto, str):
            return texto
        t = texto
        for seg in self._extras:
            t = t.replace(seg, "<REDIGIDO>")
        t = _WEBHOOK.sub("<WEBHOOK>", t)
        t = _TOKEN.sub("<TOKEN>", t)
        t = _GH_TOKEN.sub("<TOKEN_GITHUB>", t)
        t = _EMAIL.sub("<EMAIL>", t)
        t = _UUID.sub("<UUID>", t)
        t = _IPV4.sub(lambda m: m.group(0) if _PRIVADO.match(m.group(0)) else "<IP>", t)
        for nome in self._nomes:
            t = re.sub(rf"\b{re.escape(nome)}\b", "<JOGADOR>", t)
        t = re.sub(r"/home/[A-Za-z0-9_.-]+", "/home/<USER>", t)
        return t

    def estrutura(self, obj):
        """Aplica recursivamente em dict/list/str."""
        if isinstance(obj, dict):
            return {self(k): self.estrutura(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.estrutura(v) for v in obj]
        return self(obj)
