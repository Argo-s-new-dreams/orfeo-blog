"""wpcom_oauth.py - autorizzazione OAuth2 di WordPress.com (flusso «authorization code»).

Perché: sui siti ospitati da WordPress.com le chiamate dirette a /wp-json possono essere fermate dalla
verifica anti-bot della rete di WordPress.com. L'API centrale public-api.wordpress.com, autenticata con un token
OAuth, è la via ufficiale per i programmi. Il token vale solo per il blog indicato e resta nel portachiavi.

Passi: 1) apro nel browser https://public-api.wordpress.com/oauth2/authorize (client_id, redirect_uri,
response_type=code, blog, state); 2) WordPress.com rimanda al redirect_uri con ?code=…&state=…;
3) scambio il codice su https://public-api.wordpress.com/oauth2/token (grant_type=authorization_code).
"""
import json
import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import comune

URL_AUTORIZZA = "https://public-api.wordpress.com/oauth2/authorize"
URL_TOKEN = os.environ.get("ORFEO_WPCOM_TOKEN_URL", "https://public-api.wordpress.com/oauth2/token")  # variabile solo per i test
REDIRECT_PREDEFINITO = "http://127.0.0.1:8765/orfeo"
SERVIZIO = "Orfeo-WordPressCom"


class ErroreOAuth(RuntimeError):
    pass


def leggi_token(imp):
    cid = str(imp.get("wpcom_client_id", "")).strip()
    return comune.leggi_segreto(SERVIZIO, f"token-{cid}") if cid else ""


def leggi_secret(client_id):
    return comune.leggi_segreto(SERVIZIO, f"secret-{str(client_id).strip()}")


def url_autorizzazione(client_id, redirect, blog, state):
    return URL_AUTORIZZA + "?" + urlencode({"client_id": client_id, "redirect_uri": redirect,
                                           "response_type": "code", "blog": blog, "state": state})


def scambia_codice(client_id, client_secret, redirect, codice):
    corpo = urlencode({"client_id": client_id, "client_secret": client_secret, "redirect_uri": redirect,
                       "code": codice, "grant_type": "authorization_code"}).encode()
    try:
        _, risposta, _ = comune.http(URL_TOKEN, corpo, {"Content-Type": "application/x-www-form-urlencoded",
                                                        "Accept": "application/json"}, "POST")
    except Exception as e:
        dettaglio = ""
        if hasattr(e, "read"):
            try:
                dettaglio = json.loads(e.read().decode("utf-8", "replace")).get("error_description", "")
            except Exception:
                pass
        raise ErroreOAuth(f"WordPress.com non ha rilasciato il token: {dettaglio or e}") from None
    d = json.loads(risposta.decode("utf-8"))
    if not d.get("access_token"):
        raise ErroreOAuth(f"Risposta inattesa da WordPress.com: {str(d)[:200]}")
    return d


def salva(client_id, client_secret, dati_token):
    comune.salva_segreto(SERVIZIO, f"secret-{client_id}", client_secret)
    comune.salva_segreto(SERVIZIO, f"token-{client_id}", dati_token["access_token"])


def codice_da_url(url_o_codice, state_atteso=None):
    """Accetta l'indirizzo completo di ritorno (…?code=…&state=…) oppure solo il codice."""
    t = (url_o_codice or "").strip()
    if "code=" not in t:
        return t
    q = parse_qs(urlparse(t).query)
    if q.get("error"):
        raise ErroreOAuth(f"Autorizzazione negata: {q['error'][0]}")
    if state_atteso and q.get("state", [""])[0] != state_atteso:
        raise ErroreOAuth("L'indirizzo incollato non corrisponde a questa richiesta di autorizzazione (state diverso).")
    return q.get("code", [""])[0]


def autorizza(client_id, client_secret, blog, redirect=REDIRECT_PREDEFINITO, timeout=300, stop=lambda: False,
              apri=webbrowser.open):
    """Flusso completo con il server locale: ritorna i dati del token (access_token, blog_id, blog_url)."""
    client_id, blog = str(client_id).strip(), str(blog).strip()
    if not (client_id and client_secret and blog):
        raise ErroreOAuth("Servono Client ID, Client Secret e il sito.")
    r = urlparse(redirect)
    if r.hostname not in ("127.0.0.1", "localhost") or not r.port:
        raise ErroreOAuth("Per l'autorizzazione automatica il Redirect URL deve essere del tipo "
                          "http://127.0.0.1:8765/orfeo; altrimenti usa «Incolla indirizzo di ritorno».")
    state = secrets.token_urlsafe(16)
    ricevuto = {}

    class Gestore(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            u = urlparse(self.path)
            if u.path != r.path:
                self.send_response(404)
                self.end_headers()
                return
            q = parse_qs(u.query)
            ricevuto.update({k: v[0] for k, v in q.items()})
            ok = q.get("state", [""])[0] == state and "code" in q
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = ("Orfeo è autorizzato. Puoi chiudere questa scheda e tornare all'app." if ok else
                   "Autorizzazione non riuscita: torna a Orfeo per i dettagli.")
            self.wfile.write(f"<html><body style='font-family:system-ui;padding:40px'><h2>Orfeo</h2><p>{msg}</p>"
                             "</body></html>".encode("utf-8"))

    try:
        server = HTTPServer((r.hostname, r.port), Gestore)
    except OSError as e:
        raise ErroreOAuth(f"Non riesco ad aprire {r.hostname}:{r.port} sul computer ({e}).") from None
    server.timeout = 1
    apri(url_autorizzazione(client_id, redirect, blog, state))
    try:
        attesa = 0
        while not ricevuto and attesa < timeout and not stop():
            server.handle_request()
            attesa += 1
    finally:
        server.server_close()
    if not ricevuto:
        raise ErroreOAuth("Nessuna risposta da WordPress.com entro il tempo previsto: riprova.")
    if ricevuto.get("error"):
        raise ErroreOAuth(f"Autorizzazione negata: {ricevuto.get('error_description') or ricevuto['error']}")
    if ricevuto.get("state") != state:
        raise ErroreOAuth("Risposta non valida (state diverso): riprova.")
    dati = scambia_codice(client_id, client_secret, redirect, ricevuto["code"])
    salva(client_id, client_secret, dati)
    return dati


__all__ = ["autorizza", "scambia_codice", "codice_da_url", "url_autorizzazione", "leggi_token", "leggi_secret",
           "salva", "ErroreOAuth", "REDIRECT_PREDEFINITO"]
