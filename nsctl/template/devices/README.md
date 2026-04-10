# devices/

Per-device GPG public keys and deploy key public halves.
Each device that has access to this namespace has:

- `<label>.gpg-pub` — armored GPG public key (encryption subkey)
- `<label>.deploy-key.pub` — SSH deploy key public half
