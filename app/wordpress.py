"""wordpress.py - legge post e articoli della Knowledge Base, crea BOZZE di articoli (REST API di WordPress).

Sicurezza: questo modulo può solo LEGGERE e creare post con status "draft". La sola modifica di contenuti
pubblicati (gli articoli della Knowledge Base) sta in kb_applica.py, che viene chiamato unicamente dal pulsante
«Applica» nell'interfaccia, dopo la conferma di Luca: mai dal motore né dalla pianificazione.
"""
import base64
import json
import os
import urllib.error
from urllib.parse import urlencode

import comune

STATO_UNICO = "draft"


class ErroreWP(RuntimeError):
    pass


API_WPCOM = os.environ.get("ORFEO_WPCOM_API", "https://public-api.wordpress.com/wp/v2/sites")  # variabile solo per i test


def _api(sito):
    return sito.rstrip("/") + "/wp-json/wp/v2"


class Connessione:
    """Dove e come parlare con il blog.

    - metodo «wpcom» (consigliato per i siti ospitati su WordPress.com): API centrale public-api.wordpress.com
      con token OAuth; non passa dalla verifica anti-bot del dominio del blog;
    - metodo «password»: REST API del sito (/wp-json) con password applicazione.
    """

    def __init__(self, sito, api, intestazioni, descrizione):
        self.sito = sito.rstrip("/")
        self.api = api.rstrip("/")
        self.intestazioni = intestazioni
        self.descrizione = descrizione

    def h(self, json_=False):
        h = dict(self.intestazioni)
        if json_:
            h["Content-Type"] = "application/json"
        return h


def connessione(imp):
    """Costruisce la Connessione dalle impostazioni; solleva ErroreWP con un messaggio chiaro se manca qualcosa."""
    if not imp.get("wordpress_attivo"):
        raise ErroreWP("Il collegamento a WordPress è spento: attivalo nella pagina Blog.")
    sito = imp.get("wp_sito", "").strip()
    if imp.get("wp_metodo", "wpcom") == "wpcom":
        import wpcom_oauth
        blog_id, token = imp.get("wpcom_blog_id"), wpcom_oauth.leggi_token(imp)
        if not (blog_id and token):
            raise ErroreWP("Orfeo non è ancora autorizzato su WordPress.com: nella pagina Blog premi "
                           "«Collega con WordPress.com».")
        return Connessione(sito, f"{API_WPCOM}/{blog_id}", {"Authorization": f"Bearer {token}"},
                           "WordPress.com (OAuth)")
    utente = pulisci_utente(imp.get("wp_utente", ""))
    password = comune.leggi_password(utente)
    if not (utente and password):
        raise ErroreWP("Mancano utente o password applicazione di WordPress (pagina Blog).")
    return Connessione(sito, _api(sito), _auth(utente, password), "password applicazione")


def pulisci_utente(utente):
    """Il nome utente WordPress non ha la chiocciola: «@lucaborio» → «lucaborio»."""
    return (utente or "").strip().lstrip("@").strip()


def _auth(utente, password):
    tok = base64.b64encode(f"{pulisci_utente(utente)}:{password.replace(' ', '')}".encode()).decode()
    return {"Authorization": f"Basic {tok}"}


MSG_DIFENSIVA = ("WordPress.com sta proteggendo il sito con la «modalità difensiva» (verifica anti-bot "
                 "«Checking your browser…»): blocca qualunque programma prima ancora di controllare utente e "
                 "password. Disattivala nelle impostazioni Server dell'hosting (wp-admin → Hosting → Overview → "
                 "Settings → Server → Defensive mode) oppure aspetta che scada; se l'ha attivata lo staff di "
                 "WordPress.com, chiedi al supporto di disattivarla.")


def _e_sfida_antibot(corpo, tipo=""):
    """La modalità difensiva di WordPress.com risponde con una pagina HTML di verifica, non con JSON."""
    t = corpo[:4000].lower()
    return ("__challenge" in t or "hashcash" in t or "checking your browser" in t) and "json" not in tipo.lower()


def _chiama(url, dati=None, intestazioni=None, metodo=None):
    try:
        _, corpo, tipo = comune.http(url, dati, intestazioni, metodo, timeout=30)
        testo = corpo.decode("utf-8", "replace")
        if _e_sfida_antibot(testo, tipo):
            raise ErroreWP(MSG_DIFENSIVA)
        try:
            return json.loads(testo or "null")
        except json.JSONDecodeError:
            raise ErroreWP(f"WordPress ha risposto con una pagina invece che con dati: {testo[:160]}") from None
    except urllib.error.HTTPError as e:
        dettaglio = e.read().decode("utf-8", "replace")
        if _e_sfida_antibot(dettaglio, e.headers.get("Content-Type", "")):
            raise ErroreWP(MSG_DIFENSIVA) from None
        try:
            msg = json.loads(dettaglio).get("message", "")
        except Exception:
            msg = dettaglio[:200]
        if e.code in (401, 403):
            raise ErroreWP(f"WordPress ha rifiutato l'accesso ({e.code}): {msg} — controlla il collegamento "
                           "nella pagina Blog (con il metodo WordPress.com rifai «Collega con WordPress.com»).") from None
        raise ErroreWP(f"WordPress ha risposto {e.code}: {msg}") from None
    except urllib.error.URLError as e:
        raise ErroreWP(f"WordPress non raggiungibile: {e}") from None


def post_pubblicati(conn, quanti=30):
    """Post pubblicati: [{id, titolo, link}]."""
    q = urlencode({"per_page": min(quanti, 100), "_fields": "id,title,link,date", "status": "publish"})
    dati = _chiama(f"{conn.api}/posts?{q}", intestazioni=conn.h()) or []
    return [{"id": p["id"], "titolo": comune_html(p.get("title", {}).get("rendered", "")), "link": p["link"],
             "data": p.get("date", "")[:10]} for p in dati]


def comune_html(t):
    import html
    import re
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()


def elenco_kb(conn, tipo="knowledgebase"):
    """Articoli pubblicati della Knowledge Base (BasePress), con il contenuto a blocchi originale."""
    out, pagina = [], 1
    while True:
        q = urlencode({"per_page": 100, "page": pagina, "context": "edit", "status": "publish",
                       "_fields": "id,title,link,modified_gmt,content"})
        dati = _chiama(f"{conn.api}/{tipo}?{q}", intestazioni=conn.h()) or []
        for p in dati:
            out.append({"id": p["id"], "titolo": comune_html((p.get("title") or {}).get("raw") or
                                                             (p.get("title") or {}).get("rendered", "")),
                        "link": p.get("link", ""), "modified_gmt": p.get("modified_gmt", ""),
                        "raw": (p.get("content") or {}).get("raw", "")})
        if len(dati) < 100:
            return out
        pagina += 1


def leggi_kb(conn, pid, tipo="knowledgebase"):
    q = urlencode({"context": "edit", "_fields": "id,title,link,modified_gmt,content"})
    p = _chiama(f"{conn.api}/{tipo}/{int(pid)}?{q}", intestazioni=conn.h())
    return {"id": p["id"], "link": p.get("link", ""), "modified_gmt": p.get("modified_gmt", ""),
            "raw": (p.get("content") or {}).get("raw", "")}


def verifica(conn):
    """Controlla il collegamento; ritorna il nome visualizzato dell'utente."""
    dati = _chiama(f"{conn.api}/users/me?context=edit&_fields=id,name,slug", intestazioni=conn.h())
    return dati.get("name") or dati.get("slug") or "?"


def crea_bozza(conn, titolo, contenuto, estratto="", slug="", descrizione_seo=""):
    corpo = {"title": titolo, "content": contenuto, "excerpt": estratto, "status": STATO_UNICO,
             "comment_status": "open"}
    if slug:
        corpo["slug"] = slug
    if descrizione_seo:
        corpo["meta"] = {"advanced_seo_description": descrizione_seo[:155]}
    assert corpo["status"] == "draft"  # Orfeo non pubblica mai
    h = conn.h(json_=True)
    try:
        dati = _chiama(f"{conn.api}/posts", json.dumps(corpo).encode("utf-8"), h, "POST")
    except ErroreWP as e:
        if "meta" in corpo and ("meta" in str(e) or "rest_invalid_param" in str(e)):
            corpo.pop("meta")  # alcuni siti non espongono il campo SEO di Jetpack: riprovo senza
            dati = _chiama(f"{conn.api}/posts", json.dumps(corpo).encode("utf-8"), h, "POST")
        else:
            raise
    if dati.get("status") != "draft":
        raise ErroreWP(f"Stato inatteso del post creato: {dati.get('status')}. Controlla subito su WordPress.")
    pid = dati["id"]
    return {"id": pid, "modifica": f"{conn.sito}/wp-admin/post.php?post={pid}&action=edit",
            "anteprima": dati.get("link", "")}
