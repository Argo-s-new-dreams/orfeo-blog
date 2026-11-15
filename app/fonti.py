"""fonti.py - le SOLE fonti ammesse da Orfeo, la lettura delle pagine e i livelli.

Regola editoriale di Luca: solo siti istituzionali (enti pubblici) e Microsoft ufficiale, con Microsoft Learn
in primo piano. Il controllo è nel codice: un URL fuori elenco non viene né letto né citato.
"""
import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urlparse

import comune

# Livello 1 · ente pubblico / fonte normativa
ENTI_PUBBLICI = ("europa.eu", "gov.it", "gazzettaufficiale.it", "normattiva.it", "garanteprivacy.it",
                 "senato.it", "camera.it", "governo.it", "bancaditalia.it", "consob.it", "istat.it", "gov")
# Livello 2 · Microsoft Learn
LEARN = ("learn.microsoft.com",)
# Livello 3 · altre pagine ufficiali Microsoft (roadmap, Message Center pubblico, siti di prodotto)
MICROSOFT = ("microsoft.com", "microsoft365.com", "azure.com", "office.com", "cloud.microsoft", "aka.ms")

NOMI_LIVELLO = {1: "Livello 1 · ente pubblico", 2: "Livello 2 · Microsoft Learn",
                3: "Livello 3 · Microsoft ufficiale", 0: "non ammessa"}
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


def _host(url):
    return (urlparse(url).hostname or "").lower().rstrip(".")


def _tra(host, domini):
    return any(host == d or host.endswith("." + d) for d in domini)


def livello(url):
    h = _host(url)
    if not h or urlparse(url).scheme != "https":
        return 0
    if _tra(h, LEARN):
        return 2
    if _tra(h, ENTI_PUBBLICI):
        return 1
    if _tra(h, MICROSOFT):
        return 3
    return 0


def ammessa(url):
    return livello(url) > 0


@dataclass
class Fonte:
    titolo: str
    url: str
    editore: str = ""
    data: str = ""
    estratto: str = ""
    livello: int = 0
    origine: str = ""       # "learn", "link-bozza", "link-articolo"
    id: str = ""            # S1, S2... assegnato da chi usa le fonti
    extra: dict = field(default_factory=dict)

    def riga_riferimento(self):
        data = f" ({self.data})" if self.data else ""
        ed = f" — {self.editore}" if self.editore else ""
        return f"{self.titolo}{ed}{data} — [{NOMI_LIVELLO[self.livello]}] — {self.url}"


def normalizza_url(u):
    return u.strip().rstrip(").,;>\"'")


def editore(url):
    h = _host(url)
    return h[4:] if h.startswith("www.") else h


# ---------------------------------------------------------------- testo da HTML
class _Estrattore(HTMLParser):
    SALTA = {"script", "style", "noscript", "nav", "footer", "header", "svg", "form", "aside"}
    BLOCCHI = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "tr", "br", "section", "article", "td", "th"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parti, self.salta, self.titolo, self._in_title = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in self.SALTA:
            self.salta += 1
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCCHI:
            self.parti.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SALTA and self.salta:
            self.salta -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, d):
        if self._in_title:
            self.titolo += d
        elif not self.salta:
            self.parti.append(d)


def testo_da_html(h):
    e = _Estrattore()
    try:
        e.feed(h)
    except Exception:
        pass
    t = re.sub(r"[ \t\r\f\v]+", " ", "".join(e.parti))
    t = re.sub(r"\n\s*\n+", "\n\n", t)
    return e.titolo.strip(), t.strip()


def leggi_pagina(url, max_car=8000):
    """Scarica una pagina AMMESSA e ritorna una Fonte con il testo. Le pagine di Learn passano dal server MCP."""
    url = normalizza_url(url)
    if not ammessa(url):
        raise ValueError(f"fonte non ammessa (solo enti pubblici e Microsoft ufficiale): {url}")
    if livello(url) == 2:
        import learn_mcp
        testo = learn_mcp.leggi(url, max_car)
        m = re.search(r"^#\s+(.+)$", testo, flags=re.M)
        return Fonte(titolo=(m.group(1).strip() if m else url)[:200], url=url, editore="Microsoft Learn",
                     estratto=testo, livello=2)
    _, corpo, tipo = comune.http(url, intestazioni={"Accept": "text/html,application/xhtml+xml,*/*;q=0.5"})
    if "pdf" in tipo.lower() or url.lower().endswith(".pdf"):
        import io
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(corpo))
        testo = "\n".join((p.extract_text() or "") for p in r.pages[:20])
        titolo = (r.metadata.title if r.metadata and r.metadata.title else "") or url.rsplit("/", 1)[-1]
    else:
        titolo, testo = testo_da_html(corpo.decode("utf-8", "replace"))
    return Fonte(titolo=html.unescape(titolo)[:200] or url, url=url, editore=editore(url),
                 estratto=testo[:max_car], livello=livello(url))


def normalizza_testo(t):
    """Per confrontare una citazione con la fonte: minuscole, spazi e virgolette uniformi, niente markdown."""
    t = html.unescape(t or "").lower()
    t = re.sub(r"[*_`#>|]", " ", t)
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


def citazione_presente(citazione, testo_fonte, minimo=20):
    """True solo se la citazione (almeno `minimo` caratteri) compare davvero nel testo della fonte."""
    c = normalizza_testo(citazione).strip(" .\"'")
    return len(c) >= minimo and c in normalizza_testo(testo_fonte)
