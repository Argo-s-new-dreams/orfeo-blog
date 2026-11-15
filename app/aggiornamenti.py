"""aggiornamenti.py - controlla su GitHub se c'è una versione nuova dell'app e la installa.

Cosa viene contattato: solo GitHub, per leggere il numero di versione e le novità (file pubblici del
repository) e, se l'utente accetta, per scaricare il pacchetto. Nessun dato dell'utente viene inviato.
I dati dell'utente stanno in progetto.DATI, fuori dalla cartella del programma, e non vengono toccati.
Tutto il comportamento dipende da progetto.py: questo file è identico in tutte le app e non va modificato.
"""
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import progetto as P

REPO = P.REPO
RAMO = P.RAMO
URL_GITHUB = f"https://github.com/{REPO}"
URL_RAW = f"https://raw.githubusercontent.com/{REPO}/{RAMO}"
URL_ZIP = f"https://github.com/{REPO}/archive/refs/heads/{RAMO}.zip"
RE_VERSIONE = re.compile(r'^VERSIONE\s*=\s*"(\d{8}\.\d{4})"', re.M)
REQUISITI = "requisiti.txt"


def _contesti_ssl():
    """Prima i certificati di sistema (rispettano anche SSL_CERT_FILE e i proxy aziendali),
    poi quelli di certifi (il Python installato da uv su macOS non sempre trova quelli di sistema)."""
    yield ssl.create_default_context()
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass


def _scarica(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": f"{P.SLUG}-aggiornamenti", "Cache-Control": "no-cache"})
    ultimo = None
    for ctx in _contesti_ssl():
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read()
        except urllib.error.URLError as e:
            if not isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
                raise
            ultimo = e
    raise ultimo


def numero(v):
    """'20261114.1845' -> 202611141845 (per confrontare le versioni)."""
    try:
        return int(str(v).replace(".", ""))
    except ValueError:
        return 0


def versione_remota():
    """Ritorna (versione, testo del CHANGELOG) dall'ultima versione pubblicata su GitHub."""
    codice = _scarica(f"{URL_RAW}/app/progetto.py?t={int(time.time())}").decode("utf-8", "replace")
    m = RE_VERSIONE.search(codice)
    if not m:
        raise RuntimeError("numero di versione non trovato su GitHub")
    try:
        changelog = _scarica(f"{URL_RAW}/CHANGELOG.md?t={int(time.time())}").decode("utf-8", "replace")
    except Exception:
        changelog = ""
    return m.group(1), changelog


def novita(changelog, versione_locale):
    """Le sezioni del CHANGELOG più recenti della versione installata."""
    sezioni, attuale = [], None
    for riga in changelog.splitlines():
        m = re.match(r"^##\s+(\d{8}\.\d{4})", riga)
        if m:
            attuale = m.group(1) if numero(m.group(1)) > numero(versione_locale) else None
            if attuale:
                sezioni.append([riga])
            continue
        if attuale and sezioni:
            sezioni[-1].append(riga)
    return "\n".join("\n".join(s).strip() for s in sezioni).strip()


def controlla(versione_locale):
    """(c'è_aggiornamento, versione_remota, novità)."""
    remota, changelog = versione_remota()
    nuova = numero(remota) > numero(versione_locale)
    return nuova, remota, novita(changelog, versione_locale) if nuova else ""


def trova_uv():
    """Cerca uv (serve solo se la nuova versione chiede librerie nuove)."""
    trovato = shutil.which("uv")
    if trovato:
        return trovato
    casa = Path.home()
    candidati = [casa / ".local/bin/uv", Path("/opt/homebrew/bin/uv"), Path("/usr/local/bin/uv"),
                 casa / ".local/bin/uv.exe", casa / ".cargo/bin/uv",
                 Path(os.environ.get("LOCALAPPDATA", casa)) / "Microsoft/WinGet/Links/uv.exe"]
    return next((str(c) for c in candidati if c.exists()), None)


def installa(cartella_app, stato=lambda t: None):
    """Scarica il pacchetto da GitHub e sostituisce i file del programma in cartella_app.
    Ritorna un dict con: versione, backup, librerie ('ok' | 'non_servono' | 'manca_uv' | 'errore: ...')."""
    cartella_app = Path(cartella_app)
    stato("Scarico la nuova versione da GitHub…")
    dati = _scarica(URL_ZIP, timeout=120)
    stato("Controllo il pacchetto…")
    with zipfile.ZipFile(io.BytesIO(dati)) as z:
        radice = z.namelist()[0].split("/")[0]
        pref = f"{radice}/app/"
        voci = [n for n in z.namelist() if n.startswith(pref) and not n.endswith("/")]
        if not any(n.endswith("/progetto.py") for n in voci):
            raise RuntimeError(f"il pacchetto scaricato non contiene {P.NOME}")
        tmp = Path(tempfile.mkdtemp(prefix=f"{P.SLUG}_agg_"))
        for n in voci:
            dest = tmp / n[len(pref):]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(n))
    m = RE_VERSIONE.search((tmp / "progetto.py").read_text(encoding="utf-8"))
    versione = m.group(1) if m else "?"

    req_vecchi = (cartella_app / REQUISITI).read_text(encoding="utf-8") if (cartella_app / REQUISITI).exists() else ""
    req_nuovi = (tmp / REQUISITI).read_text(encoding="utf-8") if (tmp / REQUISITI).exists() else ""

    stato("Salvo una copia della versione attuale…")
    backup = cartella_app.parent / "app_precedente"
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    shutil.copytree(cartella_app, backup, ignore=shutil.ignore_patterns("__pycache__"))

    stato("Installo i nuovi file…")
    for f in tmp.rglob("*"):
        if f.is_file():
            dest = cartella_app / f.relative_to(tmp)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
    shutil.rmtree(tmp, ignore_errors=True)

    librerie = "non_servono"
    if req_nuovi.strip() and req_nuovi.strip() != req_vecchi.strip():
        uv = trova_uv()
        if not uv:
            librerie = "manca_uv"
        else:
            stato("Aggiorno le librerie (può richiedere qualche minuto)…")
            flags = 0x08000000 if os.name == "nt" else 0
            r = subprocess.run([uv, "pip", "install", "--python", sys.executable, "-r", str(cartella_app / REQUISITI)],
                               capture_output=True, text=True, creationflags=flags)
            librerie = "ok" if r.returncode == 0 else "errore: " + (r.stderr or r.stdout)[-400:]
    (cartella_app.parent / "ultimo_aggiornamento.json").write_text(
        json.dumps({"versione": versione, "quando": time.strftime("%Y-%m-%d %H:%M"), "librerie": librerie}),
        encoding="utf-8")
    return {"versione": versione, "backup": str(backup), "librerie": librerie}


def riavvia():
    """Riapre l'app dopo l'aggiornamento.
    Sul Mac passa dal bundle in ~/Applications (open -n, subito, prima di chiudere la vecchia finestra);
    altrove rilancia lo stesso Python con lo stesso script. Uscite scollegate: il processo nuovo non dipende
    da quello vecchio."""
    script = Path(sys.argv[0]).resolve()
    nulla = subprocess.DEVNULL
    if sys.platform == "darwin":
        # Sul Mac, quando un'app si chiude, macOS termina anche i processi figli rimasti (anche se staccati):
        # un «sleep 2; open» lanciato da qui moriva prima di riaprire l'app. Quindi chiediamo SUBITO a
        # LaunchServices di avviare una nuova istanza: la lancia launchd, non noi, e sopravvive alla chiusura.
        bundle = Path.home() / "Applications" / f"{P.NOME}.app"
        if bundle.exists():
            try:
                r = subprocess.run(["/usr/bin/open", "-n", str(bundle)], stdin=nulla, stdout=nulla,
                                   stderr=subprocess.PIPE, timeout=15)
                if r.returncode == 0:
                    return
            except (OSError, subprocess.SubprocessError):
                pass
        subprocess.Popen([sys.executable, str(script)], stdin=nulla, stdout=nulla, stderr=nulla,
                         close_fds=True, start_new_session=True)
        return
    if os.name == "nt":
        pyw = Path(sys.executable).with_name("pythonw.exe")
        exe = str(pyw) if pyw.exists() else sys.executable
        subprocess.Popen([exe, str(script)], stdin=nulla, stdout=nulla, stderr=nulla, close_fds=True,
                         creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | NEW_PROCESS_GROUP
        return
    subprocess.Popen(["/bin/sh", "-c", f'sleep 2; "{sys.executable}" "{script}"'], stdin=nulla, stdout=nulla,
                     stderr=nulla, close_fds=True, start_new_session=True)
