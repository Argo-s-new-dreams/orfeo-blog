"""identita.py - legge nome, slug, repo e versione dell'app, per gli strumenti di rilascio.

Funziona con le app create dal modello (app/progetto.py) e con Argo (VERSIONE in app/trascrittore.py).
"""
import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
APP = RADICE / "app"
RE_VERSIONE = re.compile(r'^VERSIONE\s*=\s*"(\d{8}\.\d{4})"', re.M)


def file_versione():
    for nome in ("progetto.py", "trascrittore.py"):
        if (APP / nome).exists() and RE_VERSIONE.search((APP / nome).read_text(encoding="utf-8")):
            return APP / nome
    raise SystemExit("ERRORE: VERSIONE non trovata in app/progetto.py né in app/trascrittore.py")


def versione():
    return RE_VERSIONE.search(file_versione().read_text(encoding="utf-8")).group(1)


def _campo(nome, predefinito):
    p = APP / "progetto.py"
    if p.exists():
        m = re.search(rf'^{nome}\s*=\s*"([^"]*)"', p.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    return predefinito


def slug():
    return _campo("SLUG", "argo-ai")


def nome():
    return _campo("NOME", "Argo · Cassetta degli attrezzi AI")


def repo():
    return f"Argo-s-new-dreams/{slug()}"


if __name__ == "__main__":
    print(nome())  # usato dalla GitHub Action per il titolo della release
