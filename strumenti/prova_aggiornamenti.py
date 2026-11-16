"""prova_aggiornamenti.py - prove automatiche della verifica degli aggiornamenti Pro e dei criteri IT.

    uv run --with cryptography strumenti/prova_aggiornamenti.py

Non usa la rete: costruisce una release finta con prepara_rilascio.py e una chiave di prova,
poi controlla che Argo accetti il pacchetto buono e rifiuti quelli manomessi.
"""
import base64
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "app"))
sys.path.insert(0, str(RADICE / "strumenti"))
import aggiornamenti as agg  # noqa: E402
import criteri  # noqa: E402
import identita  # noqa: E402

FILE_VERSIONE = identita.file_versione().name  # progetto.py nelle app dal modello, trascrittore.py in Argo
VAR_CRITERI = getattr(criteri, "VARIABILE", "ARGO_CRITERI")

esiti = []


def prova(nome, condizione):
    esiti.append(condizione)
    print(("OK   " if condizione else "FALLITA ") + nome)


def rifiuta(funzione, *argomenti):
    try:
        funzione(*argomenti)
    except agg.PacchettoNonValido:
        return True
    return False


def chiavi():
    k = Ed25519PrivateKey.generate()
    priv = base64.b64encode(k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                            serialization.NoEncryption())).decode()
    pub = base64.b64encode(k.public_key().public_bytes(serialization.Encoding.Raw,
                                                       serialization.PublicFormat.Raw)).decode()
    return priv, pub


def main():
    versione = identita.versione()
    priv, pub = chiavi()
    _, pub_altra = chiavi()
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        env = dict(os.environ, ARGO_FIRMA_PRIVATA=priv, GITHUB_SHA="prova")
        r = subprocess.run([sys.executable, str(RADICE / "strumenti" / "prepara_rilascio.py"), f"v{versione}",
                            str(t / "dist"), str(t / "note.md")], env=env, capture_output=True, text=True)
        prova("prepara_rilascio crea la release", r.returncode == 0)
        if r.returncode:
            print(r.stderr)
            sys.exit(1)
        r2 = subprocess.run([sys.executable, str(RADICE / "strumenti" / "prepara_rilascio.py"), "v19990101.0000",
                             str(t / "x"), str(t / "x.md")], env=env, capture_output=True, text=True)
        prova("prepara_rilascio rifiuta un tag diverso dalla versione", r2.returncode != 0)

        man_b = (t / "dist" / agg.MANIFESTO).read_bytes()
        firma = (t / "dist" / agg.FIRMA).read_text()
        man = json.loads(man_b)
        zip_b = (t / "dist" / man["pacchetto"]).read_bytes()

        m, tipo = agg.verifica_manifesto(man_b, firma, pub, versione)
        prova("manifesto firmato accettato", m["versione"] == versione and "Ed25519" in tipo)
        prova("firma con un'altra chiave rifiutata", rifiuta(agg.verifica_manifesto, man_b, firma, pub_altra, versione))
        prova("manifesto modificato rifiutato",
              rifiuta(agg.verifica_manifesto, man_b.replace(b'"pro"', b'"lab"'), firma, pub, versione))
        prova("release senza firma rifiutata se c'è la chiave", rifiuta(agg.verifica_manifesto, man_b, None, pub, versione))
        _, tipo2 = agg.verifica_manifesto(man_b, None, None, versione)
        prova("senza chiave configurata: solo SHA-256", "SHA-256" in tipo2 and "non ancora" in tipo2)
        prova("versione del manifesto diversa dalla release rifiutata",
              rifiuta(agg.verifica_manifesto, man_b, firma, pub, "19990101.0000"))

        agg.verifica_pacchetto(zip_b, man["sha256"])
        prova("pacchetto integro accettato", True)
        prova("pacchetto manomesso rifiutato", rifiuta(agg.verifica_pacchetto, zip_b + b"x", man["sha256"]))

        dest = t / "estratto"
        agg._estrai_app(zip_b, dest)
        prova(f"pacchetto estratto con {FILE_VERSIONE} e requisiti.lock",
              (dest / FILE_VERSIONE).exists() and (dest / "requisiti.lock").exists()
              and not any("__pycache__" in p.parts for p in dest.rglob("*")))

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(f"app/{FILE_VERSIONE}", "VERSIONE = \"20990101.0000\"\n")
            z.writestr("app/../../fuori.txt", "no")
        prova("percorsi che escono dalla cartella rifiutati", rifiuta(agg._estrai_app, buf.getvalue(), t / "slip"))

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(f"repo-main/app/{FILE_VERSIONE}", "VERSIONE = \"20990101.0000\"\n")
        agg._estrai_app(buf.getvalue(), t / "lab")
        prova("ZIP del ramo (canale Lab) ancora supportato", (t / "lab" / FILE_VERSIONE).exists())

        # criteri IT
        f = t / "criteri.json"
        os.environ[VAR_CRITERI] = str(f)
        prova("nessun file criteri: nessun criterio", criteri.carica() == {})
        f.write_text(json.dumps({"canale_aggiornamenti": "pro", "aggiornamenti_dall_app": False, "altro": 1}))
        c = criteri.carica()
        prova("criteri letti, chiavi sconosciute ignorate",
              c == {"canale_aggiornamenti": "pro", "aggiornamenti_dall_app": False})
        prova("il criterio IT vince sulla scelta dell'utente",
              agg.canale_effettivo({"canale_aggiornamenti": "lab"}, c) == "pro")
        f.write_text(json.dumps({"canale_aggiornamenti": "beta"}))
        prova("valore non valido ignorato", criteri.carica() == {})
        f.write_text("{non è json")
        prova("file illeggibile vale come assente", criteri.carica() == {})
        prova("canale predefinito come da progetto", agg.canale_effettivo({}, {}) == agg.CANALE_PREDEFINITO)

    print(f"\n{sum(esiti)}/{len(esiti)} prove superate")
    sys.exit(0 if all(esiti) else 1)


if __name__ == "__main__":
    main()
