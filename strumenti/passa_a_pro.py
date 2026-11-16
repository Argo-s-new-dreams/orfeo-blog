"""passa_a_pro.py - promuove la versione attuale di main al canale Pro (tag vAAAAMMGG.HHMM + push).

    python strumenti/passa_a_pro.py --controlla   solo i controlli e il riepilogo, non tocca niente
    python strumenti/passa_a_pro.py               controlli, riepilogo, poi chiede conferma [s/N]
    python strumenti/passa_a_pro.py --si          conferma già data (da usare SOLO dopo il sì esplicito di Luca)

Il push del tag avvia la GitHub Action «Rilascio Pro», che prova, firma e pubblica la release.
Un tag pubblicato non si ritira con leggerezza: chi è sul canale Pro installerà quella versione.

Controlli: ramo main pulito e allineato a GitHub, voce nel CHANGELOG, requisiti.lock presente e
coerente con requisiti.txt, chiave pubblica presente, tag non ancora usato, versione più alta dell'ultima Pro.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identita  # noqa: E402

RADICE = identita.RADICE


def git(*args, controlla=True):
    r = subprocess.run(["git", *args], cwd=RADICE, capture_output=True, text=True)
    if controlla and r.returncode:
        raise SystemExit(f"ERRORE: git {' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def nome_pacchetto(riga):
    return re.split(r"[<>=!~;\[ ]", riga.strip(), maxsplit=1)[0].lower().replace("_", "-")


def numero(v):
    return int(v.replace(".", ""))


def sezioni_changelog(da_esclusa, a_inclusa):
    """Titoli del CHANGELOG con versione in (da_esclusa, a_inclusa]."""
    titoli = []
    for riga in (RADICE / "CHANGELOG.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(\d{8}\.\d{4})(.*)", riga)
        if m and (not da_esclusa or numero(m.group(1)) > numero(da_esclusa)) and numero(m.group(1)) <= numero(a_inclusa):
            titoli.append(f"{m.group(1)}{m.group(2)}")
    return titoli


def main():
    solo_controllo = "--controlla" in sys.argv
    gia_confermato = "--si" in sys.argv
    versione, tag = identita.versione(), f"v{identita.versione()}"
    problemi, avvisi = [], []

    git("fetch", "--quiet", "--tags", "origin", "main")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        problemi.append("non sei sul ramo main (git checkout main)")
    if git("status", "--porcelain"):
        problemi.append("ci sono modifiche non salvate: fai commit e push prima")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        problemi.append("main locale e main su GitHub non coincidono (git pull / git push)")
    if f"## {versione}" not in (RADICE / "CHANGELOG.md").read_text(encoding="utf-8"):
        problemi.append(f"manca la voce '## {versione}' nel CHANGELOG")

    lock = identita.APP / "requisiti.lock"
    if not lock.exists():
        problemi.append("manca app/requisiti.lock (python strumenti/blocca_librerie.py)")
    else:
        bloccati = {nome_pacchetto(r) for r in lock.read_text(encoding="utf-8").splitlines()
                    if r and not r[0].isspace() and not r.startswith("#")}
        richiesti = {nome_pacchetto(r) for r in (identita.APP / "requisiti.txt").read_text(encoding="utf-8").splitlines()
                     if r.strip() and not r.startswith("#")}
        mancanti = sorted(richiesti - bloccati)
        if mancanti:
            problemi.append(f"requisiti.lock non è aggiornato, mancano: {', '.join(mancanti)} "
                            "(python strumenti/blocca_librerie.py)")
    if not (identita.APP / "chiave_aggiornamenti.pub").exists():
        if "--senza-firma" in sys.argv:
            avvisi.append("release senza firma: le app Pro verificheranno solo lo SHA-256")
        else:
            problemi.append("manca app/chiave_aggiornamenti.pub (python strumenti/genera_chiavi.py), "
                            "oppure usa --senza-firma")

    tag_pro = sorted((t for t in git("tag", "--list", "v*").split() if re.fullmatch(r"v\d{8}\.\d{4}", t)),
                     key=lambda t: numero(t[1:]))
    ultima_pro = tag_pro[-1][1:] if tag_pro else None
    if tag in tag_pro:
        problemi.append(f"la versione {versione} è già sul canale Pro (tag {tag})")
    elif ultima_pro and numero(versione) <= numero(ultima_pro):
        problemi.append(f"la versione {versione} non è più recente dell'ultima Pro ({ultima_pro})")

    print(f"App: {identita.nome()}  ({identita.repo()})")
    print(f"Versione su main (Lab): {versione}")
    print(f"Ultima versione Pro:    {ultima_pro or 'nessuna'}")
    novita = sezioni_changelog(ultima_pro, versione)
    if novita:
        print("Cosa arriverà a chi è sul canale Pro:")
        print("\n".join(f"  - {t}" for t in novita))
    for a in avvisi:
        print(f"⚠️  {a}")
    if problemi:
        print("❌ Non si può passare a Pro:")
        print("\n".join(f"  - {p}" for p in problemi))
        sys.exit(1)
    print(f"✅ Controlli superati: {versione} può passare a Pro.")
    if solo_controllo:
        return
    if not gia_confermato:
        risposta = input(f"Passo la versione {versione} al canale Pro? [s/N] ").strip().lower()
        if risposta not in ("s", "si", "sì", "y", "yes"):
            print("Nessuna modifica: la versione resta solo sul canale Lab.")
            return
    git("tag", "-a", tag, "-m", f"{identita.nome()} Pro {versione}")
    git("push", "origin", tag)
    print(f"🚀 Tag {tag} pubblicato: la GitHub Action «Rilascio Pro» sta preparando la release.")
    print(f"   Segui: https://github.com/{identita.repo()}/actions  ·  release: "
          f"https://github.com/{identita.repo()}/releases/tag/{tag}")


if __name__ == "__main__":
    main()
