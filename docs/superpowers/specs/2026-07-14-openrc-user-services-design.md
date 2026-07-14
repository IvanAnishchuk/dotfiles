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

`mpd` and `deluged` have real foreground modes, so they use
`supervisor=supervise-daemon`. **`gpg-agent` does not** and is managed
differently (see its section):

| daemon      | mode                               | note                                        |
|-------------|------------------------------------|---------------------------------------------|
| `gpg-agent` | launch via `gpg-connect-agent`     | no foreground+listen mode exists in 2.5.20; not supervised |
| `mpd`       | `--no-daemon`                      | native `pipewire` output available          |
| `deluged`   | `--do-not-daemonize` (`-d`)        | config dir `~/.config/deluge` already exists |

**Why gpg-agent can't be supervise-daemon'd** (learned during implementation):
`--daemon` always forks and orphans to init (`--no-detach` doesn't stop it),
`--server` is stdin-only and opens no sockets, and `--deprecated-supervised`
needs socket-activation FDs OpenRC doesn't provide. There is no
foreground-and-listen invocation, so a supervisor can't track it — it reports
`stopped` while an orphan agent runs. Since gpg-agent self-relaunches on demand,
respawn buys nothing; the service just launches it (with the session bus set)
and kills it on stop.

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

description="GnuPG agent (gpg + ssh auth sockets)"

depend() {
	after dbus
}

start() {
	ebegin "Launching gpg-agent"
	# Be the sole launcher: evict any agent auto-started on demand (which may
	# lack the session bus above), then launch it explicitly with gpgconf so the
	# service -- not a stray connection probe -- owns the invocation. (Using
	# `gpg-connect-agent /bye` instead only autostarts the agent as a side effect
	# of connecting, with an 8s connect-wait.)
	gpgconf --kill gpg-agent 2>/dev/null
	gpgconf --launch gpg-agent
	eend $? "Failed to launch gpg-agent"
}

stop() {
	ebegin "Stopping gpg-agent"
	gpgconf --kill gpg-agent
	eend $? "Failed to stop gpg-agent"
}

status() {
	# --no-autostart: probe without launching, so a status check can't start it.
	# NB: gpg-connect-agent exits 0 even when no agent is running, so key off the
	# 'OK' response, not the exit code -- otherwise status always reports running.
	if gpg-connect-agent --no-autostart 'GETINFO version' /bye 2>/dev/null | grep -q '^OK'; then
		einfo "gpg-agent is running"
		return 0
	fi
	einfo "gpg-agent is not running"
	return 3
}
```

**Why custom `start`/`stop`/`status`:** gpg-agent has no supervisable foreground
mode (above), so instead of `command`/`supervisor` the service launches it
GnuPG's own way. `start` first `gpgconf --kill`s any on-demand agent (which may
have come up without the session bus), then `gpgconf --launch gpg-agent` launches
a fresh one (inheriting the exported bus) — an *explicit* launch, not the
`gpg-connect-agent /bye` side-effect autostart (which comes with an 8s
connect-wait and reads as "launched by a connection"). `stop` kills it. `status`
probes with
`--no-autostart` so checking state can't itself start the agent — and keys off
the `OK` response, because `gpg-connect-agent` exits `0` whether or not an agent
is running (keying off the exit code made `status` always report "running").
Losing supervise-daemon respawn is fine: gpg-agent self-relaunches on demand.

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

- `rc-service --user gpg-agent status` → running (custom `status` probe); an ssh
  op on a `confirm` key (`ssh -T git@github.com`) pops pinentry instead of
  returning `agent refused operation`; `SSH_AUTH_SOCK` unchanged and usable.
- `rc-service --user mpd status` → started; `mpc status` (or a client on `127.0.0.1:6600`)
  responds; audio output enumerates the pipewire sink.
- `rc-service --user deluge status` → started; deluge client connects to the daemon.
- Respawn (mpd/deluge only): `kill` the supervised PID and confirm supervise-daemon
  restarts it. gpg-agent is not supervised (self-relaunches on demand instead).

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
