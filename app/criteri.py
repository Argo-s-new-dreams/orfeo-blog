"""criteri.py - criteri aziendali dell'app, impostati dall'IT (per esempio via Intune o Jamf).

Un file JSON in una cartella di sistema, scrivibile solo dall'amministratore, che ha la precedenza sulle
impostazioni dell'utente. Se il file non c'è, l'app si comporta come sempre.

    macOS    /Library/Application Support/<NOME>/criteri.json
    Windows  %ProgramData%\\<NOME>\\criteri.json
    Linux    /etc/<slug>/criteri.json
    (per le prove: variabile d'ambiente <SLUG>_CRITERI con il percorso del file)

Chiavi riconosciute (tutte facoltative):
    "canale_aggiornamenti":  "pro" | "lab"   blocca il canale e lo rende non modificabile
    "aggiornamenti_dall_app": false          l'app non controlla e non installa aggiornamenti da sola
                                             (li distribuisce l'IT)
Questo file è identico in tutte le app e non va modificato.
"""
import json
import os
import sys
from pathlib import Path

import progetto as P

CHIAVI = {"canale_aggiornamenti", "aggiornamenti_dall_app"}
VARIABILE = f"{P.SLUG.upper().replace('-', '_')}_CRITERI"


def percorso():
    if os.environ.get(VARIABILE):
        return Path(os.environ[VARIABILE])
    if sys.platform == "darwin":
        return Path("/Library/Application Support") / P.NOME / "criteri.json"
    if os.name == "nt":
        return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / P.NOME / "criteri.json"
    return Path("/etc") / P.SLUG / "criteri.json"


def carica():
    """Ritorna i criteri validi (dict, eventualmente vuoto). Un file illeggibile vale come assente."""
    try:
        dati = json.loads(percorso().read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    if not isinstance(dati, dict):
        return {}
    criteri = {k: v for k, v in dati.items() if k in CHIAVI}
    if criteri.get("canale_aggiornamenti") not in (None, "lab", "pro"):
        criteri.pop("canale_aggiornamenti")
    if "aggiornamenti_dall_app" in criteri and not isinstance(criteri["aggiornamenti_dall_app"], bool):
        criteri.pop("aggiornamenti_dall_app")
    return criteri
