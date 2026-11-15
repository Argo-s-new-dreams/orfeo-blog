"""wordpress.py - legge post e articoli della Knowledge Base, crea BOZZE di articoli (REST API di WordPress).

Sicurezza: questo modulo può solo LEGGERE e creare post con status "draft". La sola modifica di contenuti
pubblicati (gli articoli della Knowledge Base) sta in kb_applica.py, che viene chiamato unicamente dal pulsante
«Applica» nell'interfaccia, dopo la conferma di Luca: mai dal motore né dalla pianificazione.
"""
import base64
import json
import urllib.error
from urllib.parse import urlencode

import comune

STATO_UNICO = "draft"


class ErroreWP(RuntimeError):
    pass


def _api(sito):
    return sito.rstrip("/") + "/wp-json/wp/v2"


def _auth(utente, password):
    tok = base64.b64encode(f"{utente}:{password.replace(' ', '')}".encode()).decode()
    return {"Authorization": f"Basic {tok}"}


def _chiama(url, dati=None, intestazioni=None, metodo=None):
    try:
        _, corpo, _ = comune.http(url, dati, intestazioni, metodo, timeout=30)
        return json.loads(corpo.decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        dettaglio = e.read().decode("utf-8", "replace")[:300]
        if e.code in (401, 403):
            raise ErroreWP(f"WordPress ha rifiutato le credenziali ({e.code}). Controlla utente e password "
                           f"applicazione nelle Impostazioni. Dettaglio: {dettaglio}") from None
        raise ErroreWP(f"WordPress ha risposto {e.code}: {dettaglio}") from None
    except urllib.error.URLError as e:
        raise ErroreWP(f"WordPress non raggiungibile: {e}") from None


def post_pubblicati(sito, quanti=30):
    """Post pubblici (nessuna credenziale): [{id, titolo, link}]."""
    q = urlencode({"per_page": min(quanti, 100), "_fields": "id,title,link,date", "status": "publish"})
    dati = _chiama(f"{_api(sito)}/posts?{q}") or []
    return [{"id": p["id"], "titolo": comune_html(p.get("title", {}).get("rendered", "")), "link": p["link"],
             "data": p.get("date", "")[:10]} for p in dati]


def comune_html(t):
    import html
    import re
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()


def elenco_kb(sito, utente, password, tipo="knowledgebase"):
    """Articoli pubblicati della Knowledge Base (BasePress), con il contenuto a blocchi originale."""
    out, pagina = [], 1
    while True:
        q = urlencode({"per_page": 100, "page": pagina, "context": "edit", "status": "publish",
                       "_fields": "id,title,link,modified_gmt,content"})
        dati = _chiama(f"{_api(sito)}/{tipo}?{q}", intestazioni=_auth(utente, password)) or []
        for p in dati:
            out.append({"id": p["id"], "titolo": comune_html((p.get("title") or {}).get("raw") or
                                                             (p.get("title") or {}).get("rendered", "")),
                        "link": p.get("link", ""), "modified_gmt": p.get("modified_gmt", ""),
                        "raw": (p.get("content") or {}).get("raw", "")})
        if len(dati) < 100:
            return out
        pagina += 1


def leggi_kb(sito, utente, password, pid, tipo="knowledgebase"):
    q = urlencode({"context": "edit", "_fields": "id,title,link,modified_gmt,content"})
    p = _chiama(f"{_api(sito)}/{tipo}/{int(pid)}?{q}", intestazioni=_auth(utente, password))
    return {"id": p["id"], "link": p.get("link", ""), "modified_gmt": p.get("modified_gmt", ""),
            "raw": (p.get("content") or {}).get("raw", "")}


def verifica(sito, utente, password):
    """Controlla le credenziali; ritorna il nome visualizzato dell'utente."""
    dati = _chiama(f"{_api(sito)}/users/me?context=edit", intestazioni=_auth(utente, password))
    return dati.get("name") or dati.get("slug") or utente


def crea_bozza(sito, utente, password, titolo, contenuto, estratto="", slug="", descrizione_seo=""):
    corpo = {"title": titolo, "content": contenuto, "excerpt": estratto, "status": STATO_UNICO,
             "comment_status": "open"}
    if slug:
        corpo["slug"] = slug
    if descrizione_seo:
        corpo["meta"] = {"advanced_seo_description": descrizione_seo[:155]}
    assert corpo["status"] == "draft"  # Orfeo non pubblica mai
    h = dict(_auth(utente, password), **{"Content-Type": "application/json"})
    try:
        dati = _chiama(f"{_api(sito)}/posts", json.dumps(corpo).encode("utf-8"), h, "POST")
    except ErroreWP as e:
        if "meta" in corpo and ("meta" in str(e) or "rest_invalid_param" in str(e)):
            corpo.pop("meta")  # alcuni siti non espongono il campo SEO di Jetpack: riprovo senza
            dati = _chiama(f"{_api(sito)}/posts", json.dumps(corpo).encode("utf-8"), h, "POST")
        else:
            raise
    if dati.get("status") != "draft":
        raise ErroreWP(f"Stato inatteso del post creato: {dati.get('status')}. Controlla subito su WordPress.")
    pid = dati["id"]
    return {"id": pid, "modifica": f"{sito.rstrip('/')}/wp-admin/post.php?post={pid}&action=edit",
            "anteprima": dati.get("link", "")}
