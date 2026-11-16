"""genera_chiavi.py - crea la coppia di chiavi Ed25519 che firma le release Pro dell'app. UNA volta per app.

Sul Mac, dalla cartella del repository:

    uv run --with cryptography strumenti/genera_chiavi.py

Scrive:
    app/chiave_aggiornamenti.pub        chiave PUBBLICA: va nel repository (le app la usano per verificare)
    ~/<slug>-firma-privata.txt          chiave PRIVATA: NON va nel repository

Poi:
    gh secret set ARGO_FIRMA_PRIVATA --repo Argo-s-new-dreams/<slug> < ~/<slug>-firma-privata.txt
    conserva una copia della chiave privata nel portachiavi o nel password manager, e cancella il file.

Attenzione: dal momento in cui un'app con chiave_aggiornamenti.pub è installata, accetterà solo release
firmate con questa chiave. Se perdi la chiave privata, le installazioni Pro andranno aggiornate a mano.
"""
import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identita  # noqa: E402
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

RADICE = Path(__file__).resolve().parent.parent
PUBBLICA = RADICE / "app" / "chiave_aggiornamenti.pub"
PRIVATA = Path.home() / f"{identita.slug()}-firma-privata.txt"


def main():
    if PUBBLICA.exists() or PRIVATA.exists():
        sys.exit(f"Esiste già {PUBBLICA if PUBBLICA.exists() else PRIVATA}: non la sovrascrivo.")
    chiave = Ed25519PrivateKey.generate()
    priv = chiave.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                serialization.NoEncryption())
    pub = chiave.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    PRIVATA.write_text(base64.b64encode(priv).decode("ascii") + "\n", encoding="ascii")
    os.chmod(PRIVATA, 0o600)
    PUBBLICA.write_text(f"# Chiave pubblica Ed25519 per verificare le release Pro di {identita.nome()}\n"
                        + base64.b64encode(pub).decode("ascii") + "\n", encoding="ascii")
    print(f"Chiave pubblica: {PUBBLICA}  (da fare commit)")
    print(f"Chiave privata:  {PRIVATA}  (NON fare commit)")
    print(f"Ora: gh secret set ARGO_FIRMA_PRIVATA --repo {identita.repo()} < {PRIVATA}")


if __name__ == "__main__":
    main()
