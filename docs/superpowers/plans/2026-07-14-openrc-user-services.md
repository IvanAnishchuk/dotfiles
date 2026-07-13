# OpenRC User Services (gpg-agent, mpd, deluge) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OpenRC user-mode service scripts for `gpg-agent`, `mpd`, and `deluged`, plus a starter `mpd.conf`, all onboarded into this dotfiles repo.

**Architecture:** rcm maps `config/` → `~/.config/`, so each service is a repo file `config/rc/init.d/<name>` that `rcup` symlinks into `~/.config/rc/init.d/`. All three daemons run in the foreground under `supervisor=supervise-daemon`, mirroring `/etc/user/init.d/ssh-agent`. Enabling (runlevel + start) is a runtime step the user runs; runlevel symlinks are not committed.

**Tech Stack:** OpenRC 0.63.1 user services (`openrc-run`, `supervise-daemon`, `rc-service --user`, `rc-update --user`), rcm, GnuPG 2.5.20, MPD, Deluge, PipeWire.

**Spec:** `docs/superpowers/specs/2026-07-14-openrc-user-services-design.md`

**Conventions:** Commit messages follow Conventional Commits (see `git log`: `feat(git):`, `chore(bashrc):`) with the `Co-Authored-By: Claude` trailer (user's own repo). Humanize each message per the repo convention before finalizing. Stage explicit paths only — never `git add -A`. Do not run `rcup`/`rc-update`/`rc-service` for the user without their go; those are called out as runtime steps.

---

### Task 1: gpg-agent user service

**Files:**
- Create: `config/rc/init.d/gpg-agent`

- [ ] **Step 1: Write the service script**

Create `config/rc/init.d/gpg-agent`:

```sh
#!/sbin/openrc-run
# GnuPG agent (provides gpg + ssh auth sockets under $XDG_RUNTIME_DIR/gnupg).
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

- [ ] **Step 2: Make it executable**

Run: `chmod +x config/rc/init.d/gpg-agent`
Expected: no output; `ls -l config/rc/init.d/gpg-agent` shows the `x` bits.

- [ ] **Step 3: Syntax-check the shell**

Run: `bash -n config/rc/init.d/gpg-agent`
Expected: no output, exit 0 (no syntax errors). (The `#!/sbin/openrc-run` shebang is not invoked here; `bash -n` only parses the POSIX-sh body.)

- [ ] **Step 4: Commit**

```bash
git add config/rc/init.d/gpg-agent
git commit -m "feat(rc): add gpg-agent openrc user service

Foreground supervise-daemon service mirroring /etc/user/init.d/ssh-agent.
start_pre/stop_post kill any on-demand agent so the supervised process is
the sole launcher; sockets land under \$XDG_RUNTIME_DIR/gnupg as before."
```
Expected: commit succeeds and is GPG-signed. If signing fails with a Timeout / "agent refused operation", STOP — the user is AFK from the pinentry prompt; ask for a "go" and retry the same command once.

---

### Task 2: mpd user service + starter config

**Files:**
- Create: `config/rc/init.d/mpd`
- Create: `config/mpd/mpd.conf`

- [ ] **Step 1: Write the mpd service script**

Create `config/rc/init.d/mpd`:

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

- [ ] **Step 2: Write the starter mpd.conf**

Create `config/mpd/mpd.conf`:

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

- [ ] **Step 3: Make the service executable**

Run: `chmod +x config/rc/init.d/mpd`
Expected: no output; `ls -l config/rc/init.d/mpd` shows the `x` bits.

- [ ] **Step 4: Syntax-check the service script**

Run: `bash -n config/rc/init.d/mpd`
Expected: no output, exit 0.

- [ ] **Step 5: Validate the mpd.conf parses**

First create the state dir the config references (start_pre is not invoked in a manual run, so this avoids a false failure):

```bash
mkdir -p ~/.local/share/mpd/playlists
mpd --no-daemon --stdout --verbose config/mpd/mpd.conf
```

Note: this actually starts mpd in the foreground against the real music dir. Confirm the log shows it reading the config and opening the `pipewire` output, then Ctrl-C. Expected: no config-parse errors (music dir found, database path accepted). Any `Failed to parse` / `Failed to load config` / unknown-directive error is a FAIL — fix the file. If `pipewire` output fails to open in this environment (no session bus), that is an environment limitation, not a config syntax error — note it and move on.

- [ ] **Step 6: Commit**

```bash
git add config/rc/init.d/mpd config/mpd/mpd.conf
git commit -m "feat(rc): add mpd openrc user service + starter config

Foreground supervise-daemon service; start_pre creates the XDG state dir
tree mpd will not make itself. Starter mpd.conf points at /home/data/Mus
with a native pipewire output and XDG-scoped db/state/playlists."
```
Expected: signed commit succeeds (same AFK-signing caveat as Task 1).

---

### Task 3: deluge user service

**Files:**
- Create: `config/rc/init.d/deluge`

- [ ] **Step 1: Write the service script**

Create `config/rc/init.d/deluge`:

```sh
#!/sbin/openrc-run
# Deluge BitTorrent daemon (foreground, supervised).
supervisor=supervise-daemon
description="Deluge BitTorrent daemon"
command="/usr/bin/deluged"
command_args="--do-not-daemonize --config ${HOME}/.config/deluge"
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x config/rc/init.d/deluge`
Expected: no output; `ls -l config/rc/init.d/deluge` shows the `x` bits.

- [ ] **Step 3: Syntax-check the shell**

Run: `bash -n config/rc/init.d/deluge`
Expected: no output, exit 0.

- [ ] **Step 4: Commit**

```bash
git add config/rc/init.d/deluge
git commit -m "feat(rc): add deluge openrc user service

Foreground supervise-daemon service running deluged against the existing
~/.config/deluge config dir."
```
Expected: signed commit succeeds (same AFK-signing caveat as Task 1).

---

### Task 4: Install, enable, and verify (runtime — user runs)

**Files:** none (runtime state only; runlevel symlinks under `~/.config/rc/runlevels/` are intentionally not committed).

> These steps mutate the live user session and must be run by the user (or with an explicit go). Do not run them unattended. `XDG_RUNTIME_DIR` must be set (true on a normal login).

- [ ] **Step 1: Symlink the new files into ~/.config**

Run: `rcup`
Expected: rcup reports creating `~/.config/rc/init.d/{gpg-agent,mpd,deluge}` and `~/.config/mpd/mpd.conf`. Verify: `ls -l ~/.config/rc/init.d/` shows the three symlinks pointing into `~/dotfiles/config/rc/init.d/`.

- [ ] **Step 2: Confirm OpenRC sees the services**

Run: `rc-service --user -l`
Expected: `gpg-agent`, `mpd`, and `deluge` appear in the list.

- [ ] **Step 3: Enable each in the user default runlevel**

```bash
for s in gpg-agent mpd deluge; do rc-update --user add "$s" default; done
rc-update --user show
```
Expected: `rc-update --user show` lists all three under `default`.

- [ ] **Step 4: Start each service**

```bash
for s in gpg-agent mpd deluge; do rc-service --user "$s" start; done
```
Expected: each prints `Starting <svc> ... [ ok ]`. A failure prints `[ !! ]` — inspect with `rc-service --user <svc> status` and the daemon's own error output.

- [ ] **Step 5: Verify gpg-agent**

```bash
rc-service --user gpg-agent status
gpgconf --list-dirs agent-ssh-socket
ssh-add -l || true
```
Expected: status `started`; the ssh socket path is `/run/user/$(id -u)/gnupg/S.gpg-agent.ssh` and exists; `ssh-add -l` talks to the agent (either lists keys or says "no identities" — not "Could not open a connection").

- [ ] **Step 6: Verify mpd**

```bash
rc-service --user mpd status
mpc status || printf 'no mpc client; check 127.0.0.1:6600\n'
```
Expected: status `started`; `mpc status` responds (empty playlist is fine). The mpd log shows the `pipewire` output opened.

- [ ] **Step 7: Verify deluge**

```bash
rc-service --user deluge status
```
Expected: status `started`. Optionally confirm a deluge client (deluge-console / GTK) connects to the daemon.

- [ ] **Step 8: Verify supervise-daemon respawn (one service)**

```bash
rc-service --user deluge status   # note the pid
pkill -x deluged
sleep 2
rc-service --user deluge status   # should be started again, new pid
```
Expected: supervise-daemon restarts the daemon; status returns to `started` with a different PID.

---

## Notes for the executor

- **No env / bashrc changes.** `SSH_AUTH_SOCK` is already `gpgconf`-derived in bashrc and resolves to the same socket the service creates; leave it alone.
- **Do not commit runlevel symlinks** or any `~/.config/rc/runlevels/` state.
- **Deferred (do not solve here):** multi-session gpg-agent reconciliation — see the spec's "Known limitation / deferred" section.
