"""kb_applica.py - l'UNICO punto in cui Orfeo modifica contenuti pubblicati su WordPress.

Viene importato solo dalla pagina Knowledge Base e chiamato solo dai pulsanti «Applica» e «Ripristina»,
cioè dopo la conferma esplicita di Luca. Motore e pianificazione non lo importano (lo verifica un test).

Prima di scrivere:
1. rilegge l'articolo e controlla che non sia cambiato dopo il controllo (altrimenti rifiuta);
2. salva una copia di sicurezza in dati/kb/backup/;
3. modifica SOLO il campo «content»: titolo, stato, autore e categorie non vengono toccati.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

import dati
import kb
import wordpress as wp

DIR_BACKUP = kb.KB_DIR / "backup"
DIR_ARCHIVIO = kb.KB_DIR / "archivio"


class ErroreApplica(RuntimeError):
    pass


def _connessione():
    try:
        return wp.connessione(dati.carica_impostazioni())
    except wp.ErroreWP as e:
        raise ErroreApplica(str(e)) from None


def _scrivi(conn, pid, contenuto):
    url = f"{conn.api}/knowledgebase/{int(pid)}?context=edit&_fields=id,modified_gmt,content"
    r = wp._chiama(url, json.dumps({"content": contenuto}).encode("utf-8"), conn.h(json_=True), "POST")
    if (r.get("content") or {}).get("raw", contenuto).strip() != contenuto.strip():
        raise ErroreApplica("WordPress ha salvato un contenuto diverso da quello atteso: controlla l'articolo.")
    return r


def _backup(pid, raw, motivo):
    DIR_BACKUP.mkdir(parents=True, exist_ok=True)
    f = DIR_BACKUP / f"{pid}-{datetime.now():%Y%m%d-%H%M%S}.json"
    f.write_text(json.dumps({"id": pid, "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "motivo": motivo,
                             "raw": raw}, ensure_ascii=False, indent=2), "utf-8")
    return f


def applica(file_proposta):
    p = json.loads(Path(file_proposta).read_text("utf-8"))
    conn = _connessione()
    attuale = wp.leggi_kb(conn, p["id"])
    if attuale["modified_gmt"] != p["modified_gmt"] or attuale["raw"] != p["raw_vecchio"]:
        raise ErroreApplica("L'articolo è stato modificato dopo il controllo: la proposta non è più valida. "
                            "Scartala e rifai il controllo di questo articolo.")
    copia = _backup(p["id"], attuale["raw"], f"prima di applicare {Path(file_proposta).name}")
    _scrivi(conn, p["id"], p["raw_nuovo"])
    _archivia(file_proposta, "applicata")
    st = kb.carica_stato()
    s = st.get(str(p["id"]), {})
    s.update(esito="aggiornato", proposta="", impronta=kb.impronta(p["raw_nuovo"]),
             ultimo_aggiornamento=datetime.now().strftime("%Y-%m-%d %H:%M"), backup=copia.name)
    st[str(p["id"])] = s
    kb.salva_stato(st)
    return {"id": p["id"], "titolo": p["titolo"], "link": p["link"], "backup": str(copia)}


def scarta(file_proposta):
    p = json.loads(Path(file_proposta).read_text("utf-8"))
    _archivia(file_proposta, "scartata")
    st = kb.carica_stato()
    if str(p["id"]) in st:
        st[str(p["id"])].update(esito="scartata", proposta="")
        kb.salva_stato(st)


def ripristina(pid):
    """Rimette la versione salvata prima dell'ultima modifica di Orfeo (dopo averne fatto a sua volta una copia)."""
    # solo le copie fatte prima di un «Applica»: quelle fatte prima di un ripristino non si ripristinano
    copie = [c for c in sorted(DIR_BACKUP.glob(f"{int(pid)}-*.json"))
             if json.loads(c.read_text("utf-8")).get("motivo", "").startswith("prima di applicare")]
    if not copie:
        raise ErroreApplica("Non c'è una copia di sicurezza per questo articolo.")
    vecchio = json.loads(copie[-1].read_text("utf-8"))
    conn = _connessione()
    attuale = wp.leggi_kb(conn, pid)
    _backup(pid, attuale["raw"], f"prima di ripristinare {copie[-1].name}")
    _scrivi(conn, pid, vecchio["raw"])
    copie[-1].rename(copie[-1].with_suffix(".ripristinato"))
    st = kb.carica_stato()
    if str(pid) in st:
        st[str(pid)].update(esito="ripristinato", impronta=kb.impronta(vecchio["raw"]))
        kb.salva_stato(st)
    return vecchio["data"]


def ha_backup(pid):
    return any(json.loads(c.read_text("utf-8")).get("motivo", "").startswith("prima di applicare")
               for c in DIR_BACKUP.glob(f"{int(pid)}-*.json"))


def _archivia(file_proposta, come):
    dest = DIR_ARCHIVIO / come
    dest.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_proposta), str(dest / Path(file_proposta).name))
