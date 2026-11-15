"""wordpress.py - legge i post pubblicati e crea BOZZE sul blog tramite la REST API di WordPress.

Sicurezza: questo modulo può solo creare post con status "draft". Non esiste una funzione per
pubblicare, programmare, modificare o cancellare post: è una scelta voluta.
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
