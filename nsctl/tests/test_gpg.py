"""Tests for GPG subprocess wrapper."""

import pytest

from nsctl.gpg import (
    GpgError,
    decrypt,
    encrypt_to_recipients,
    export_public_key,
    generate_keypair,
    get_fingerprint,
    import_key,
    init_gnupghome,
    list_keys,
)


@pytest.fixture
def gpghome(tmp_path):
    d = tmp_path / "gnupg"
    init_gnupghome(d)
    return d


@pytest.mark.slow
def test_generate_and_list(gpghome):
    fpr = generate_keypair(gpghome, "Test User", "test@nsctl.local")
    assert len(fpr) == 40  # full fingerprint

    keys = list_keys(gpghome)
    assert any(k.fingerprint == fpr for k in keys)
    assert any("test@nsctl.local" in k.uid for k in keys)


@pytest.mark.slow
def test_get_fingerprint(gpghome):
    fpr = generate_keypair(gpghome, "FPR Test", "fpr@test.local")
    found = get_fingerprint(gpghome, "fpr@test.local")
    assert found == fpr


@pytest.mark.slow
def test_export_import(gpghome, tmp_path):
    fpr = generate_keypair(gpghome, "Export Test", "export@test.local")
    pub = export_public_key(gpghome, fpr)
    assert "BEGIN PGP PUBLIC KEY BLOCK" in pub

    # Import into a second keyring
    other = tmp_path / "gnupg2"
    init_gnupghome(other)
    import_key(other, pub)
    keys = list_keys(other)
    assert any(k.fingerprint == fpr for k in keys)


@pytest.mark.slow
def test_encrypt_decrypt_roundtrip(gpghome):
    fpr = generate_keypair(gpghome, "Crypto Test", "crypto@test.local")
    plaintext = b"hello secret world"

    ciphertext = encrypt_to_recipients(gpghome, [fpr], plaintext)
    assert b"BEGIN PGP MESSAGE" in ciphertext

    decrypted = decrypt(gpghome, ciphertext)
    assert decrypted == plaintext


@pytest.mark.slow
def test_encrypt_bad_recipient(gpghome):
    with pytest.raises(GpgError):
        encrypt_to_recipients(gpghome, ["nonexistent@nowhere"], b"data")
