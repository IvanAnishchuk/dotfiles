# Manual Verification Plan

Everything below assumes you're on `g94` with the current dotfiles
checkout at `~/dotfiles` (master, tip `b5763c5`).

---

## 1. Verify rcm symlinks are intact

```bash
# Every file here should be a symlink pointing into ~/dotfiles or ~/dotfiles-local
for f in ~/.bashrc ~/.bashrc.local ~/.aliases ~/.bash_logout ~/.profile \
         ~/.psqlrc ~/.tmux.conf ~/.inputrc ~/.ctags ~/.rcrc \
         ~/.config/git/config ~/.config/git/config.local \
         ~/.config/git/ignore ~/.config/git/message \
         ~/.config/nvim/init.lua; do
  if [ -L "$f" ]; then
    echo "OK  $f -> $(readlink "$f")"
  else
    echo "BAD $f is NOT a symlink"
  fi
done
```

Expected: all OK. If any say BAD, run:
```bash
env RCRC=$HOME/dotfiles/rcrc rcup -v \
  -x README.md -x LICENSE -x CLAUDE.md -x archive \
  -x ssh -x gnupg -x bin -x fonts -x 'config/mpv'
```

## 2. Verify shell environment loads correctly

```bash
# Open a fresh interactive shell and check key variables
bash -ic '
  echo "EDITOR=$EDITOR"
  echo "VISUAL=$VISUAL"
  echo "EMAIL=$EMAIL"
  echo "GPG_TTY=$GPG_TTY"
  echo "SSH_AUTH_SOCK=$SSH_AUTH_SOCK"
  echo "vi mode: $(bind -v 2>/dev/null | grep editing-mode)"
  type vim
  echo "PATH has cargo: $(echo $PATH | tr : "\n" | grep -c cargo)"
  echo "PATH has foundry: $(echo $PATH | tr : "\n" | grep -c foundry)"
'
```

Expected:
- `EDITOR=nvim`, `VISUAL=nvim`
- `EMAIL=ivan@agorism.org`
- `SSH_AUTH_SOCK=/run/user/1000/gnupg/S.gpg-agent.ssh`
- `vim` is aliased to `nvim -p`
- cargo and foundry in PATH

## 3. Verify git identity and signing

```bash
git config user.name        # Ivan Anishchuk
git config user.email       # ivan@agorism.org
git config user.signingkey  # 0xE27325A392D70FFB
git config commit.gpgsign   # true

# Test signing works
echo "test" | gpg --clearsign | tail -3   # should show END PGP SIGNATURE

# Test the template dir is set correctly
git config init.templatedir  # ~/.config/git_template
ls ~/.config/git_template/hooks/  # should list ctags, post-checkout, etc.
```

## 4. Verify neovim

```bash
# Quick health check
nvim --headless +'checkhealth provider' +qa 2>&1 | grep -E 'python|OK|ERROR'

# Verify vim-plug is installed
ls ~/.config/nvim/autoload/plug.vim  # should exist

# Open a Python file and check LSP attaches
nvim ~/.config/nvim/init.lua
# Inside nvim:  :LspInfo   → should show ruff and/or ty attached
#               :PlugStatus → should show installed plugins
#               :q
```

## 5. Verify GPG agent provides SSH

```bash
ssh-add -L    # should list at least one key (the ed25519)
ssh -T git@github.com 2>&1  # "Hi IvanAnishchuk! You've successfully authenticated"
```

## 6. Verify the git_template hooks

```bash
# Create a test repo to verify the template propagates
cd /tmp && mkdir test-template-repo && cd test-template-repo
git init
ls .git/hooks/  # should contain ctags, post-checkout, post-commit, etc.
cd ~ && rm -rf /tmp/test-template-repo
```

## 7. Verify dotfiles-local repo

```bash
cd ~/dotfiles-local
git remote -v          # origin → git@github.com:IvanAnishchuk/dotfiles-local.git
git log --oneline      # should show 1454a1d "Initial import..."
git status             # clean
cat ssh/config         # should show only 'a' and 'yoga' hosts
cat config/git/config.local  # identity
```

## 8. Verify legacy backup is intact

```bash
# The old bitbucket dotfiles-local
ls ~/dotfiles-local-bitbucket/.git  # should exist
git -C ~/dotfiles-local-bitbucket log --oneline | head -3

# The pre-rcup backup
ls ~/dotfiles-pre-rcup-backup/home/
ls ~/dotfiles-pre-rcup-backup/config-git/
ls ~/dotfiles-pre-rcup-backup/ssh/

# The MEGA masterkey moved to tmp
ls ~/tmp/MEGA-MASTERKEY.txt  # should exist
```

## 9. Verify archive directory

```bash
ls ~/dotfiles/archive/
# Should contain: host-he11/ host-yoga/ repo/ themes/ README.md

# Verify rcm does NOT process archive/
env RCRC=$HOME/dotfiles/rcrc lsrc 2>&1 | grep archive
# Should produce NO output (archive is in EXCLUDES)
```

---

## 10. nsctl — automated tests

```bash
cd ~/dotfiles/nsctl
uv run pytest -v                      # 32 tests should pass
uv run pytest --cov --cov-report=term # coverage should be ~70%+
uv run ruff check src/ tests/         # 0 errors
```

## 11. nsctl — manual integration test

**IMPORTANT: this creates real directories under ~/. The cleanup
step at the end removes them. Do NOT skip the cleanup.**

### 11a. Create a test namespace

```bash
cd ~/dotfiles/nsctl
uv run nsctl new test-demo --prompt-color blue
```

Expected output: `Created namespace: test-demo` with the repo path.

Verify the created structure:

```bash
# Namespace repo
ls ~/dotfiles-id-test-demo/
# Should contain: .git/ .gitignore .gpg-id bashrc.d/ devices/ keys/
#                 namespace.toml ssh/ sync/

cat ~/dotfiles-id-test-demo/namespace.toml
# name = "test-demo", prompt.color = "blue"

cat ~/dotfiles-id-test-demo/.gpg-id
# 40-character GPG fingerprint

cat ~/dotfiles-id-test-demo/bashrc.d/50-id-test-demo.sh
# Should have DOTFILES_ID, GNUPGHOME, PASSWORD_STORE_DIR exports

cat ~/dotfiles-id-test-demo/keys/ssh/id_ed25519.toml
# Key metadata with fingerprint, creation date, history

ls ~/dotfiles-id-test-demo/devices/
# Should have g94.gpg-pub and g94.deploy-key.pub

# GPG keyring
ls ~/.gnupg-test-demo/
# Should exist, contain pubring.kbx etc.
gpg --homedir ~/.gnupg-test-demo --list-keys
# Should show nsctl-test-demo key

# SSH keys
ls -la ~/.ssh-test-demo/
# id_ed25519 (mode 600) and id_ed25519.pub
cat ~/.ssh-test-demo/id_ed25519.pub
# ssh-ed25519 AAAA... test-demo@g94

# Git log of the namespace repo
git -C ~/dotfiles-id-test-demo log --oneline
# Should show "Initial namespace: test-demo"
```

### 11b. List namespaces

```bash
uv run nsctl list
# Should show a table with test-demo, status active, GPG fingerprint
```

### 11c. Switch

```bash
uv run nsctl switch test-demo
# Should print export lines to stdout (NOT executed — just printed)
# Verify it contains:
#   export DOTFILES_ID="test-demo"
#   export GNUPGHOME="~/.gnupg-test-demo"
#   export PASSWORD_STORE_DIR="~/dotfiles-id-test-demo"
#   export NSCTL_PROMPT_COLOR="blue"
```

### 11d. Sync

```bash
uv run nsctl sync test-demo
# Should print "Synced: test-demo (no remote configured; skipped pull)"
# or similar

# Verify sync log was written
ls ~/dotfiles-id-test-demo/sync/
# Should have a .toml file with timestamp
```

### 11e. Doctor

```bash
uv run nsctl doctor
# Should show test-demo with all checks passing (green checkmarks)
```

### 11f. Disable / Enable

```bash
uv run nsctl disable test-demo
uv run nsctl list          # should show test-demo as "disabled"
uv run nsctl doctor        # should show "No enabled namespaces to check"
uv run nsctl enable test-demo
uv run nsctl list          # should show test-demo as "active" again
```

### 11g. Create a second namespace

```bash
uv run nsctl new test-work --prompt-color red
uv run nsctl list          # should show both test-demo and test-work
uv run nsctl switch test-work
# Verify it prints different GNUPGHOME and PASSWORD_STORE_DIR than test-demo
uv run nsctl doctor        # should show both passing
```

### 11h. Cleanup — IMPORTANT

```bash
uv run nsctl remove test-demo --force
uv run nsctl remove test-work --force

# Verify everything is gone
ls ~/dotfiles-id-test-demo 2>&1   # "No such file or directory"
ls ~/.gnupg-test-demo 2>&1        # "No such file or directory"
ls ~/.ssh-test-demo 2>&1          # "No such file or directory"
ls ~/dotfiles-id-test-work 2>&1   # "No such file or directory"
ls ~/.gnupg-test-work 2>&1        # "No such file or directory"
ls ~/.ssh-test-work 2>&1          # "No such file or directory"

uv run nsctl list   # "No namespaces found."
```

---

## 12. Verify nothing was damaged

After running everything above, confirm the system is unchanged:

```bash
# dotfiles repo is clean
cd ~/dotfiles && git status

# dotfiles-local repo is clean
cd ~/dotfiles-local && git status

# Real GPG keyring untouched
gpg --list-secret-keys   # should show the same keys as before

# Real SSH keys untouched
ls ~/.ssh/id_ed25519     # should exist, unchanged
ssh-add -L               # should show the same keys as before

# Real password store untouched
pass ls | head -5        # should show existing entries
```

---

## Quick reference: what's where

| What | Location |
|---|---|
| Public dotfiles | `~/dotfiles` → github.com/IvanAnishchuk/dotfiles |
| Private dotfiles-local | `~/dotfiles-local` → github.com/IvanAnishchuk/dotfiles-local |
| Legacy bitbucket clone | `~/dotfiles-local-bitbucket/` (local only) |
| Pre-rcup backup | `~/dotfiles-pre-rcup-backup/` |
| MEGA masterkey (temp) | `~/tmp/MEGA-MASTERKEY.txt` |
| nsctl source | `~/dotfiles/nsctl/` |
| nsctl plan doc | `~/dotfiles/docs/nsctl-project-plan.md` |
| Modernization plan | `~/.claude/plans/nested-sauteeing-fox.md` |
