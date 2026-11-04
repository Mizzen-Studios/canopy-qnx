#!/bin/bash
# Run INSIDE the selected x86_64 Linux environment. No SDK is bundled.
# Credentials enter a transient private @options file, NEVER expanded argv.
set +x
set -euo pipefail
umask 077
: "${MYQNX_USER:?Set account name in environment}"
: "${QSC_CLI:?Set installed qnxsoftwarecenter_clt absolute path}"
secret=${MYQNX_SECRET_FILE:-$HOME/.secrets/myqnx}
private=${QSC_PRIVATE_DIR:-$HOME/.qnx/private-auth}
if [ ! -f "$secret" ]; then echo "BLOCKED: waiting for password file (SDK-blocked); no login attempted" >&2; exit 75; fi
# Validate before reading; symlinks/foreign ownership/permissive files fail closed.
python3 - "$secret" "$private" <<'PY'
import os,pathlib,stat,sys
secret=pathlib.Path(sys.argv[1]); private=pathlib.Path(sys.argv[2])
for path,mode in ((secret,0o600),(secret.parent,0o700)):
    info=path.lstat()
    if path.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=mode:
        raise SystemExit("BLOCKED: credential ownership/mode/symlink validation failed")
for path in (private, *private.parents):
    if path.is_symlink() or (path/".git").exists():
        raise SystemExit("BLOCKED: private auth must be outside repositories and symlinks")
private.mkdir(parents=True,exist_ok=True,mode=0o700)
info=private.stat()
if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
    raise SystemExit("BLOCKED: private auth directory must be owned and mode700")
PY
options=$(mktemp "$private/options.XXXXXXXX")
log=$(mktemp "$private/qsc-log.XXXXXXXX")
cleanup() { unset MYQNX_PASSWORD; [ -z "${options:-}" ] || rm -f -- "$options"; }
trap cleanup EXIT HUP INT TERM
MYQNX_PASSWORD="$(cat -- "$secret")"
export MYQNX_PASSWORD
python3 - "$options" <<'PY'
import os,pathlib,sys
password=os.environ["MYQNX_PASSWORD"]; user=os.environ["MYQNX_USER"]
if not password or any(c in password+user for c in ("\n","\r","\0")):
    raise SystemExit("BLOCKED: empty or multiline credential cannot use options format")
pathlib.Path(sys.argv[1]).write_text("-myqnx.user\n"+user+"\n-myqnx.password\n"+password+"\n",encoding="utf-8")
PY
unset MYQNX_PASSWORD
set +e
"$QSC_CLI" "@$options" "$@" >"$log" 2>&1
status=$?
set -e
echo "QSC finished; private log retained outside repositories (output intentionally not printed)"
exit "$status"
