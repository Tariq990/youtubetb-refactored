# 🔐 Encrypted Secrets System

This folder contains **encrypted** versions of sensitive files (API keys, tokens, cookies).

## 🎯 Quick Info

- **Safe for GitHub**: These files are password-encrypted and safe to commit
- **Decryption needed**: Use `scripts/decrypt_secrets.py` to restore the original files
- **Password required**: You need the encryption password to decrypt

## 📋 Files

| Encrypted File | Original File | Description |
|----------------|---------------|-------------|
| `api_key.txt.enc` | `secrets/api_key.txt` | Gemini API key |
| `client_secret.json.enc` | `secrets/client_secret.json` | YouTube OAuth client |
| `cookies.txt.enc` | `secrets/cookies.txt` | YouTube + Amazon cookies (merged) |
| `token.json.enc` | `secrets/token.json` | YouTube access token |

## 🚀 Usage

### On Google Colab (or new machine)

```python
# 1. Install cryptography
!pip install cryptography

# 2. Decrypt the secrets
!python scripts/decrypt_secrets.py
# Enter password when prompted

# 3. Run your project
!python main.py
```

### Re-encrypting (on local machine)

```bash
# Update files in secrets/ first, then:
python scripts/encrypt_secrets.py
git add secrets_encrypted/
git commit -m "Update encrypted secrets"
git push
```

## 📖 Full Documentation

See **[SECRETS_ENCRYPTION.md](../SECRETS_ENCRYPTION.md)** for complete guide (Arabic + English).

## 🔒 Security

- Encryption: **Fernet (AES-128)** via password-based key derivation
- KDF: **PBKDF2-SHA256** with 100,000 iterations
- Salt: Unique 16-byte salt per file (stored in first 16 bytes of .enc file)

---

**IMPORTANT**: Never commit the original `secrets/` folder! Keep your password safe!
