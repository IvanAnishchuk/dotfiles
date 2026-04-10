# nsctl — Namespace/Identity Management Tool

## What this is

`nsctl` is a standalone Python CLI tool for managing isolated identity
namespaces. Each namespace is a `pass` store (git repo) with extra
files alongside it — GPG keyring, SSH key set, uv-managed Python venv,
AWS profiles, browser profile, key metadata, GPG-encrypted sync blobs,
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
- **cryptography** — SSH key generation, fingerprint computation,
  potential future encryption backends
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
│   │   ├── id_ed25519.gpg                      # encrypted to all device enc subkeys
│   │   ├── id_ed25519.pub
│   │   └── id_ed25519.toml                     # key metadata (see below)
│   ├── gnupg/
│   │   ├── private-keys-export.gpg
│   │   ├── keystone.toml                       # metadata for the namespace GPG key
│   │   ├── pubring/<fpr>.asc
│   │   └── revocation/*.asc
│   └── README.md
│
├── devices/                                    # per-device GPG public keys (recipients)
│   ├── README.md
│   ├── g94.gpg-pub                             # armored GPG pubkey (with Curve25519 enc subkey)
│   ├── g94.deploy-key.pub                      # SSH deploy key for git push/pull
│   ├── pixel-phone.gpg-pub
│   ├── pixel-phone.deploy-key.pub
│   └── ...
│
├── sync/                                       # append-only audit log
│   └── YYYY-MM-DD-HHMMSS-<device>.log
│
└── .gpg-trust                                  # ownertrust for all device keys in this
                                                 # namespace (imported into per-ns GNUPGHOME)
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

[encryption]
backend = "gpg"               # "gpg" (v0.1), future: "age", "hpke", "sops", "kms"
# kms_key_arn = ""            # only for backend = "sops" or "kms"
# hpke_kem = "X25519"         # only for backend = "hpke"
# hpke_kdf = "HKDF-SHA256"
# hpke_aead = "ChaCha20Poly1305"
```

### Per-key metadata (.toml)

Every private key in `keys/` gets a sibling `.toml`:

```toml
schema_version = 1
kind = "ssh"                      # or "gpg-sign", "gpg-encrypt", "gpg-primary"
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

nsctl sync [<name>]               — git pull --ff-only + uv sync + gpg-decrypt
                                    imports device pubkeys from devices/*.gpg-pub
                                    appends to sync/ audit log
                                    refuses non-fast-forward (append-only invariant)
nsctl rotate <name> [--ssh|--gpg|--all]
                                  — generate new keypair, re-encrypt, append-only
                                    commit, push; print registrations to update
nsctl lock <name>                 — wipe unlocked GNUPGHOME/SSH dir/venv from disk
nsctl unlock <name>               — re-decrypt from the namespace repo

nsctl device add <name> [--label LABEL]
                                  — generate per-device GPG keypair (Curve25519
                                    encryption + ed25519 signing subkeys) + SSH
                                    deploy key; export pubkey to devices/<label>.gpg-pub
                                    and devices/<label>.deploy-key.pub; register
                                    deploy key via gh; re-encrypt all keys/*.gpg to
                                    include the new device; push
nsctl device remove <name> --label LABEL
                                  — remove device pubkey from devices/, re-encrypt
                                    keys/*.gpg to the reduced recipient set, revoke
                                    the deploy key via gh API (append-only: old
                                    commits where the device WAS a recipient stay)

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

### Per-device keys and access control

Each device generates **three separate keypairs** on `nsctl device add`:

| Key | Type | Purpose |
|---|---|---|
| GPG encryption subkey | Curve25519 | **recipient key** for `keys/*.gpg` blobs |
| GPG signing subkey | ed25519 | signs commits to the namespace repo |
| SSH deploy key | ed25519 | git push/pull access to the namespace repo on github |

Optionally a fourth **SSH auth key** (ed25519) for authenticating to
servers listed in the namespace's `ssh/config.d/`. This is separate
from the deploy key because deploy keys are scoped to one github repo
while auth keys are scoped to whatever servers the namespace cares about.

All per-device keys are **separate from the namespace's identity GPG
key** (the one in `.gpg-id` that `pass` encrypts to). The identity key
is "who is this namespace"; the device keys are "which machines can read
the backup blobs".

**Recipient model:** secret blobs in `keys/` are GPG-encrypted to the
union of all device encryption subkeys:

```bash
gpg --homedir ~/.gnupg-<ns> --trust-model always \
    --encrypt --armor \
    --recipient <device1-enc-fpr> \
    --recipient <device2-enc-fpr> \
    --output keys/ssh/id_ed25519.gpg \
    keys/ssh/id_ed25519
```

The `--trust-model always` is scoped to the per-namespace GNUPGHOME so
device keys are trusted unconditionally within their own namespace
(each namespace's keyring contains only its own devices, not the
global trust database).

**Device pubkeys** live in `devices/<label>.gpg-pub` (armored GPG
public key export) and `devices/<label>.deploy-key.pub` (SSH). Adding
a device = export pubkey + import into namespace GNUPGHOME + re-encrypt
blobs + register deploy key via `gh` + push. Removing = drop + re-encrypt
+ revoke deploy key (old commits where the device WAS a recipient stay —
append-only invariant).

`--readonly` deploy keys use github's read-only deploy key scope for
devices that should pull but never push (phones, CI runners).

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

## Encryption backend: evaluation and future options

**Current decision (2026-04-10):** GPG for everything. Per-device
Curve25519 encryption subkeys as recipients. No additional tool.

The `namespace.toml` schema includes `[encryption] backend = "gpg"`
to make the backend swappable later without changing the namespace
layout. The following backends were evaluated:

### GPG (chosen, v0.1+)

Per-device Curve25519 encryption subkeys. `gpg --encrypt -r <fpr>
-r <fpr> ...` for multi-recipient. Per-namespace GNUPGHOME with
`--trust-model always` for unconditional device trust within each
namespace.

- **Pros:** already everywhere (`pass` uses it, git signing uses it,
  the keystone is GPG); no additional dependency; mature; hardware
  token support built in; the `cryptography` Python library can
  generate GPG-compatible keys; `python-gnupg` wrapper exists for
  automation.
- **Cons:** verbose CLI; trust model ceremony (mitigated by
  `--trust-model always` per namespace); `python-gnupg` is fragile
  (subprocess wrapper over `gpg` CLI, not a library); error messages
  are notoriously unhelpful; adding/removing recipients requires
  re-encryption of every blob.
- **When to reconsider:** if the number of devices grows large
  (>10) and re-encryption latency becomes annoying; if `python-gnupg`
  breaks on a gpg version upgrade; if a use case emerges where the
  GPG trust model actively gets in the way.

### age (deferred, potential v0.5+)

Simple recipient-based encryption. `age -R recipients.txt -o out.age
in`. Native support for SSH public keys as recipients (no extra key
type). `pyrage` for Python bindings, or shell out to `age` / `rage`.

- **Pros:** dead simple API; SSH-key-as-recipient means zero extra
  key management; no trust model at all; well-audited; widely
  adopted in infra/devops; `recipients.txt` is a plain text file.
- **Cons:** extra tool to install (`app-crypt/age` on Gentoo,
  unstable on Debian); `pyrage` is less mature than `cryptography`;
  doesn't do signing (need GPG for that anyway); diverges from the
  "GPG for everything" simplicity.
- **When it becomes compelling:** if the project wants to drop the
  GPG dependency for encryption (keeping it only for `pass` and
  signing); if SSH-key-as-recipient eliminates the per-device GPG
  keypair generation step; if the user wants a tool that doesn't
  carry GPG's historical baggage.

### Pure `cryptography` library (deferred, potential v0.5+)

X25519 key agreement + ChaCha20-Poly1305 (or AES-GCM). Custom
multi-recipient envelope format modeled on age's internal structure.

- **Pros:** zero external tool dependency; `cryptography` is already
  pinned; full control; can add features (streaming, chunking,
  metadata headers).
- **Cons:** designing a crypto protocol (envelope format, nonce
  handling, key derivation, versioning) is new attack surface even
  with safe primitives; more code to audit; not battle-tested.
- **When it becomes compelling:** if both GPG and age prove too
  heavy or too flaky for the automation needs; if the project wants
  a single-binary story with no subprocess calls.

### SOPS (Mozilla) (deferred, potential v0.5+ for work namespaces)

Structured file encryption with pluggable backends (age, GPG, AWS
KMS, GCP KMS, HashiCorp Vault, Azure Key Vault). Format-aware:
encrypts values but leaves keys readable in YAML/JSON/ENV/INI.

- **Pros:** multi-backend — personal namespaces use GPG keys, work
  namespaces use the employer's AWS KMS (audit-logged, IAM-revocable,
  no key material on disk); `git diff` shows which field changed.
- **Cons:** designed for structured config, not arbitrary binary
  blobs (SSH private keys aren't YAML — needs base64 wrapping);
  heavier dependency; overkill for personal use.
- **When it becomes compelling:** when a work namespace has access
  to a cloud KMS and the employer wants audit-logged, IAM-controlled
  access to credentials. At that point `namespace.toml` declares
  `[encryption] backend = "sops"` and `kms_key_arn = "arn:aws:..."`.

### Cloud KMS directly (deferred, potential v0.5+ for work namespaces)

Envelope encryption with AWS KMS or GCP KMS via the cloud SDKs.
The master key lives in the cloud provider's HSM; the data key is
encrypted locally.

- **Pros:** hardware-backed (HSM), audit-logged (CloudTrail/
  Cloud Audit), access-revocable from IAM without key rotation,
  the cloud provider handles key lifecycle.
- **Cons:** cloud-dependent (doesn't work offline, which personal
  namespaces require); vendor-specific; requires cloud SDK + auth
  configured; inappropriate for personal/offline namespaces.
- **When it becomes compelling:** same as SOPS but for namespaces
  that don't need the structured-file features — just raw envelope
  encryption with a cloud-managed master key.

### HPKE — Hybrid Public Key Encryption (deferred, potential v0.5+)

RFC 9180. A modern IETF standard for public-key encryption that
combines a KEM (Key Encapsulation Mechanism, e.g. X25519 or
P-256), a KDF (e.g. HKDF-SHA256), and an AEAD (e.g. AES-GCM or
ChaCha20-Poly1305) into a single composable construction. The
`cryptography` library has HPKE support since v41.

- **Pros:** IETF-standardized (RFC 9180) — not a bespoke protocol;
  the `cryptography` library implements it natively (no subprocess,
  no extra tool); multi-recipient via multiple KEM encapsulations
  (same pattern as age internally); lightweight — just a library
  call, no GPG daemon, no trust model, no keyring; X25519-based,
  so Curve25519 device keys can be reused or derived; the
  construction is formally analyzed.
- **Cons:** no established file format convention (age has `.age`,
  GPG has `.gpg` — HPKE would need a custom envelope format, or
  adopt the age format with an HPKE KEM); no CLI tool (pure library
  use only — fine for nsctl but means no `hpke encrypt foo.txt`
  one-liner for manual debugging); less community adoption than
  age/GPG for file encryption specifically (HPKE is more commonly
  used in TLS 1.3, MLS, and protocol-level encryption).
- **When it becomes compelling:** if the project wants a
  standards-based encryption layer with zero external tool
  dependencies and the `cryptography` library is already pinned.
  HPKE + a thin envelope format (header with per-recipient
  encapsulated keys, body AEAD-encrypted with the shared secret)
  is essentially "age but IETF-blessed and library-native".
  Strongest candidate for replacing GPG blob encryption long-term.

### Certificate Transparency / Key Transparency standards (future research)

Transparency logs (RFC 6962 for CT, Key Transparency proposals
from Google/Apple) provide **append-only, publicly auditable,
cryptographically verifiable logs** of key-related events. While
designed for TLS certificates and messaging keys respectively,
the underlying data structures (Merkle trees with signed tree
heads, inclusion/consistency proofs) are directly applicable to
nsctl's append-only sync invariant.

- **Potential application to nsctl:** instead of relying on git
  history + branch protection as the append-only log, publish
  key lifecycle events (creation, rotation, revocation, device
  add/remove) to a transparency log. This gives a third-party-
  verifiable audit trail that doesn't depend on the git host's
  integrity. A `nsctl audit --verify` command could check that
  the local git history matches the transparency log.
- **Concrete options:**
  - **Sigstore / Rekor** — an existing public transparency log
    for software signing. nsctl could log key rotation events
    to Rekor as signed attestations. Free, public, already
    operational.
  - **A self-hosted transparency log** via `trillian` (Google's
    open-source Merkle tree implementation) for users who want
    a private log.
  - **Git-native Merkle proofs** — git's object model is already
    a Merkle DAG. The append-only invariant we enforce via
    `--ff-only` + branch protection is a weaker form of the same
    guarantee. A transparency log adds *external* witnessing.
- **When it becomes compelling:** when the threat model includes
  "what if the git host is compromised and rewrites history
  silently". For personal use this is unlikely; for work
  namespaces with compliance requirements (SOC2, FedRAMP) it
  could be a real value-add. Also relevant if nsctl ever becomes
  a multi-user tool (team namespaces) where members need to
  verify each other's key operations.
- **Not in scope for v0.1–v0.4.** Record as a future research
  direction. The `EncryptionBackend` protocol doesn't directly
  cover transparency (it's orthogonal — transparency is about
  auditability, not confidentiality), so this would be a separate
  `AuditBackend` protocol or a `transparency/` module.

### Personal CA / certificate management via step-ca (future research)

`step-ca` (Smallstep) is an open-source online Certificate Authority
that can issue short-lived X.509 and SSH certificates. Relevant to
nsctl because:

- **SSH certificates instead of raw keys.** Instead of distributing
  `authorized_keys` entries per device, a namespace could run (or
  reference) a step-ca that issues short-lived SSH user certificates.
  Servers trust the CA public key; devices get certificates on demand
  (via `step ssh certificate`). This eliminates `authorized_keys`
  management and gives automatic expiry without key rotation.
- **TLS client certificates for internal services.** A work namespace
  could issue client certs from its own CA for mTLS to internal APIs,
  dashboards, or git forges. The cert is scoped to the namespace and
  expires with it (if time-bound).
- **Per-namespace CA.** Each namespace could have its own step-ca root
  (either a local offline root whose key is the namespace's GPG-
  encrypted keystone, or a remote step-ca instance). Certificates
  issued under one namespace's CA are not valid in another — same
  isolation principle as everything else.
- **Integration shape:** `nsctl cert issue <namespace> --type ssh
  --principal <user>` calls `step ssh certificate` against the
  namespace's CA. `nsctl cert issue <namespace> --type tls --san
  <hostname>` calls `step ca certificate`. The CA's root key is
  stored as a `pass` entry or in `keys/ca/` encrypted to the device
  recipients.
- **When it becomes compelling:** when the user manages enough servers
  that `authorized_keys` distribution is painful (homelab growth),
  or when a work namespace needs mTLS for internal services, or
  when short-lived SSH certs are preferable to long-lived keys for
  compliance reasons.
- **Dependencies:** `step-cli` (Go binary, available on Gentoo and
  most distros), `step-ca` (only needed if running the CA locally —
  can also point at a remote instance). Both are open-source
  (Apache 2.0).
- **Not in scope for v0.1–v0.4.** Record as a future capability.
  The namespace layout can accommodate a `ca/` subtree alongside
  `keys/` when the time comes.

### Backend abstraction in code

The `nsctl` codebase should have a `backends/` package:

```
src/nsctl/backends/
├── __init__.py          # EncryptionBackend protocol (encrypt, decrypt,
│                         #   add_recipient, remove_recipient, list_recipients)
├── gpg.py               # v0.1: the default
├── age.py               # stub / future
├── sops.py              # stub / future
└── kms.py               # stub / future
```

Each backend implements the same `EncryptionBackend` protocol (a
Python Protocol class with `encrypt()`, `decrypt()`,
`add_recipient()`, `remove_recipient()`, `list_recipients()`).
`namespace.toml`'s `[encryption] backend = "gpg"` selects which
implementation to use. The rest of nsctl doesn't care about the
backend's internals — it calls the protocol methods.

This means adding a new backend later is one new file + one
`namespace.toml` field value, not a rewrite.

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
├── devices/
│   └── README.md
├── sync/
│   └── .gitkeep
└── .gpg-trust
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
│       ├── backends/             # encryption backend implementations
│       │   ├── __init__.py      # EncryptionBackend protocol
│       │   ├── gpg.py           # v0.1 default
│       │   ├── age.py           # future
│       │   ├── hpke.py          # future
│       │   ├── sops.py          # future
│       │   └── kms.py           # future
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

1. **Encryption backend.** RESOLVED: GPG for v0.1 (per-device
   Curve25519 encryption subkeys). The `EncryptionBackend` protocol
   abstraction makes age / SOPS / KMS backends addable later without
   refactoring. See "Encryption backend: evaluation and future
   options" above for the full evaluation.

2. **Should `nsctl` shell out to `pass` or reimplement pass's
   functionality?** Shell out. `pass` is well-tested, the user
   already uses it, and re-implementing GPG-encrypted file CRUD
   is a lot of surface area for no gain. `nsctl` is an orchestrator,
   not a replacement.

3. **Should `nsctl` shell out to `gh` or use httpx directly?**
   Default to `gh` when available (the user has `gh` installed
   locally and uses it; it handles auth, pagination, rate limiting).
   Fall back to httpx + `GITHUB_TOKEN` env var when `gh` isn't
   installed (servers, CI).

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

7. **`python-gnupg` vs shelling out to `gpg` directly.** Both
   are subprocess wrappers ultimately. `python-gnupg` adds a
   thin OO layer but is notoriously brittle across `gpg` versions.
   Alternative: write a small `nsctl/gpg.py` that calls
   `subprocess.run(["gpg", ...])` directly with structured
   argument building — more verbose but more debuggable. The
   `cryptography` library can generate key material (ed25519,
   X25519) natively but can't drive `gpg` operations (import,
   encrypt, sign). Recommendation: start with direct subprocess,
   consider `python-gnupg` if the boilerplate gets excessive.

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
- Per-device GPG Curve25519 encryption subkey management
- Re-encryption of `keys/*.gpg` on device add/remove
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
- `age` / `rage` — simple recipient-based file encryption (potential future backend)
- `chezmoi` — dotfile manager with secret management (different approach)
- RFC 9180 (HPKE) — IETF standard for hybrid public-key encryption (potential future backend)
- RFC 6962 (Certificate Transparency) — append-only Merkle-tree audit logs
- Key Transparency (Google/Apple proposals) — transparency logs for identity keys
- Sigstore / Rekor — public transparency log for signing events
- SOPS (Mozilla) — structured file encryption with pluggable KMS backends
- `trillian` (Google) — open-source Merkle tree for self-hosted transparency logs
- `step-ca` / `step-cli` (Smallstep) — open-source CA for SSH certs + X.509, potential per-namespace CA
- HPKE (RFC 9180) via Python `cryptography` — native hybrid public-key encryption without external tools
