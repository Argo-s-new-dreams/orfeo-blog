"""blocca_librerie.py - rigenera app/requisiti.lock (versioni fisse con hash, Mac/Windows/Linux, Python 3.12).

    python strumenti/blocca_librerie.py                  rigenera usando i vincoli già salvati
    python strumenti/blocca_librerie.py freeze.txt       prima salva freeze.txt come ambiente di riferimento

Il «freeze» si ottiene dall'ambiente che funziona davvero sul Mac:
    uv pip freeze --python ~/<slug>-env/bin/python > ~/Desktop/freeze.txt
Così il canale Pro usa le stesse versioni collaudate, non quelle che PyPI offre oggi.
Va rilanciato ogni volta che cambia app/requisiti.txt. Serve uv.
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identita  # noqa: E402

RIFERIMENTO = identita.RADICE / "strumenti" / "ambiente-riferimento.txt"


def main():
    uv = shutil.which("uv")
    if not uv:
        sys.exit("ERRORE: uv non trovato (https://docs.astral.sh/uv/)")
    if len(sys.argv) > 1:
        freeze = Path(sys.argv[1]).expanduser()
        RIFERIMENTO.write_text(
            "# Ambiente di riferimento (uv pip freeze dall'ambiente collaudato).\n"
            "# Vincola requisiti.lock alle versioni provate. Aggiornalo quando l'ambiente cambia.\n"
            + freeze.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Ambiente di riferimento salvato in {RIFERIMENTO.relative_to(identita.RADICE)}")
    comando = ["uv", "pip", "compile", "app/requisiti.txt", "--universal", "--python-version", "3.12",
               "--generate-hashes", "-o", "app/requisiti.lock"]
    if RIFERIMENTO.exists():
        comando += ["-c", "strumenti/ambiente-riferimento.txt"]
    r = subprocess.run([uv, *comando[1:], "-q", "--custom-compile-command", "python strumenti/blocca_librerie.py"],
                       cwd=identita.RADICE)
    if r.returncode:
        sys.exit("ERRORE: risoluzione delle librerie non riuscita (vedi sopra)")
    print("✅ app/requisiti.lock aggiornato" + (" (vincolato all'ambiente di riferimento)." if RIFERIMENTO.exists() else "."))


if __name__ == "__main__":
    main()
