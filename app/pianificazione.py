"""pianificazione.py - esecuzione settimanale automatica, senza diritti di amministratore.

macOS: un LaunchAgent dell'utente apre Orfeo.app in background con `open --env ORFEO_ESEGUI=1`.
       Passando dal bundle, i permessi di macOS sulla cartella Documenti sono quelli concessi a Orfeo.app.
       L'installer standard non passa argomenti all'app: per questo si usa una variabile d'ambiente.
       Se a quell'ora il Mac dorme, launchd esegue al risveglio; se è spento, quella settimana salta.
Windows: un'attività dell'Utilità di pianificazione lancia pythonw.exe main.py --esegui.
"""
import plistlib
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import progetto as P

ETICHETTA = P.BUNDLE_ID
VARIABILE = "ORFEO_ESEGUI"
GIORNI = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"]  # 0 = domenica (launchd)
SIGLE_WIN = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{ETICHETTA}.plist"
BUNDLE = Path.home() / "Applications" / f"{P.NOME}.app"
TASK_WIN = f"{P.NOME} - bozza settimanale"


def _esegui(cmd):
    return subprocess.run(cmd, capture_output=True, text=True,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0)


def supportata():
    return sys.platform in ("darwin", "win32")


def stato():
    """{'installata': bool, 'caricata': bool}"""
    if sys.platform == "darwin":
        return {"installata": PLIST.exists(), "caricata": _esegui(["launchctl", "list", ETICHETTA]).returncode == 0}
    if sys.platform == "win32":
        ok = _esegui(["schtasks", "/Query", "/TN", TASK_WIN]).returncode == 0
        return {"installata": ok, "caricata": ok}
    return {"installata": False, "caricata": False}


def comando_manuale():
    """Il comando che la pianificazione esegue (usato anche da «Prova adesso in background»)."""
    if sys.platform == "darwin":
        return ["/usr/bin/open", "-n", "-g", "-j", "--env", f"{VARIABILE}=1", "-a", str(BUNDLE)]
    return [str(P.CASA / "Scripts" / "pythonw.exe"), str(Path(__file__).with_name("main.py")), "--esegui"]


def attiva(giorno, ora, minuto, log_dir):
    disattiva()
    if sys.platform == "darwin":
        if not BUNDLE.exists():
            raise RuntimeError(f"Non trovo {BUNDLE}: reinstalla {P.NOME} con Installa-Mac.command.")
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        dati = {"Label": ETICHETTA, "ProgramArguments": comando_manuale(),
                "StartCalendarInterval": {"Weekday": int(giorno), "Hour": int(ora), "Minute": int(minuto)},
                "StandardOutPath": str(Path(log_dir) / "launchd.log"),
                "StandardErrorPath": str(Path(log_dir) / "launchd.log"), "RunAtLoad": False}
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        with open(PLIST, "wb") as f:
            plistlib.dump(dati, f)
        uid = _esegui(["id", "-u"]).stdout.strip()
        if _esegui(["launchctl", "bootstrap", f"gui/{uid}", str(PLIST)]).returncode != 0:
            r = _esegui(["launchctl", "load", "-w", str(PLIST)])  # sintassi storica, come riserva
            if r.returncode != 0:
                raise RuntimeError(f"macOS non ha accettato la pianificazione: {r.stderr.strip()}")
    elif sys.platform == "win32":
        exe, main, arg = comando_manuale()
        tr = f'"{exe}" "{main}" {arg}'
        r = _esegui(["schtasks", "/Create", "/F", "/SC", "WEEKLY", "/D", SIGLE_WIN[int(giorno)],
                     "/ST", f"{int(ora):02d}:{int(minuto):02d}", "/TN", TASK_WIN, "/TR", tr])
        if r.returncode != 0:
            raise RuntimeError(f"Windows non ha accettato la pianificazione: {(r.stderr or r.stdout).strip()}")
    else:
        raise RuntimeError("La pianificazione è disponibile su macOS e Windows.")


def disattiva():
    if sys.platform == "darwin" and PLIST.exists():
        uid = _esegui(["id", "-u"]).stdout.strip()
        if _esegui(["launchctl", "bootout", f"gui/{uid}/{ETICHETTA}"]).returncode != 0:
            _esegui(["launchctl", "unload", "-w", str(PLIST)])
        PLIST.unlink(missing_ok=True)
    elif sys.platform == "win32":
        _esegui(["schtasks", "/Delete", "/F", "/TN", TASK_WIN])


def prossima(giorno, ora, minuto, adesso=None):
    """Prossima data di esecuzione (giorno: 0 = domenica)."""
    adesso = adesso or datetime.now()
    py_giorno = (int(giorno) - 1) % 7  # in Python 0 = lunedì
    c = adesso.replace(hour=int(ora), minute=int(minuto), second=0, microsecond=0)
    c += timedelta(days=(py_giorno - adesso.weekday()) % 7)
    if c <= adesso:
        c += timedelta(days=7)
    return c


def descrivi(giorno, ora, minuto):
    q = prossima(giorno, ora, minuto)
    return f"{GIORNI[(q.weekday() + 1) % 7]} {q:%d/%m} alle {q:%H:%M}"
