# nsctl — Namespace/Identity Management Tool

## What this is

`nsctl` is a standalone Python CLI tool for managing isolated identity
namespaces. Each namespace is a `pass` store (git repo) with extra
files alongside it — GPG keyring, SSH key set, uv-managed Python venv,
AWS profiles, browser profile, key metadata, age-encrypted sync blobs,
deploy-key registry, and rcm tag fragments.

`ns switch <name>` is the unified "activate" that swaps all of them at
once — same mental model as `source .venv/bin/activate`, but for an
entire identity context.

**Repo:** `github.com/IvanAnishchuk/nsctl` (to be created)

**Relationship to dotfiles:** nsctl is installed globally via
`uv tool install nsctl` and is available on every host. The
`dotfiles` repo ships a thin bash shim (`bashrc.d/55-nsctl-switch.sh`)
that wraps `nsctl switch` with `eval` so it can mutate the parent
shell's environment. The `dotfiles` repo also ships the
`dotfiles-id-template` repo reference that `nsctl new` clones from.

---

## Tech stack

- **Python ≥ 3.12** (whatever the current `ty` floor is)
- **typer** — CLI framework (subcommand routing, help, shell completion)
- **pydantic** — data models for `namespace.toml`, key metadata `.toml`,
  sync log entries, device registry
- **cryptography** — SSH/GPG key generation, age-equivalent envelope
  encryption, fingerprint computation
- **rich** — pretty terminal output (tables, status, progress, tree views)
- **httpx** — GitHub API calls when `gh` CLI isn't available
- **tomli / tomllib** — TOML parsing (stdlib in 3.11+)
- **uv** — venv management, dependency resolution, tool install
- **ruff** — lint + format
- **ty** — type checking
- Tests: **pytest** + **pytest-cov**

---

## Core concepts

### Namespace = pass store + extras

Each namespace is a private git repo with this layout:

```
~/dotfiles-id-<name>/                          # cloned from the private repo
├── namespace.toml                              # pydantic-validated metadata
├── pyproject.toml                              # optional: per-namespace Python tools
├── uv.lock                                     # lockfile for the above
├── .gpg-id                                     # pass: the namespace's GPG fingerprint(s)
├── .gitignore                                  # deny-list for plaintext keys
│
├── (pass entries — managed by `pass insert` etc.)
├── aws/
│   └── default.gpg
├── github/
│   └── token.gpg
├── ...
│
├── bashrc.d/
│   └── 50-id-<name>.sh                         # env exports for this namespace
├── ssh/
│   └── config.d/
│       └── 10-id-<name>.conf
│
├── keys/                                       # private-key material (encrypted)
│   ├── ssh/
│   │   ├── id_ed25519.age                      # encrypted to recipients.txt
│   │   ├── id_ed25519.pub
│   │   └── id_ed25519.toml                     # key metadata (see below)
│   ├── gnupg/
│   │   ├── private-keys-export.age
│   │   ├── keystone.toml                       # metadata for the namespace GPG key
│   │   ├── pubring/<fpr>.asc
│   │   └── revocation/*.asc
│   └── README.md
│
├── recipients.txt                              # age recipient pubkeys, one per device
├── sync/                                       # append-only audit log
│   └── YYYY-MM-DD-HHMMSS-<device>.log
│
└── deploy-keys/
    ├── README.md
    └── <device-label>.pub
```

### namespace.toml (pydantic model)

```toml
schema_version = 1
name = "work-acme"
description = "ACME Corp client engagement"
created_at = "2026-04-10T03:14:15Z"
created_on = "g94"

keystone_gpg_fingerprint = "0xABCD1234..."

[lifecycle]
valid_until = ""                  # blank = no hard expiry
rotation_cadence_days = 365

[venv]
enabled = true
python = "3.13"

[browser]
enabled = true
type = "firefox"                  # or "chrome"
profile_name = "id-work-acme"

[prompt]
color = "red"                     # PS1 color when this namespace is active
marker = "work-acme"              # text shown in prompt

[aws]
enabled = true
region = "us-east-1"
```

### Per-key metadata (.toml)

Every private key in `keys/` gets a sibling `.toml`:

```toml
schema_version = 1
kind = "ssh"                      # or "gpg", "age"
algorithm = "ed25519"
fingerprint_sha256 = "SHA256:abc123..."
public_key = "ssh-ed25519 AAAA..."
comment = "work-acme@g94"

[lifecycle]
created_at = "2026-04-10T03:14:15Z"
created_on = "g94"
rotated_at = "2026-04-10T03:14:15Z"
rotation_cadence_days = 365
expires_at = ""

[purpose]
description = "SSH key for ACME infra"
hardware_backed = false
keystone = false

[registrations]
github = ["acme-corp"]
servers = ["bastion.acme.com"]

[[history]]
at = "2026-04-10T03:14:15Z"
device = "g94"
action = "created"
note = "initial generation by nsctl new"
```

---

## CLI commands

```
nsctl list                        — show all namespaces (cloned, available, disabled)
nsctl current                     — print the active namespace
nsctl new <name> [options]        — create a new namespace from template
    --remote URL                    github remote (default: gh repo create)
    --browser firefox|chrome        link a browser profile
    --no-venv                       skip Python venv setup
    --no-aws                        skip AWS profile setup
nsctl add <name> [--remote URL]   — clone an existing namespace onto this device
    --readonly                      read-only deploy key (no push)
    --no-venv                       skip venv
    --only SUBTREE,...              selective sync (e.g. --only aws,github)
nsctl remove <name> [--force]     — remove local clone + per-namespace HOMEs
nsctl disable <name>              — keep clone, drop from active TAGS
nsctl enable <name>               — opposite of disable
nsctl switch <name>               — print env exports for eval by shell wrapper
nsctl deactivate                  — print env restore for eval by shell wrapper

nsctl sync [<name>]               — git pull --ff-only + uv sync + age-decrypt
                                    appends to sync/ audit log
                                    refuses non-fast-forward (append-only invariant)
nsctl rotate <name> [--ssh|--gpg|--all]
                                  — generate new keypair, re-encrypt, append-only
                                    commit, push; print registrations to update
nsctl lock <name>                 — wipe unlocked GNUPGHOME/SSH dir/venv from disk
nsctl unlock <name>               — re-decrypt from the namespace repo

nsctl device add <name> [--label LABEL]
                                  — generate device key, register as deploy key +
                                    age recipient, re-encrypt, push
nsctl device remove <name> --label LABEL
                                  — revoke device access, re-encrypt to reduced
                                    recipient set (append-only: old commits stay)

nsctl export <name> --to <file>   — portable encrypted bundle for bootstrapping
                                    a new device without an existing deploy key
nsctl import <file>               — opposite of export

nsctl search <term>               — fzf across pass entries in all enabled namespaces
nsctl get <namespace>/<path>      — convenience over `pass show`
nsctl audit <name>                — rich table of keys, ages, registrations, rotation status
nsctl history <name>              — git log of the namespace repo, formatted
nsctl kill <name>                 — emergency: publish revocation certs, remove deploy
                                    keys, optionally delete remote repo

nsctl doctor                      — sanity-check all enabled namespaces:
                                    key fingerprints match metadata
                                    deploy key for this device is registered
                                    no plaintext key files on disk
                                    venv matches pyproject.toml
                                    sync log is monotonic
                                    rotation cadence not exceeded
                                    valid_until not past
nsctl doctor --fix                — auto-correct what it safely can
```

---

## Shell integration

A thin bash shim in `dotfiles/bashrc.d/55-nsctl.sh`:

```bash
ns() {
  case "$1" in
    switch|deactivate)
      eval "$(command nsctl "$@")"
      ;;
    *)
      command nsctl "$@"
      ;;
  esac
}
```

So `ns switch work-acme` evals the env exports into the current shell.
Everything else delegates to the Python binary unchanged.

---

## Per-namespace venv

- Venv location: `~/.local/share/nsctl/venv/<name>/`
- Declared by: `pyproject.toml` at the namespace repo root
- Lockfile: `uv.lock` committed to the namespace repo
- Materialized by: `nsctl new`, `nsctl add`, `nsctl sync` (runs `uv sync`)
- Activated by: `nsctl switch` (sets `VIRTUAL_ENV`, prepends bin to `PATH`)
- Deactivated by: `nsctl deactivate` or `nsctl switch <other>`
- Skipped if: `--no-venv` on `nsctl add`, or `[venv] enabled = false` in
  `namespace.toml`, or no `pyproject.toml` in the namespace repo
- Python version per namespace via `[venv] python = "3.13"` → `uv venv
  --python 3.13`

---

## Security model

### Append-only sync

1. `nsctl sync` enforces `git pull --ff-only` — refuses non-fast-forward.
2. Every sync writes a timestamped device-labeled log entry to `sync/`.
3. `nsctl new` configures github branch protection (via `gh api`) to
   forbid force-push on the default branch.
4. Revoking a leaked key = rotation, not history erasure. Old encrypted
   blobs stay in git history; the key they were encrypted to is revoked.

### Per-device access control

- Each device has its own deploy key (SSH, registered via `gh repo
  deploy-key add`) for git push/pull.
- Each device has its own age keypair; device pubkey listed in the
  namespace's `recipients.txt`.
- Secret blobs in `keys/` are age-encrypted to the union of recipients.
- Adding a device = append pubkey + re-encrypt + push.
- Removing a device = drop pubkey + re-encrypt + push (old commits
  where the device WAS a recipient are NOT rewritten).
- `--readonly` deploy keys = git read-only scope (github supports this).

### Nested passphrases

Each namespace's GPG key has its own passphrase. The passphrase is
stored as a `pass` entry in the default (personal) namespace:
`pass show nsctl/passphrases/work-acme`. So unlocking `work-acme`
requires already being in `personal`. Single keystone, layered defense.

### Time-bound namespaces

`namespace.toml` can declare `valid_until = "2026-12-31"`. `nsctl
doctor` warns when expired. `nsctl sync` refuses past expiry unless
`--force`.

### YubiKey / hardware token support

Key metadata `.toml` has `hardware_backed = true` and
`smartcard_serial = "12345678"`. `nsctl rotate` knows not to try to
extract the private key from a hardware token. `nsctl doctor` checks
the token is plugged in if the namespace is hardware-backed.

---

## Template repo: `dotfiles-id-template`

A public repo at `github.com/IvanAnishchuk/dotfiles-id-template`
containing the skeleton for a new namespace. `nsctl new` does
`gh repo create --template ... --private ...` then clones and runs
the bootstrap logic (key generation, `pass init`, template
substitution). The template has:

```
dotfiles-id-template/
├── README.md.tmpl
├── namespace.toml.tmpl
├── pyproject.toml.tmpl
├── .gpg-id.tmpl
├── .gitignore
├── bashrc.d/
│   └── 50-id-IDENTITY.sh.tmpl
├── ssh/
│   └── config.d/
│       └── 10-id-IDENTITY.conf.tmpl
├── keys/
│   ├── .gitkeep
│   ├── .gitignore
│   └── README.md
├── recipients.txt
├── sync/
│   └── .gitkeep
└── deploy-keys/
    └── README.md
```

`nsctl new` replaces `IDENTITY` placeholders with the actual name.

---

## Integration with the dotfiles ecosystem

- **rcm:** each namespace repo contributes a `tag-id-<name>/` overlay
  via `DOTFILES_DIRS`. `nsctl new/add` appends the repo path to
  `DOTFILES_DIRS` in `~/.rcrc` and adds `id-<name>` to `TAGS`.
- **dotfiles-status (login greeting):** reports "namespace: personal |
  last sync: 2h ago | 2 namespaces have pending pulls".
- **dotfiles-doctor:** calls `nsctl doctor` as one of its checks.
- **install.sh:** `uv tool install nsctl` is part of the bootstrap.
- **tools-sync:** global (non-namespace) Python/npm tools; separate
  from per-namespace venvs.

---

## Packaging

```
nsctl/
├── pyproject.toml                # project metadata, dependencies, entry points
├── uv.lock
├── src/
│   └── nsctl/
│       ├── __init__.py
│       ├── cli.py                # typer app, subcommand routing
│       ├── models.py             # pydantic models (NamespaceConfig, KeyMetadata, etc.)
│       ├── namespace.py          # create, add, remove, disable, enable
│       ├── switch.py             # env-var generation for switch/deactivate
│       ├── sync.py               # pull, push, append-only enforcement
│       ├── keys.py               # generate, rotate, encrypt, decrypt
│       ├── device.py             # add, remove, deploy-key management
│       ├── venv.py               # uv venv lifecycle
│       ├── doctor.py             # health checks
│       ├── audit.py              # key inventory, history, rotation status
│       ├── export_import.py      # portable bundle creation/consumption
│       ├── kill.py               # emergency revocation
│       ├── search.py             # cross-namespace pass search
│       ├── github.py             # gh CLI / httpx wrappers
│       ├── age.py                # age encryption helpers (via cryptography or pyrage)
│       ├── gpg.py                # GPG key generation / import / export
│       ├── ssh.py                # SSH key generation
│       ├── config.py             # global nsctl config (~/.config/nsctl/config.toml)
│       └── defaults.py           # rotation cadences, default python version, etc.
├── tests/
│   ├── conftest.py
│   ├── test_namespace.py
│   ├── test_keys.py
│   ├── test_sync.py
│   ├── test_doctor.py
│   └── ...
└── README.md
```

Install: `uv tool install nsctl` (from PyPI or from local checkout).

---

## Open design questions

1. **age vs GPG for blob encryption in `keys/`.** age is simpler
   (no keyservers, no trust model, no subkey dance). But the user
   already has GPG everywhere and pass uses GPG natively. Could
   use age for blob encryption and GPG for pass entries — two tools,
   clean separation. Or unify on GPG. Recommendation: age for blobs,
   GPG for pass. Revisit if `pyrage` or `cryptography` can do both
   without shelling out.

2. **Should `nsctl` shell out to `pass` or reimplement pass's
   functionality?** Shell out. `pass` is well-tested, the user
   already uses it, and re-implementing GPG-encrypted file CRUD
   is a lot of surface area for no gain. `nsctl` is an orchestrator,
   not a replacement.

3. **Should `nsctl` shell out to `gh` or use httpx directly?**
   Default to `gh` when available (it handles auth, pagination,
   rate limiting). Fall back to httpx + `GITHUB_TOKEN` env var
   when `gh` isn't installed (servers, CI).

4. **Global nsctl config location.** `~/.config/nsctl/config.toml`
   for user-global settings (default git host, default template
   repo URL, default rotation cadences, device label for this
   machine). Pydantic model. Created by `nsctl init` or
   auto-populated with defaults on first run.

5. **Should `nsctl` manage `~/.rcrc` directly (append to TAGS /
   DOTFILES_DIRS)?** Yes, via a small `rcrc.py` helper that
   parses the shell-variable format, modifies, and rewrites.
   The rcrc file is simple enough (POSIX shell vars) that this
   is safe. Alternative: just print instructions and let the
   user edit manually. Recommendation: auto-edit with a backup.

6. **Publish to PyPI?** Eventually, but not on day one. Start as
   `uv tool install --from ~/nsctl nsctl` (local checkout) or
   `uv tool install --from git+ssh://github.com/... nsctl`.
   Publish to PyPI when it's stable enough for others to use.

---

## Milestones

### v0.1 — MVP (start here)

- `nsctl new`, `nsctl add`, `nsctl remove`
- `nsctl switch`, `nsctl deactivate` (env-var generation)
- `nsctl sync` (append-only `git pull --ff-only`)
- `nsctl list`, `nsctl current`
- `namespace.toml` + pydantic model
- Key generation (SSH ed25519 + GPG) via `cryptography`
- Key metadata `.toml` files
- Shell shim (`ns` wrapper)
- Template repo skeleton
- Basic tests

### v0.2 — Device management + rotation

- `nsctl device add`, `nsctl device remove`
- `nsctl rotate` (SSH + GPG)
- age recipient list management
- `recipients.txt` re-encryption on device add/remove
- Deploy-key registration via `gh`

### v0.3 — Polish + safety

- `nsctl doctor`, `nsctl doctor --fix`
- `nsctl audit`, `nsctl history`
- `nsctl lock`, `nsctl unlock`
- Per-namespace venv lifecycle (`uv sync` on `nsctl sync`)
- Browser profile creation
- Shell completion (typer auto-generates)
- Prompt color per namespace

### v0.4 — Advanced features

- `nsctl export`, `nsctl import`
- `nsctl search` (cross-namespace fzf)
- `nsctl kill` (emergency revocation)
- Namespace bundles (meta-repo for multi-namespace device setup)
- Time-bound namespaces (`valid_until`)
- YubiKey / hardware token support in key metadata + doctor
- Background sync via systemd user timer
- Integration with `dotfiles-status` login greeting

---

## Relationship to the dotfiles modernization plan

nsctl was originally subsystem 9b in the dotfiles modernization
strategy (`~/dotfiles/.claude/plans/nested-sauteeing-fox.md`). It
grew large enough to warrant its own repo and development lifecycle.

The dotfiles plan's Phase B references nsctl at these points:

- **B4** (Python helpers via uv): `install.sh` runs
  `uv tool install nsctl` alongside `dotfiles-tools`
- **B5** (SSH host inventory): per-namespace `ssh/config.d/` fragments
  are managed by `nsctl new/add`, not manually
- **B7** (GPG backup chain + pass setup): replaced entirely by
  nsctl's per-namespace key lifecycle + metadata + rotation
- **B8** (Debian VM bootstrap): `nsctl add personal` is part of
  the bootstrap flow
- **B9** (Cloud variant): `nsctl add personal --no-venv --readonly`
  for throwaway VMs

The leaked-key rotation (dotfiles plan task #2) should wait until
nsctl v0.2 (`nsctl rotate`) exists, so new keys go directly into
the namespace structure rather than the old monolithic `~/.gnupg`.

---

## Prior art / inspiration

- `pass` (password-store.org) — the underlying secret store
- `direnv` — per-directory env activation (nsctl is per-namespace)
- `tox` / `nox` — multi-env Python test runners (venv-per-context idea)
- `1Password CLI` / `op` — namespace-like "vaults" with per-device access
- `age` — simple file encryption with recipient lists
- `chezmoi` — dotfile manager with secret management (different approach)
