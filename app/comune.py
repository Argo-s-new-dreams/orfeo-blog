"""comune.py - servizi di Orfeo condivisi da motore e pagine: cartelle, rete, password, storico, notifiche.

Impostazioni e dati stanno in progetto.DATI (standard famiglia Argo): gli aggiornamenti non li toccano.
"""
import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import dati
import progetto as P

STORICO_FILE = P.DATI / "storico.json"
LOG_DIR = P.DATI / "log"
SERVIZIO_PASSWORD = "Orfeo-WordPress"
USER_AGENT = f"Orfeo/{P.VERSIONE} (+https://github.com/{P.REPO})"


def cartelle(imp=None):
    """Cartella di lavoro scelta dall'utente (di serie ~/Documents/Orfeo) con le quattro sottocartelle."""
    base = Path((imp or dati.carica_impostazioni())["cartella"]).expanduser()
    d = {k: base / k for k in ("in-arrivo", "bozze", "elaborati", "config")}
    for p in d.values():
        p.mkdir(parents=True, exist_ok=True)
    d["base"] = base
    return d


# ---------------------------------------------------------------- rete (solo se attivata nelle impostazioni)
def _contesti_ssl():
    """Prima i certificati di sistema, poi certifi (il Python di uv su macOS non sempre trova quelli di sistema)."""
    yield ssl.create_default_context()
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass


def http(url, dati_post=None, intestazioni=None, metodo=None, timeout=25):
    """Ritorna (codice, bytes, content_type). Solleva URLError/HTTPError come urllib."""
    h = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    h.update(intestazioni or {})
    req = urllib.request.Request(url, data=dati_post, headers=h, method=metodo)
    ultimo = None
    for ctx in _contesti_ssl():
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.status, r.read(), r.headers.get("Content-Type", "")
        except urllib.error.URLError as e:
            if not isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
                raise
            ultimo = e
    raise ultimo


# ---------------------------------------------------------------- password WordPress
# keyring usa il Portachiavi su macOS e il Gestore credenziali su Windows: la password non finisce mai su file.
def leggi_password(utente):
    if not utente:
        return ""
    try:
        import keyring
        return keyring.get_password(SERVIZIO_PASSWORD, utente) or ""
    except Exception:
        return ""


def salva_password(utente, password):
    import keyring
    keyring.set_password(SERVIZIO_PASSWORD, utente, password)


# ---------------------------------------------------------------- varie
def slugify(testo, max_len=70):
    t = testo.lower()
    for a, b in (("àáâä", "a"), ("èéêë", "e"), ("ìíîï", "i"), ("òóôö", "o"), ("ùúûü", "u"), ("ç", "c"), ("ñ", "n")):
        t = re.sub(f"[{a}]", b, t)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:max_len].rstrip("-") or "bozza"


def notifica(titolo, messaggio):
    """Notifica di sistema: Centro notifiche su macOS; su Windows l'esito resta nello Storico."""
    if sys.platform != "darwin":
        return
    esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')  # noqa: E731
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{esc(messaggio)}" with title "{esc(titolo)}" sound name "Glass"'],
                       timeout=10, capture_output=True)
    except Exception:
        pass


def carica_storico():
    try:
        return json.loads(STORICO_FILE.read_text("utf-8"))
    except Exception:
        return []


def aggiungi_storico(voce):
    st = carica_storico()
    st.insert(0, voce)
    P.DATI.mkdir(parents=True, exist_ok=True)
    tmp = STORICO_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st[:200], ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(STORICO_FILE)
