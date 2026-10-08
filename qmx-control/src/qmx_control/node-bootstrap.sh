#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
if [[ "$(. /etc/os-release; echo "$ID")" != ubuntu ]]; then
  echo 'QMX nodes require Ubuntu' >&2
  exit 1
fi
apt-get update
apt-get install -y ca-certificates curl git unzip
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release; echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
if ! command -v tailscale >/dev/null; then
  curl -fsSL https://tailscale.com/install.sh -o "$scratch/tailscale-install.sh"
  sh "$scratch/tailscale-install.sh"
fi
if ! command -v uv >/dev/null || [[ "$(uv --version)" != 'uv 0.12.23'* ]]; then
  curl -fsSL https://astral.sh/uv/0.12.23/install.sh -o "$scratch/uv-install.sh"
  UV_INSTALL_DIR=/usr/local/bin sh "$scratch/uv-install.sh"
fi
architecture="$(dpkg --print-architecture)"
archive="rclone-v1.75.1-linux-${architecture}"
if ! command -v rclone >/dev/null || [[ "$(rclone version | head -1)" != 'rclone v1.75.1' ]]; then
  curl -fsSL "https://downloads.rclone.org/v1.75.1/${archive}.zip" -o "$scratch/rclone.zip"
  unzip -oq "$scratch/rclone.zip" -d "$scratch/rclone"
  install -m 0755 "$scratch/rclone/${archive}/rclone" /usr/local/bin/rclone
fi
install -d -m 0700 /etc/qmx/vault /var/lib/qmx /var/lib/qmx/apps /var/lib/qmx/bucket /var/lib/qmx/traces
test -s /opt/qmx-deploy/source.tar
install -d -m 0755 /opt/qmx-versions/@REVISION@
tar -xf /opt/qmx-deploy/source.tar -C /opt/qmx-versions/@REVISION@
ln -sfnT /opt/qmx-versions/@REVISION@ /opt/qmx
uv sync --project /opt/qmx/qmx-control --frozen --no-dev
if [[ ! -f /var/lib/qmx/rclone.conf ]]; then
  printf '[bucket]\ntype = local\n' > /var/lib/qmx/rclone.conf
  chmod 600 /var/lib/qmx/rclone.conf
fi
cat > /etc/systemd/system/qmx-node.service <<'EOF'
[Unit]
Description=QMX Docker node supervisor
After=docker.service tailscaled.service network-online.target
Requires=docker.service tailscaled.service
[Service]
ExecStart=/opt/qmx/qmx-control/.venv/bin/qmx node serve
Restart=on-failure
RestartSec=5
UMask=0077
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/qmx-ship.service <<'EOF'
[Unit]
Description=Ship QMX node logs and traces to the configured bucket
[Service]
Type=oneshot
ExecStart=/usr/local/bin/rclone copy /var/lib/qmx/apps bucket:/var/lib/qmx/bucket/logs --config /var/lib/qmx/rclone.conf --filter "+ */logs/**" --filter "- *" --max-age 30d
ExecStart=/usr/local/bin/rclone copy /var/lib/qmx/traces bucket:/var/lib/qmx/bucket/traces --config /var/lib/qmx/rclone.conf --max-age 30d
UMask=0077
EOF
cat > /etc/systemd/system/qmx-ship.timer <<'EOF'
[Unit]
Description=Flush node logs and traces every minute
[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now docker tailscaled qmx-ship.timer
systemctl enable qmx-node
if tailscale ip -4 >/dev/null 2>&1 && [[ -s /etc/qmx/vault/control-token ]]; then
  systemctl restart qmx-node
fi
echo 'Bootstrap complete; CLIProxy subscription setup is a separate live operation.'
