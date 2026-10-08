"""Fixtures para os testes de API.

Usa o contexto de requisição do Playwright, o mesmo que se usa para testar
REST, sem abrir navegador. O endereço vem do ambiente: no repositório é sempre
local, nunca o endereço real do servidor.
"""
import os

import pytest
from playwright.sync_api import sync_playwright

BASE = os.environ.get("QA_HTTP_BASE", "http://127.0.0.1:25580")


@pytest.fixture(scope="session")
def playwright_inst():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def api(playwright_inst):
    contexto = playwright_inst.request.new_context(base_url=BASE)
    yield contexto
    contexto.dispose()
