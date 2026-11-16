"""aggiornamenti.py - controlla su GitHub se c'è una versione nuova dell'app e la installa.

Cosa viene contattato: solo GitHub, per leggere il numero di versione e le novità (file pubblici del
repository) e, se l'utente accetta, per scaricare il pacchetto. Nessun dato dell'utente viene inviato.
I dati dell'utente stanno in progetto.DATI, fuori dalla cartella del programma, e non vengono toccati.
Tutto il comportamento dipende da progetto.py: questo file è identico in tutte le app e non va modificato.

Due canali:
- Lab: segue il ramo main. Ogni modifica pubblicata arriva subito; nessuna verifica del pacchetto.
- Pro: solo le versioni rilasciate (GitHub Releases, tag vAAAAMMGG.HHMM). Il pacchetto viene accettato
  solo se il suo SHA-256 corrisponde al manifesto e, quando l'app contiene la chiave pubblica
  (chiave_aggiornamenti.pub), se il manifesto è firmato con la chiave Ed25519 dell'app.
  Le librerie vengono installate dalla lista bloccata con hash (requisiti.lock).
"""
import base64
import hashlib
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
URL_API_RELEASE = f"https://api.github.com/repos/{REPO}/releases/latest"
RE_VERSIONE = re.compile(r'^VERSIONE\s*=\s*"(\d{8}\.\d{4})"', re.M)
REQUISITI = "requisiti.txt"
LOCK = "requisiti.lock"
MANIFESTO = "argo-manifest.json"
FIRMA = "argo-manifest.json.sig"
CHIAVE_PUBBLICA = Path(__file__).resolve().with_name("chiave_aggiornamenti.pub")

CANALI = {
    "pro": "Pro · solo versioni rilasciate e verificate",
    "lab": "Lab · ogni novità appena pubblicata",
}
CANALE_PREDEFINITO = getattr(P, "CANALE_PREDEFINITO", "lab")


class PacchettoNonValido(RuntimeError):
    """Il pacchetto o il manifesto non superano i controlli: non si installa nulla."""


def _contesti_ssl():
    """Prima i certificati di sistema (rispettano anche SSL_CERT_FILE e i proxy aziendali),
    poi quelli di certifi (il Python installato da uv su macOS non sempre trova quelli di sistema)."""
    yield ssl.create_default_context()
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass


def _scarica(url, timeout=15, accetta=None):
    intestazioni = {"User-Agent": f"{P.SLUG}-aggiornamenti", "Cache-Control": "no-cache"}
    if accetta:
        intestazioni["Accept"] = accetta
    req = urllib.request.Request(url, headers=intestazioni)
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


def canale_effettivo(impostazioni, criteri_it=None):
    """Il canale in uso: prima il criterio aziendale, poi la scelta dell'utente, poi il predefinito."""
    criteri_it = criteri_it or {}
    c = criteri_it.get("canale_aggiornamenti") or impostazioni.get("canale_aggiornamenti") or CANALE_PREDEFINITO
    return c if c in CANALI else CANALE_PREDEFINITO


def ultima_release():
    """L'ultima release pubblicata (niente bozze né pre-release), come dict dell'API GitHub."""
    dati = _scarica(URL_API_RELEASE, accetta="application/vnd.github+json")
    rel = json.loads(dati.decode("utf-8"))
    tag = str(rel.get("tag_name", ""))
    m = re.fullmatch(r"v?(\d{8}\.\d{4})", tag)
    if not m:
        raise RuntimeError(f"release senza un numero di versione valido ({tag or 'nessun tag'})")
    rel["_versione"] = m.group(1)
    return rel


def controlla(versione_locale, canale=CANALE_PREDEFINITO):
    """(c'è_aggiornamento, versione_remota, novità)."""
    if canale == "pro":
        rel = ultima_release()
        remota = rel["_versione"]
        nuova = numero(remota) > numero(versione_locale)
        return nuova, remota, (rel.get("body") or "").strip() if nuova else ""
    remota, changelog = versione_remota()
    nuova = numero(remota) > numero(versione_locale)
    return nuova, remota, novita(changelog, versione_locale) if nuova else ""


# ---------------------------------------------------------------- verifiche (canale Pro)
def chiave_pubblica():
    """La chiave pubblica Ed25519 (base64) inclusa nell'app, oppure None se non è ancora configurata."""
    try:
        testo = CHIAVE_PUBBLICA.read_text(encoding="utf-8")
    except OSError:
        return None
    righe = [r.strip() for r in testo.splitlines() if r.strip() and not r.lstrip().startswith("#")]
    return righe[0] if righe else None


def verifica_firma(dati, firma_b64, chiave_b64):
    """True se firma_b64 è una firma Ed25519 valida di dati per la chiave chiave_b64."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        chiave = Ed25519PublicKey.from_public_bytes(base64.b64decode(chiave_b64))
        chiave.verify(base64.b64decode(firma_b64.strip()), dati)
        return True
    except (InvalidSignature, ValueError):
        return False


def verifica_manifesto(manifesto_bytes, firma_b64, chiave_b64, versione_attesa):
    """Controlla firma (se c'è la chiave) e contenuto del manifesto. Ritorna (manifesto, tipo_di_verifica)."""
    if chiave_b64:
        if not firma_b64:
            raise PacchettoNonValido("la release non è firmata, ma questa installazione richiede la firma")
        if not verifica_firma(manifesto_bytes, firma_b64, chiave_b64):
            raise PacchettoNonValido("la firma del manifesto non è valida")
        tipo = "firma Ed25519 e SHA-256"
    else:
        tipo = "SHA-256 (firma non ancora configurata)"
    try:
        man = json.loads(manifesto_bytes.decode("utf-8"))
    except ValueError:
        raise PacchettoNonValido("manifesto illeggibile")
    for campo in ("versione", "pacchetto", "sha256"):
        if not man.get(campo):
            raise PacchettoNonValido(f"nel manifesto manca «{campo}»")
    if man["versione"] != versione_attesa:
        raise PacchettoNonValido(f"il manifesto è della versione {man['versione']}, la release è la {versione_attesa}")
    return man, tipo


def verifica_pacchetto(dati, sha256_atteso):
    calcolato = hashlib.sha256(dati).hexdigest()
    if calcolato.lower() != str(sha256_atteso).lower():
        raise PacchettoNonValido("il pacchetto scaricato non corrisponde al manifesto (SHA-256 diverso)")


def _asset(rel, nome):
    return next((a for a in rel.get("assets", []) if a.get("name") == nome), None)


def _scarica_pro(stato):
    """Scarica e verifica il pacchetto dell'ultima release. Ritorna (zip_bytes, versione, tipo_di_verifica)."""
    stato("Leggo l'ultima versione rilasciata…")
    rel = ultima_release()
    a_man = _asset(rel, MANIFESTO)
    if not a_man:
        raise PacchettoNonValido("la release non contiene il manifesto: non la installo")
    manifesto = _scarica(a_man["browser_download_url"], timeout=30)
    a_firma = _asset(rel, FIRMA)
    firma = _scarica(a_firma["browser_download_url"], timeout=30).decode("ascii", "replace") if a_firma else None
    stato("Verifico il manifesto…")
    man, tipo = verifica_manifesto(manifesto, firma, chiave_pubblica(), rel["_versione"])
    a_pac = _asset(rel, man["pacchetto"])
    if not a_pac:
        raise PacchettoNonValido(f"nella release manca il pacchetto {man['pacchetto']}")
    stato(f"Scarico {P.NOME} {man['versione']}…")
    dati = _scarica(a_pac["browser_download_url"], timeout=300)
    stato("Controllo l'impronta del pacchetto…")
    verifica_pacchetto(dati, man["sha256"])
    return dati, man["versione"], tipo


def _estrai_app(dati, cartella):
    """Estrae la cartella app/ dello ZIP in cartella. Vale sia per lo ZIP del ramo (radice
    «<repo>-main/app/…») sia per il pacchetto di release (radice «app/…»)."""
    with zipfile.ZipFile(io.BytesIO(dati)) as z:
        nomi = z.namelist()
        pref = "app/" if any(n.startswith("app/") for n in nomi) else f"{nomi[0].split('/')[0]}/app/"
        voci = [n for n in nomi if n.startswith(pref) and not n.endswith("/")]
        if not any(n.endswith("/progetto.py") for n in voci):
            raise PacchettoNonValido(f"il pacchetto scaricato non contiene {P.NOME}")
        for n in voci:
            rel = n[len(pref):]
            if rel.startswith("/") or ".." in Path(rel).parts:
                raise PacchettoNonValido(f"percorso non ammesso nel pacchetto: {n}")
            dest = cartella / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(n))


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


def installa(cartella_app, stato=lambda t: None, canale=CANALE_PREDEFINITO):
    """Scarica il pacchetto da GitHub e sostituisce i file del programma in cartella_app.
    Ritorna un dict con: versione, backup, canale, verifica,
    librerie ('ok' | 'non_servono' | 'manca_uv' | 'errore: ...')."""
    cartella_app = Path(cartella_app)
    if canale == "pro":
        dati, versione_attesa, verifica = _scarica_pro(stato)
    else:
        stato("Scarico la nuova versione da GitHub…")
        dati, versione_attesa, verifica = _scarica(URL_ZIP, timeout=120), None, "nessuna (canale Lab)"
    stato("Controllo il pacchetto…")
    tmp = Path(tempfile.mkdtemp(prefix=f"{P.SLUG}_agg_"))
    try:
        _estrai_app(dati, tmp)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    m = RE_VERSIONE.search((tmp / "progetto.py").read_text(encoding="utf-8"))
    versione = m.group(1) if m else "?"
    if versione_attesa and versione != versione_attesa:
        shutil.rmtree(tmp, ignore_errors=True)
        raise PacchettoNonValido(f"il pacchetto contiene la versione {versione}, non la {versione_attesa}")

    # Pro: librerie dalla lista bloccata con hash, se il pacchetto la contiene
    file_req = LOCK if canale == "pro" and (tmp / LOCK).exists() else REQUISITI
    req_vecchi = (cartella_app / file_req).read_text(encoding="utf-8") if (cartella_app / file_req).exists() else ""
    req_nuovi = (tmp / file_req).read_text(encoding="utf-8") if (tmp / file_req).exists() else ""

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
            comando = [uv, "pip", "install", "--python", sys.executable, "-r", str(cartella_app / file_req)]
            if file_req == LOCK:
                comando.insert(3, "--require-hashes")
            r = subprocess.run(comando, capture_output=True, text=True, creationflags=flags)
            librerie = "ok" if r.returncode == 0 else "errore: " + (r.stderr or r.stdout)[-400:]
    (cartella_app.parent / "ultimo_aggiornamento.json").write_text(
        json.dumps({"versione": versione, "quando": time.strftime("%Y-%m-%d %H:%M"), "librerie": librerie,
                    "canale": canale, "verifica": verifica}),
        encoding="utf-8")
    return {"versione": versione, "backup": str(backup), "librerie": librerie, "canale": canale,
            "verifica": verifica}


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
