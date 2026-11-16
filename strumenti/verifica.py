"""verifica.py - controlli prima di pubblicare una nuova versione. Uso: python strumenti/verifica.py

Controlla: formato della versione, voce nel CHANGELOG, file obbligatori, identità compilata,
requisiti.lock allineato a requisiti.txt (canale Pro),
assenza di dati personali nel repository, sintassi dei file Python, a capo corretti negli installer.
Esce con codice 1 se qualcosa non va.
"""
import py_compile
import re
import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
APP = RADICE / "app"
OBBLIGATORI = ["README.md", "CHANGELOG.md", "LICENSE", "THIRD_PARTY_LICENSES.md", "CLAUDE.md", ".gitignore",
               ".gitattributes", "Installa-Mac.command", "Installa-Windows.bat", "installer/installa_windows.ps1",
               "docs/MANUALE.md", "app/progetto.py", "app/main.py", "app/requisiti.txt", "app/icon.png",
               "app/icon.ico", "app/icon.iconset/icon_512x512@2x.png", "app/criteri.py", "app/requisiti.lock",
               ".github/workflows/rilascio-pro.yml"]
VIETATI = re.compile(r"(\.hf_token|impostazioni\.json|\.env$|token|secret|\.npy$|/dati/)", re.I)

problemi = []


def controlla(cond, msg):
    if not cond:
        problemi.append(msg)


prog = (APP / "progetto.py").read_text(encoding="utf-8")
ver = re.search(r'^VERSIONE = "(\d{8}\.\d{4})"', prog, re.M)
controlla(ver, "VERSIONE assente o non nel formato AAAAMMGG.HHMM")
if ver:
    log = (RADICE / "CHANGELOG.md").read_text(encoding="utf-8")
    controlla(f"## {ver.group(1)}" in log, f"manca la voce '## {ver.group(1)}: …' nel CHANGELOG")
for f in OBBLIGATORI:
    controlla((RADICE / f).exists(), f"file mancante: {f}")
slug = re.search(r'^SLUG = "([^"]*)"', prog, re.M).group(1)
controlla(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug), f"SLUG non valido: {slug}")
controlla(slug != "nuova-app-ai" or "--modello" in sys.argv, "progetto.py ha ancora l'identità del modello")
def _pacchetto(riga):
    return re.split(r"[<>=!~;\[ ]", riga.strip(), maxsplit=1)[0].lower().replace("_", "-")


if (APP / "requisiti.lock").exists():
    bloccati = {_pacchetto(r) for r in (APP / "requisiti.lock").read_text(encoding="utf-8").splitlines()
                if r and not r[0].isspace() and not r.startswith("#")}
    richiesti = {_pacchetto(r) for r in (APP / "requisiti.txt").read_text(encoding="utf-8").splitlines()
                 if r.strip() and not r.startswith("#")}
    mancanti = sorted(richiesti - bloccati)
    controlla(not mancanti, f"requisiti.lock non aggiornato (mancano {', '.join(mancanti)}): "
                            "python strumenti/blocca_librerie.py")
for py in APP.rglob("*.py"):
    try:
        py_compile.compile(str(py), doraise=True)
    except py_compile.PyCompileError as e:
        problemi.append(f"errore di sintassi: {e}")
try:
    tracciati = subprocess.run(["git", "ls-files"], cwd=RADICE, capture_output=True, text=True).stdout.split()
except OSError:
    tracciati = []
for f in tracciati:
    controlla(not VIETATI.search(f) or f.startswith("strumenti/"), f"possibile dato personale nel repository: {f}")
for f, eol in (("Installa-Windows.bat", b"\r\n"), ("installer/installa_windows.ps1", b"\r\n")):
    p = RADICE / f
    if p.exists() and tracciati:  # i CRLF li mette git (.gitattributes) al checkout su Windows: qui basta la regola
        controlla("eol=crlf" in (RADICE / ".gitattributes").read_text(), f".gitattributes: manca eol=crlf per {f}")

if problemi:
    print("❌ Da sistemare prima di pubblicare:")
    print("\n".join(f"  - {p}" for p in problemi))
    sys.exit(1)
print(f"✅ Tutto a posto: {slug} versione {ver.group(1)} pronta da pubblicare.")
