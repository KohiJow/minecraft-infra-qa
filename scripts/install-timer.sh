#!/bin/bash
# Instala o timer que roda a suite todo dia de madrugada.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USUARIO="${SUDO_USER:-$USER}"

sudo tee /etc/systemd/system/qa-suite.service >/dev/null <<EOF
[Unit]
Description=Suite de qualidade da plataforma de jogos
After=network-online.target

[Service]
Type=oneshot
User=${USUARIO}
WorkingDirectory=${REPO}
ExecStart=${REPO}/scripts/run-daily.sh
TimeoutStartSec=600
EOF

sudo tee /etc/systemd/system/qa-suite.timer >/dev/null <<'EOF'
[Unit]
Description=Roda a suite de qualidade todo dia

[Timer]
OnCalendar=*-*-* 04:30:00
RandomizedDelaySec=600
Persistent=yes

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now qa-suite.timer
echo "timer instalado. Proxima execucao:"
systemctl list-timers qa-suite.timer --no-pager
