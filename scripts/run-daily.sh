#!/bin/bash
# Execução diária: roda a suite, publica o relatório e registra no histórico
# do repositório. Falha vira código de saída diferente de zero, que o systemd
# reporta: e, se houver notificação configurada, dispara aviso.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

python3 suite/runner.py
RC=$?

# Painel visual para embutir no README do perfil
python3 suite/painel.py >/dev/null 2>&1 || true

# Robot Framework, quando disponivel: mesma logica, relatorio em HTML
if command -v robot >/dev/null 2>&1 || [ -x "$HOME/.local/bin/robot" ]; then
  ROBOT=$(command -v robot || echo "$HOME/.local/bin/robot")
  "$ROBOT" --outputdir robot/results --quiet robot/ >/dev/null 2>&1 || RC=1
fi

# Contrato da API (Playwright), quando disponivel
if python3 -c "import playwright, pytest" >/dev/null 2>&1; then
  (cd api && python3 -m pytest -q >/dev/null 2>&1) || RC=1
fi

if command -v git >/dev/null && [ -d .git ]; then
  git add -A reports/ >/dev/null 2>&1
  if ! git diff --cached --quiet; then
    DATA=$(date +%Y-%m-%d)
    ESTADO=$([ $RC -eq 0 ] && echo "ok" || echo "com falha")
    git commit -q -m "relatorio de ${DATA} (${ESTADO})" || true
    # push só acontece se houver remoto configurado e credencial disponível
    git remote get-url origin >/dev/null 2>&1 && git push -q origin HEAD 2>/dev/null || true
  fi
fi
exit $RC
