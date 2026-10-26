#!/usr/bin/env bash
# qmx-recover: the operator's way back into a QMX server without an agent (engine AD-71,
# ruling 139). `qmx node setup` installs it at /usr/local/sbin/qmx-recover, outside the version
# folders, with its settings in /etc/qmx-recover.conf. It needs only what the machine has without
# QMX, runs QMX's own Python only for `doctor`, `reinstall` and the layout step of `repair`, and
# never prints a key, a token or a vault value: it reads the token and key files only to test that
# they exist and their modes.
set -u
umask 077

HOST_UNIT=qmx-host
QMX_FOLDER=/srv/qmx/home/.qmx
QMX_HOME=/srv/qmx/home/.qmx/data
QMX_KEYS=/srv/qmx/home/.qmx/keys
LIBRARY=/srv/qmx/library
PORT=8766
PROJECT=/opt/qmx/qmx-agents
VENV=/opt/qmx/qmx-agents/.venv
VERSIONS=/opt/qmx-versions
CURRENT=/opt/qmx
QMX_USER=qmx
OLD_VAULT=/etc/qmx/vault
UNIT_DIR=/etc/systemd/system
UNIT_COPY=/usr/local/lib/qmx-recover/qmx-host.service
UFW_DEFAULTS=/etc/default/ufw
SHIPPING_UNIT=qmx-ship.timer
MONITORING_UNITS="otelcol openobserve"
PC_NAME=
WAIT_S=60
UNDO_UNIT=qmx-firewall-undo
CLOSE_UNIT=qmx-firewall-close
FIREWALL_STATUS=/var/lib/qmx-recover/firewall-close
CONF="${QMX_RECOVER_CONF:-/etc/qmx-recover.conf}"

say() { printf '%s\n' "$*"; }
FAILED=0
line() {
  printf '%-11s %s  %s\n' "$1" "$2" "$3"
  [[ "$3" == FAIL ]] && FAILED=$((FAILED + 1))
  return 0
}
stop_here() {
  printf '%s\n' "$@" >&2
  exit 1
}

help() {
  cat <<'EOF'
qmx-recover: get this server going again, without an agent.
Run it as: sudo qmx-recover <what>

  status            What is running, what is not, and what looks wrong.
  logs [part]       The last 200 lines of a part's log. Add "follow" to keep watching.
  start [part]      Start a part, or all of QMX.
  stop [part]       Stop a part, or all of QMX.
  restart [part]    Stop and start again.
  repair            Fix what can be fixed without a reset, move an old home into the folder
                    tree, then start QMX and check it answers.
  reinstall         Put QMX's program files back at the version in use.
  rollback          Go back to the version before the last update.
  pair              Make a fresh pairing code here. Then run "qmx-recover pair" on your PC.
  vault             Check the key copy your PC sent (names only, never values).
  firewall status   Say whether the firewall is on, and how the last close went.
  firewall close    Turn it on: SSH, Tailscale and QMX's containers only.
  firewall keep     Keep it on. Without this it turns itself off five minutes after a close.
  firewall open     Turn it off. Every door then answers the internet, each still behind its key.
  doctor            QMX's own check (needs QMX's program files).

Parts: host, shipping, monitoring, tailscale, docker. Leave it out to mean all of QMX.
Locked out of SSH? Use Contabo's VNC console in its customer panel, log in, and run
"sudo qmx-recover firewall open".
A full reset is "qmx node setup" from your PC, and losing the Library is "qmx node rebuild".
EOF
}

# The settings file is read as KEY=value lines, never run, and only when nobody else can change
# it: root acts on the paths it names.
load_conf() {
  if [[ ! -e "$CONF" ]]; then
    [[ -n "${QMX_RECOVER_CONF:-}" ]] && stop_here "There is no settings file at $CONF."
    return 0
  fi
  local owner mode key value
  owner="$(stat -c %u "$CONF")"
  mode="$(stat -c %a "$CONF")"
  if [[ "$owner" != "$(id -u)" ]] || (( 8#$mode & 8#022 )); then
    stop_here "Another user can change $CONF, so it is not used. Fix it with:" \
      "sudo chown root:root $CONF && sudo chmod 644 $CONF"
  fi
  while IFS='=' read -r key value || [[ -n "$key" ]]; do
    case "$key" in
      HOST_UNIT | QMX_FOLDER | QMX_HOME | QMX_KEYS | LIBRARY | PORT | PROJECT | VENV | \
        VERSIONS | CURRENT | QMX_USER | OLD_VAULT | UNIT_DIR | UNIT_COPY | UFW_DEFAULTS | SHIPPING_UNIT | MONITORING_UNITS | \
        PC_NAME | WAIT_S | FIREWALL_STATUS)
        printf -v "$key" '%s' "$value"
        ;;
    esac
  done <"$CONF"
}

need_root() {
  if [[ "$(id -u)" != 0 && -z "${QMX_RECOVER_CONF:-}" ]]; then
    stop_here "Run it with sudo: sudo qmx-recover $*"
  fi
}

units_of() {
  case "${1:-qmx}" in
    host) say "$HOST_UNIT" ;;
    shipping) say "$SHIPPING_UNIT" ;;
    monitoring) say "$MONITORING_UNITS" ;;
    tailscale) say tailscaled ;;
    docker) say docker ;;
    qmx | all) say "$HOST_UNIT $SHIPPING_UNIT $MONITORING_UNITS" ;;
    *) return 1 ;;
  esac
}

part_units() {
  units_of "$1" ||
    stop_here "There is no part called \"$1\". The parts are host, shipping, monitoring, tailscale and docker."
}

installed() { [[ "$(systemctl show -p LoadState --value "$1" 2>/dev/null)" == loaded ]]; }

door_code() {
  curl -s -o /dev/null -m 5 -w '%{http_code}' "http://127.0.0.1:$PORT/api/health" 2>/dev/null
}

door_answers() {
  local code
  code="$(door_code)"
  [[ "$code" == 401 || "$code" == 200 ]]
}

mode_of() { stat -c %a "$1" 2>/dev/null; }

# --- status ---------------------------------------------------------------------------------

unit_line() {
  local part="$1" unit="$2" state result
  if ! installed "$unit"; then
    line "$part" "$unit is not installed on this server" FAIL
    return
  fi
  state="$(systemctl is-active "$unit" 2>/dev/null)"
  if [[ "$state" == active ]]; then
    line "$part" "$unit is running" PASS
  else
    result="$(systemctl show -p Result --value "$unit" 2>/dev/null)"
    line "$part" "$unit is ${state:-stopped} (last result: ${result:-unknown})" FAIL
  fi
}

status() {
  local unit address peers free_kb free_mb owner vault_mode token_mode key_mode errors
  unit_line host "$HOST_UNIT"
  if door_answers; then
    line door "answers on 127.0.0.1:$PORT and asks for its key" PASS
  else
    line door "does not answer on 127.0.0.1:$PORT" FAIL
  fi
  unit_line shipping "$SHIPPING_UNIT"
  for unit in $MONITORING_UNITS; do unit_line monitoring "$unit"; done
  unit_line docker docker
  address="$(tailscale ip -4 2>/dev/null | head -1)"
  if [[ -n "$address" ]]; then
    line tailscale "this server is $address on your tailnet" PASS
  else
    line tailscale "this server has no tailnet address; try: sudo tailscale up" FAIL
  fi
  if [[ -n "$PC_NAME" ]]; then
    peers="$(tailscale status 2>/dev/null | awk -v name="$PC_NAME" '$2 == name')"
    if [[ -n "$peers" && "$peers" != *offline* ]]; then
      line pc "your PC $PC_NAME shows on the tailnet" PASS
    else
      line pc "your PC $PC_NAME does not show; that is normal while it is off" PASS
    fi
  fi
  firewall_line
  if grep -qsx 'format_version = 2' "$QMX_FOLDER/qmx-home.toml"; then
    line folder "$QMX_FOLDER is in the folder tree" PASS
  else
    line folder "$QMX_FOLDER is not in the folder tree; run: sudo qmx-recover repair" FAIL
  fi
  free_kb="$(df -Pk "$QMX_FOLDER" 2>/dev/null | awk 'NR == 2 { print $4 }')"
  if [[ -z "$free_kb" ]]; then
    line disk "cannot read the free space under $QMX_FOLDER" FAIL
  elif ((free_kb < 2 * 1024 * 1024)); then
    line disk "$((free_kb / 1024 / 1024)) GB free, under 2 GB" FAIL
  else
    line disk "$((free_kb / 1024 / 1024)) GB free" PASS
  fi
  free_mb="$(free -m 2>/dev/null | awk '$1 == "Mem:" { print $7 }')"
  if [[ -z "$free_mb" ]]; then
    line memory "cannot read the free memory" FAIL
  elif ((free_mb < 500)); then
    line memory "$free_mb MB available, under 500 MB" FAIL
  else
    line memory "$free_mb MB available" PASS
  fi
  if [[ -d "$LIBRARY" ]]; then
    owner="$(stat -c %U "$LIBRARY")"
    if [[ "$owner" == "$QMX_USER" ]]; then
      line library "$LIBRARY belongs to $QMX_USER, $(du -sh "$LIBRARY" 2>/dev/null | cut -f1) in use" PASS
    else
      line library "$LIBRARY belongs to $owner, not $QMX_USER; run: sudo qmx-recover repair" FAIL
    fi
  else
    line library "there is no Library at $LIBRARY" FAIL
  fi
  vault_mode="$(mode_of "$QMX_KEYS")"
  if [[ "$vault_mode" == 700 ]]; then
    line vault "the key folder is private" PASS
  else
    line vault "the key folder is ${vault_mode:-missing}, not 700; run: sudo qmx-recover repair" FAIL
  fi
  token_mode="$(mode_of "$QMX_KEYS/control-token")"
  key_mode="$(mode_of "$QMX_HOME/vault/pairing-key")"
  if [[ "$key_mode" == 600 ]]; then
    line pairing "the pairing code is in place and private" PASS
  else
    line pairing "the pairing code is ${key_mode:-missing}; run: sudo qmx-recover pair" FAIL
  fi
  if [[ "$token_mode" == 600 ]]; then
    line token "the host's door key is in place and private" PASS
  elif [[ -z "$token_mode" ]]; then
    line token "the host makes its door key when it first starts; it has not yet" FAIL
  else
    line token "the host's door key is $token_mode, not 600; run: sudo qmx-recover repair" FAIL
  fi
  errors="$(journalctl -u "$HOST_UNIT" -p err -n 5 --no-pager -o cat 2>/dev/null)"
  if [[ -z "$errors" ]]; then
    line errors "no recent errors in the host's log" PASS
  else
    line errors "the host's last error lines are below" FAIL
    printf '%s\n' "$errors" | sed 's/^/    /'
  fi
  ((FAILED == 0))
}

# --- start, stop, logs ------------------------------------------------------------------------

act() {
  local verb="$1" unit units
  units="$(part_units "${2:-qmx}")" || exit 1
  for unit in $units; do
    if ! installed "$unit"; then
      say "$unit is not installed here; skipped."
      continue
    fi
    if systemctl "$verb" "$unit"; then
      say "${verb^} $unit: done."
    else
      say "${verb^} $unit: it did not work. See: sudo qmx-recover logs"
    fi
  done
}

logs() {
  local part="${1:-host}" follow=() unit
  [[ "${2:-}" == follow || "$part" == follow ]] && follow=(-f)
  [[ "$part" == follow ]] && part=host
  local args=() units
  units="$(part_units "$part")" || exit 1
  for unit in $units; do args+=(-u "$unit"); done
  journalctl "${args[@]}" -n 200 --no-pager "${follow[@]}"
}

# --- repair -----------------------------------------------------------------------------------

# Only the QMX folder and the store root from the settings, and never a short path such as / or
# /srv, so a wrong setting cannot change the owner of the raw tick copy or the system.
own_path() {
  local path="$1"
  if [[ "$path" != "$QMX_FOLDER" && "$path" != "$LIBRARY" ]] ||
    [[ "$path" != /*/*/* || "$path" == */ || "$path" == *..* ]]; then
    say "Not touching $path: it is not QMX's folder or Library in $CONF."
    return 1
  fi
  [[ -d "$path" ]] || install -d -o "$QMX_USER" -g "$QMX_USER" -m 750 "$path"
  chown -hR "$QMX_USER:$QMX_USER" "$path"
}

# qmx-home's layout step (design 62 guard 4): a flat home from an earlier setup moves into the
# folder tree and nothing is taken away; a folder already in the tree is left as it is.
layout_step() {
  if ! runuser -u "$QMX_USER" -- "$VENV/bin/python" -m qmx_home layout "$QMX_FOLDER"; then
    say "QMX's folder did not move into the folder tree, and nothing was taken away."
    return 1
  fi
}

move_old_keys() {
  local name folder
  for name in pairing-key control-token; do
    folder="$QMX_KEYS"
    [[ "$name" == pairing-key ]] && folder="$QMX_HOME/vault"
    if [[ -s "$folder/$name" ]]; then
      rm -f "$OLD_VAULT/$name"
    elif [[ -s "$OLD_VAULT/$name" ]]; then
      mv "$OLD_VAULT/$name" "$folder/$name"
      say "Moved the old $name into QMX's folder."
    fi
  done
}

repair() {
  local folder
  say "Stopping the host."
  systemctl stop "$HOST_UNIT" 2>/dev/null
  say "Checking QMX's program files."
  if ! "$VENV/bin/python" -c 'import qmx_host.host' >/dev/null 2>&1; then
    say "QMX's program files are broken; putting them back."
    reinstall || return 1
  fi
  say "Setting owners and modes on QMX's folder and Library."
  own_path "$QMX_FOLDER" || return 1
  own_path "$LIBRARY" || return 1
  layout_step || return 1
  install -d -o "$QMX_USER" -g "$QMX_USER" -m 700 "$QMX_KEYS" "$QMX_HOME/vault"
  move_old_keys
  chmod 750 "$QMX_FOLDER"
  for folder in "$QMX_KEYS" "$QMX_HOME/vault"; do
    chmod 700 "$folder"
    find "$folder" -maxdepth 1 -type f -exec chown "$QMX_USER:$QMX_USER" {} + -exec chmod 600 {} +
  done
  if [[ -f "$UNIT_COPY" ]] && ! cmp -s "$UNIT_COPY" "$UNIT_DIR/$HOST_UNIT.service"; then
    say "Putting the host's service file back."
    install -m 644 "$UNIT_COPY" "$UNIT_DIR/$HOST_UNIT.service"
    systemctl daemon-reload
  fi
  say "Starting the host."
  systemctl start "$HOST_UNIT"
  wait_for_door
}

wait_for_door() {
  local waited=0
  while ((waited < WAIT_S)); do
    if door_answers; then
      say "QMX answers again."
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  say "The host did not answer within $WAIT_S seconds. See what it said: sudo qmx-recover logs host"
  return 1
}

# --- reinstall, rollback, doctor --------------------------------------------------------------

reinstall() {
  local uv
  uv="$(command -v uv || echo /usr/local/bin/uv)"
  if [[ ! -x "$uv" ]]; then
    say "uv, the installer QMX uses, is missing. Run \"qmx node setup\" from your PC."
    return 1
  fi
  say "Reinstalling QMX's program files from this server's own copy."
  if "$uv" sync --project "$PROJECT" --package qmx-host --frozen --no-default-groups --offline; then
    say "Reinstalled."
    return 0
  fi
  say "That needs files this server does not hold. Trying again over the internet."
  if "$uv" sync --project "$PROJECT" --package qmx-host --frozen --no-default-groups; then
    say "Reinstalled."
    return 0
  fi
  say "Both tries failed, so the program files are as they were."
  say "Check the internet here, or run \"qmx node setup\" from your PC."
  return 1
}

rollback() {
  local current previous found=0 version
  current="$(readlink -f "$CURRENT" 2>/dev/null)"
  for version in $(ls -1dt "$VERSIONS"/*/ 2>/dev/null); do
    version="${version%/}"
    if ((found)); then
      previous="$version"
      break
    fi
    [[ "$version" == "$current" ]] && found=1
  done
  if [[ -z "${previous:-}" ]]; then
    say "No earlier version is kept here. Nothing changed."
    return 1
  fi
  # A release from before the folder tree (design 62 B4) would open the folder's top as a flat
  # home and start empty beside data/, so it is never the one to go back to here.
  if [[ -f "$QMX_FOLDER/qmx-home.toml" ]] &&
    ! grep -qs '^TREE' "$previous/qmx-agents/packages/qmx-home/src/qmx_home/__init__.py"; then
    say "The version before this one (${previous##*/}) cannot read the folder tree this server's"
    say "home moved into: it would start QMX empty beside your data. Nothing changed."
    say "Your data is safe in $QMX_FOLDER. Repair this version instead: sudo qmx-recover repair"
    return 1
  fi
  say "Going back to ${previous##*/}."
  ln -sfnT "$previous" "$CURRENT"
  reinstall || return 1
  systemctl restart "$HOST_UNIT"
  wait_for_door
}

doctor() {
  if ! "$VENV/bin/python" -c 'import qmx_control.node' >/dev/null 2>&1; then
    say "QMX's program files are broken, so its own check cannot run. Try: sudo qmx-recover repair"
    return 1
  fi
  "$VENV/bin/qmx" node verify --home "$QMX_HOME" --vault "$QMX_KEYS"
}

# --- pair -------------------------------------------------------------------------------------

# The server half of a pairing: the new code where the host reads it, the outgoing one kept as
# pairing-key.previous for one pass lifetime, the run-pass secret rotated with it, the old /etc
# copy removed, and the host restarted so every reader takes the new code. `qmx node pair` on the
# PC sends its code on stdin; without --from-stdin a fresh code is made here.
pair() {
  local code vault="$QMX_HOME/vault"
  if [[ "${1:-}" == --from-stdin ]]; then
    IFS= read -r code || true
    if [[ ! "$code" =~ ^[A-Za-z0-9_-]{16,}$ ]]; then
      stop_here "The pairing code from your PC did not arrive. Nothing changed."
    fi
  else
    code="$(head -c 32 /dev/urandom | base64 | tr '+/' '-_' | tr -d '=\n')"
  fi
  install -d -o "$QMX_USER" -g "$QMX_USER" -m 700 "$vault"
  printf '%s\n' "$code" >"$vault/pairing-key.tmp"
  if [[ -s "$vault/pairing-key" ]]; then
    mv "$vault/pairing-key" "$vault/pairing-key.previous"
    rm -f "$vault/run-pass-key"
  fi
  mv "$vault/pairing-key.tmp" "$vault/pairing-key"
  chown "$QMX_USER:$QMX_USER" "$vault"/pairing-key*
  chmod 600 "$vault"/pairing-key*
  rm -f "$OLD_VAULT/pairing-key"
  systemctl try-restart "$HOST_UNIT"
  if [[ "${1:-}" == --from-stdin ]]; then
    say "Paired: this server holds your PC's new code, and its host restarted."
  else
    say "A fresh pairing code is ready here, and the host restarted with it."
    say "Now run \"qmx-recover pair\" on your PC so it holds the same code."
  fi
}

# --- vault ------------------------------------------------------------------------------------

vault() {
  local file="$QMX_HOME/vault-store.json" owner mode counts age_h
  if [[ ! -f "$file" ]]; then
    line vault "no key copy from your PC yet; on your PC run: qmx-recover vault" FAIL
    return 1
  fi
  owner="$(stat -c %U "$file")"
  mode="$(mode_of "$file")"
  age_h=$((($(date +%s) - $(stat -c %Y "$file")) / 3600))
  if [[ "$owner" == "$QMX_USER" ]]; then
    line owner "the key copy belongs to $QMX_USER" PASS
  else
    line owner "the key copy belongs to $owner, not $QMX_USER; run: sudo qmx-recover repair" FAIL
  fi
  if [[ "$mode" == 600 ]]; then
    line mode "the key copy is private (600)" PASS
  else
    line mode "the key copy is $mode, not 600; run: sudo qmx-recover repair" FAIL
  fi
  if ! command -v python3 >/dev/null; then
    line shape "python3 is missing, so the copy's shape cannot be checked" FAIL
    return 1
  fi
  counts="$(python3 -c '
import json, sys
rows = json.load(open(sys.argv[1], encoding="utf-8"))["entries"]
gone = sum(1 for row in rows if isinstance(row, dict) and row.get("deleted"))
print(len(rows) - gone, gone)
' "$file" 2>/dev/null)"
  if [[ -z "$counts" ]]; then
    line shape "the copy is damaged; on your PC run: qmx-recover vault" FAIL
    return 1
  fi
  line shape "it reads well: keys ${counts% *}, removed ${counts#* }, sent $age_h hours ago" PASS
  say "To send it again, run \"qmx-recover vault\" on your PC."
}

# --- firewall (engine AD-71) ------------------------------------------------------------------

firewall_on() {
  local shown
  shown="$(ufw status verbose 2>/dev/null)"
  [[ "$shown" == *"Status: active"* && "$shown" == *"deny (incoming)"* ]]
}

firewall_line() {
  local state words
  if firewall_on; then
    line firewall "on: only SSH, Tailscale and QMX's containers get in" PASS
  else
    line firewall "off: every door answers the internet, each behind its key; run: sudo qmx-recover firewall close" FAIL
  fi
  [[ -s "$FIREWALL_STATUS" ]] || return 0
  read -r state words <"$FIREWALL_STATUS"
  if [[ "$state" == on ]]; then
    line "last close" "$words" PASS
  else
    line "last close" "$words" FAIL
  fi
}

stop_unit() {
  systemctl stop "$1.timer" "$1.service" >/dev/null 2>&1
  systemctl reset-failed "$1.timer" "$1.service" >/dev/null 2>&1
  return 0
}

stamp() { date -u '+%Y-%m-%d %H:%M:%S UTC'; }

close_result() {
  install -d -m 700 "${FIREWALL_STATUS%/*}"
  printf '%s\n' "$*" >"$FIREWALL_STATUS"
}

# Switching ufw on resets the SSH session that asked for it, so the switch runs in its own unit a
# few seconds after this returns, and writes its result where `firewall status` reads it.
firewall_close() {
  local ports port ufw
  ufw="$(command -v ufw)" || stop_here "The firewall program ufw is not installed. Nothing changed."
  ports="$(sshd -T 2>/dev/null | awk '$1 == "port" { print $2 }')"
  if [[ -z "$ports" ]]; then
    stop_here "Could not read which port SSH uses, so the firewall stays as it is."
  fi
  if ! grep -Eq '^IPV6=yes' "$UFW_DEFAULTS" 2>/dev/null; then
    stop_here "The firewall is set to skip IPv6 ($UFW_DEFAULTS), so it stays as it is." \
      "Set IPV6=yes there and run this again."
  fi
  for port in $ports; do
    ufw allow "$port/tcp" >/dev/null || stop_here "Could not let SSH in on port $port. The firewall stays as it is."
  done
  ufw allow in on tailscale0 >/dev/null
  ufw allow 41641/udp >/dev/null
  ufw allow in on docker0 >/dev/null
  stop_unit "$UNDO_UNIT"
  systemd-run --unit "$UNDO_UNIT" --on-active=300 --timer-property=AccuracySec=1s \
    "$ufw" --force disable >/dev/null ||
    stop_here "Could not set the five-minute undo, so the firewall stays as it is."
  stop_unit "$CLOSE_UNIT"
  close_result pending "still being switched on since $(stamp); check again in a few seconds"
  local env=()
  [[ -n "${QMX_RECOVER_CONF:-}" ]] && env=(--setenv="QMX_RECOVER_CONF=$QMX_RECOVER_CONF")
  systemd-run --unit "$CLOSE_UNIT" --on-active=3 --timer-property=AccuracySec=1s "${env[@]}" \
    "$BASH" "$(readlink -f "${BASH_SOURCE[0]}")" firewall switch-on >/dev/null ||
    stop_here "Could not start switching the firewall on, so it stays as it is."
  say "The firewall is being switched on: SSH (port ${ports//$'\n'/, }), Tailscale and QMX's containers only."
  say "This SSH session may drop when it does. Log in again and check: sudo qmx-recover firewall status"
  say "It turns itself off in five minutes unless you keep it: sudo qmx-recover firewall keep"
}

firewall_switch_on() {
  if ufw default deny incoming >/dev/null && ufw default allow outgoing >/dev/null &&
    ufw --force enable >/dev/null && firewall_on; then
    close_result on "switched on at $(stamp)"
  else
    close_result failed "did not switch on at $(stamp); run: sudo qmx-recover firewall close"
  fi
}

firewall() {
  case "${1:-status}" in
    status) firewall_line ;;
    close) firewall_close ;;
    switch-on) firewall_switch_on ;;
    keep)
      stop_unit "$UNDO_UNIT"
      say "The firewall stays on."
      ;;
    open)
      say "Turning the firewall off. Every door then answers the internet, each still behind its key."
      stop_unit "$CLOSE_UNIT"
      stop_unit "$UNDO_UNIT"
      ufw --force disable >/dev/null && say "The firewall is off."
      ;;
    *) stop_here "Use: sudo qmx-recover firewall status, close, keep or open." ;;
  esac
}

main() {
  local what="${1:-help}"
  [[ "$what" == help || "$what" == -h || "$what" == --help ]] && {
    help
    return 0
  }
  need_root "$@"
  load_conf
  shift
  case "$what" in
    status) status ;;
    logs) logs "$@" ;;
    start | stop | restart) act "$what" "$@" ;;
    repair) repair ;;
    reinstall) reinstall ;;
    rollback) rollback ;;
    pair) pair "$@" ;;
    vault) vault ;;
    firewall) firewall "$@" ;;
    doctor) doctor ;;
    *)
      say "There is no \"$what\". Run \"qmx-recover help\" for the list."
      return 2
      ;;
  esac
}

main "$@"
