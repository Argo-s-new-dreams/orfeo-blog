"""dati.py - impostazioni e cartelle dell'utente. Tutto sta in progetto.DATI, fuori dal programma."""
import json

import progetto as P


def carica_impostazioni():
    s = dict(P.IMPOSTAZIONI_BASE)
    try:
        s.update(json.loads(P.IMPOSTAZIONI.read_text(encoding="utf-8")))
    except Exception:
        pass
    return s


def salva_impostazioni(s):
    P.DATI.mkdir(parents=True, exist_ok=True)
    tmp = P.IMPOSTAZIONI.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(P.IMPOSTAZIONI)  # scrittura atomica: un crash non lascia il file a metà
