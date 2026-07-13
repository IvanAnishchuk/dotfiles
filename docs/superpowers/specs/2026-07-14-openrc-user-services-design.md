# OpenRC user services: gpg-agent, mpd, deluge

**Date:** 2026-07-14
**Repo:** `~/dotfiles` (personal dotfiles, rcm-managed)
**Status:** design, awaiting review

## Goal

Add OpenRC **user-mode** service scripts for three long-running per-user daemons —
`gpg-agent`, `mpd`, `deluged` — so they are supervised by OpenRC (auto-respawn,
uniform `rc-service --user` control) instead of being auto-launched ad hoc or
started by hand. The `gpg-agent` script follows the system template at
`/etc/user/init.d/ssh-agent`. All new files are onboarded into this dotfiles repo.

## Background / research

OpenRC on this host is `sys-apps/openrc-0.63.1`, which supports user services.
From the installed `user-guide.md`:

- User init scripts load from `${XDG_CONFIG_HOME}/rc/init.d` → `~/.config/rc/init.d/`
  (system templates in `/etc/user/init.d` are also visible).
- `conf.d` overrides: `~/.config/rc/conf.d/` over `/etc/user/conf.d`.
- `rc.conf` override: `~/.config/rc/rc.conf` over `/etc/rc.conf`.
- Runlevels live in `~/.config/rc/runlevels/`.
- Every `rc-*` tool (and `openrc`) takes `--user` / `-U`.
- `XDG_RUNTIME_DIR` must be set before `openrc --user` (elogind/pam already set it).

Because this repo maps `config/` → `~/.config/` via rcm, the user init scripts are
committed as `config/rc/init.d/<name>` and `rcup` symlinks them into
`~/.config/rc/init.d/`.

The `/etc/user/init.d/ssh-agent` template we mirror:

```sh
#!/sbin/openrc-run
supervisor=supervise-daemon
command="/usr/bin/ssh-agent"
command_args="-D -a ${XDG_RUNTIME_DIR}/ssh-agent.sock"
```

All three daemons offer a foreground/non-detaching mode, so all use
`supervisor=supervise-daemon`:

| daemon      | foreground flag                    | note                                        |
|-------------|------------------------------------|---------------------------------------------|
| `gpg-agent` | `--daemon --no-detach`             | `--supervised` is now `--deprecated-supervised` (GnuPG 2.5.20) |
| `mpd`       | `--no-daemon`                      | native `pipewire` output available          |
| `deluged`   | `--do-not-daemonize` (`-d`)        | config dir `~/.config/deluge` already exists |

### Environment

bashrc already derives the gpg env from `gpgconf`, not hardcoded paths:

```sh
export GPG_TTY="$(tty)"
export SSH_AUTH_SOCK="$(gpgconf --list-dirs agent-ssh-socket)"   # -> /run/user/<uid>/gnupg/S.gpg-agent.ssh
```

`~/.gnupg/gpg-agent.conf` already has `enable-ssh-support`. An OpenRC-managed
`gpg-agent` creates its sockets under `$XDG_RUNTIME_DIR/gnupg/` — the exact path
`SSH_AUTH_SOCK` already resolves to. **No bashrc change is required**; tools reach
the sockets as they do today.

**But the service must hand the agent the session bus** (fixed after first cut).
gpg feeds the agent a live tty/display per call via Assuan `OPTION`s, so gpg
pinentry works from a terminal. The **ssh-agent protocol has no such channel**,
so ssh-triggered signatures use the agent's *own launch environment*.
OpenRC/supervise-daemon start the agent with a scrubbed env (no
`DBUS_SESSION_BUS_ADDRESS`), so `pinentry-gnome3` can't reach the GNOME/gcr
prompter and ssh signing fails with `agent refused operation` — most visibly for
the `confirm`-flagged keys in `~/.gnupg/sshcontrol`. On this pure-Wayland GNOME
box even `gnome-shell` carries no `DISPLAY`/`WAYLAND_DISPLAY`; every session daemon
reaches the GUI via `DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus`. The
service therefore exports exactly that one var — the same idiom as
`/etc/user/init.d/gsd` and `xdg-desktop-portal`.

**Rejected alternative — importing the whole `gnome-session` environ** (the
`gnome-shell-wayland` `start_pre` pattern, tried first): it drags in the session's
`PATH`, which lacks `/lib/rc/bin`, so OpenRC's own `ebegin`/`eend` helpers (real
binaries there, not shell functions) become "command not found" inside
`supervise-daemon.sh` and the service fails to start. Set only the bus var; never
import the session `PATH`.

## Files (all onboarded into the repo)

| Repo path                    | Symlinked to (`rcup`)          | Purpose            |
|------------------------------|--------------------------------|--------------------|
| `config/rc/init.d/gpg-agent` | `~/.config/rc/init.d/gpg-agent`| gpg-agent service  |
| `config/rc/init.d/mpd`       | `~/.config/rc/init.d/mpd`      | mpd service        |
| `config/rc/init.d/deluge`    | `~/.config/rc/init.d/deluge`   | deluged service    |
| `config/mpd/mpd.conf`        | `~/.config/mpd/mpd.conf`       | starter mpd config |

The init scripts must be executable (`chmod +x`); rcm preserves mode on the symlink
target, so the committed repo files carry the exec bit.

### `config/rc/init.d/gpg-agent`

```sh
#!/sbin/openrc-run
# GnuPG agent (provides gpg + ssh auth sockets under $XDG_RUNTIME_DIR/gnupg).

# Hand the agent the session bus so ssh-triggered pinentry-gnome3 can reach the
# GNOME/gcr prompter (ssh, unlike gpg, can't pass a display/bus per request).
# One var is enough on Wayland GNOME; do NOT import the whole session environ --
# its PATH lacks /lib/rc/bin and breaks OpenRC's ebegin/eend.
DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
export DBUS_SESSION_BUS_ADDRESS

supervisor=supervise-daemon
description="GnuPG agent (gpg + ssh auth sockets)"
command="/usr/bin/gpg-agent"
command_args="--daemon --no-detach"

start_pre() {
	# GnuPG auto-launches the agent on demand; make this service the sole
	# launcher so supervise-daemon owns the process (avoids "already running").
	gpgconf --kill gpg-agent 2>/dev/null || true
}

stop_post() {
	gpgconf --kill gpg-agent 2>/dev/null || true
}
```

**Rationale for `start_pre`/`stop_post`:** without them, any gpg invocation before
the service starts leaves a stray agent, and `gpg-agent --daemon` would fail with
"already running", which supervise-daemon reports as a failed start. Killing first
guarantees the supervised process is the live one. `stop_post` clears sockets on
stop.

### `config/rc/init.d/mpd`

```sh
#!/sbin/openrc-run
# Music Player Daemon (foreground, supervised).
supervisor=supervise-daemon
description="Music Player Daemon"
command="/usr/bin/mpd"
command_args="--no-daemon ${HOME}/.config/mpd/mpd.conf"

depend() {
	use pipewire dbus
}

start_pre() {
	# mpd does not create its own state dir tree.
	checkpath -d -m 0700 "${HOME}/.local/share/mpd"
	checkpath -d -m 0700 "${HOME}/.local/share/mpd/playlists"
}
```

`depend … use` is a soft dependency: if pipewire/dbus are also OpenRC user services
they start first, but mpd does not fail if they are provided by the desktop session
instead.

### `config/mpd/mpd.conf` (starter)

```
music_directory     "/home/data/Mus"
playlist_directory  "~/.local/share/mpd/playlists"
db_file             "~/.local/share/mpd/database"
state_file          "~/.local/share/mpd/state"
sticker_file        "~/.local/share/mpd/sticker.sql"

bind_to_address     "127.0.0.1"
# no pid_file / no user: foreground under supervise-daemon

audio_output {
	type    "pipewire"
	name    "PipeWire Output"
}
```

No `pid_file` and no `user` directive — the process runs in the foreground as the
invoking user under supervise-daemon. `~` in mpd.conf expands to the running user's
home. Music dir is `/home/data/Mus` (confirmed on disk).

### `config/rc/init.d/deluge`

```sh
#!/sbin/openrc-run
# Deluge BitTorrent daemon (foreground, supervised).
supervisor=supervise-daemon
description="Deluge BitTorrent daemon"
command="/usr/bin/deluged"
command_args="--do-not-daemonize --config ${HOME}/.config/deluge"
```

`~/.config/deluge` already exists, so no config scaffolding is needed.

## Install / enable (runtime — not tracked in the repo)

Runlevel symlinks under `~/.config/rc/runlevels/` are runtime state, deliberately
**not** committed. After `rcup` links the scripts, enable and start per service:

```sh
rcup                                          # symlink the new files into ~/.config
for s in gpg-agent mpd deluge; do
	rc-update --user add "$s" default
	rc-service --user "$s" start
done
```

(`XDG_RUNTIME_DIR` must be set — it already is on a normal login.) These commands
are a documented runtime step the user runs; the design does not automate them.

## Verification

- `rc-service --user gpg-agent status` → started; `gpgconf --list-dirs agent-ssh-socket`
  socket present; `SSH_AUTH_SOCK` unchanged and usable (`ssh-add -l`).
- `rc-service --user mpd status` → started; `mpc status` (or a client on `127.0.0.1:6600`)
  responds; audio output enumerates the pipewire sink.
- `rc-service --user deluge status` → started; deluge client connects to the daemon.
- Respawn: `kill` the supervised PID and confirm supervise-daemon restarts it.

## Known limitation / deferred

- **Multi-session gpg-agent reconciliation.** A single OpenRC user instance owns one
  `gpg-agent` keyed off `XDG_RUNTIME_DIR`. With multiple concurrent login sessions
  (each with its own runtime dir, or a shared one), the `start_pre`/`stop_post`
  `gpgconf --kill` could tear down an agent another session is using. Accepted for
  now (single primary session in practice); revisit if multi-session use becomes
  real. Not resolved by this design.

## Explicitly out of scope (YAGNI)

- No bashrc / env edits (env already correct).
- No `conf.d/` files (tunables inline in the init scripts).
- No `pam_openrc.so` auto-start (would need root PAM edits).
- No runlevel symlinks committed to the repo.
- No migration of gpg/deluge config locations.
```
