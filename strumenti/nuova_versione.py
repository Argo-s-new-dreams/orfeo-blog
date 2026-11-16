"""nuova_versione.py - aggiorna VERSIONE (AAAAMMGG.HHMM, ora di Roma) e apre la voce nel CHANGELOG.

Uso:  python strumenti/nuova_versione.py "Titolo della novità" ["- punto 1" "- punto 2" ...]
Va eseguito a OGNI modifica pubblicata: è il numero che l'app confronta con GitHub per proporre l'aggiornamento.
"""
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RADICE = Path(__file__).resolve().parent.parent
PROGETTO = RADICE / "app" / "progetto.py"
CHANGELOG = RADICE / "CHANGELOG.md"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    titolo, punti = sys.argv[1], sys.argv[2:]
    nuova = datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y%m%d.%H%M")
    testo = PROGETTO.read_text(encoding="utf-8")
    vecchia = re.search(r'^VERSIONE = "(\d{8}\.\d{4})"', testo, re.M).group(1)
    if int(nuova.replace(".", "")) <= int(vecchia.replace(".", "")):
        # due rilasci nello stesso minuto: avanza di un minuto per restare crescente
        nuova = (datetime.strptime(vecchia, "%Y%m%d.%H%M") + timedelta(minutes=1)).strftime("%Y%m%d.%H%M")
    PROGETTO.write_text(re.sub(r'^VERSIONE = ".*"', f'VERSIONE = "{nuova}"', testo, count=1, flags=re.M),
                        encoding="utf-8")
    log = CHANGELOG.read_text(encoding="utf-8")
    voce = f"## {nuova}: {titolo}\n" + "".join(f"{p if p.startswith('-') else '- ' + p}\n" for p in punti) + "\n"
    m = re.search(r"^## ", log, re.M)
    log = log[:m.start()] + voce + log[m.start():] if m else log.rstrip() + "\n\n" + voce
    CHANGELOG.write_text(log, encoding="utf-8")
    print(f"Versione {vecchia} -> {nuova}. Ricorda: commit, push su GitHub (canale Lab) e copia nella cartella "
          "SharePoint. Per i clienti: python strumenti/passa_a_pro.py (canale Pro).")


if __name__ == "__main__":
    main()
