"""fonti.py - feed RSS/Atom, lettura pagine web e classificazione delle fonti per livello.

Ogni URL che finisce nei Riferimenti passa da qui: è stato scaricato davvero durante l'esecuzione.
"""
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

import comune

# Livello 1: fonte primaria ufficiale - Livello 2: ricerca accademica - Livello 3: annunci ufficiali dei vendor
DOMINI_LIVELLO = [
    (1, ("eur-lex.europa.eu", "europa.eu", "learn.microsoft.com", "microsoft.com/releasecommunications",
         "gazzettaufficiale.it", "garanteprivacy.it", "agid.gov.it", "acn.gov.it", "edpb.europa.eu", "normattiva.it")),
    (2, ("arxiv.org", "doi.org", "dl.acm.org", "ieeexplore.ieee.org", "nature.com", "science.org",
         "aclanthology.org", "openreview.net", "proceedings.neurips.cc", "springer.com", "sciencedirect.com")),
    (3, ("blogs.microsoft.com", "microsoft.com", "techcommunity.microsoft.com", "devblogs.microsoft.com",
         "azure.microsoft.com", "news.microsoft.com", "anthropic.com", "openai.com", "github.blog",
         "blog.google", "ai.meta.com", "mistral.ai")),
]
NOMI_LIVELLO = {1: "Livello 1 · fonte ufficiale primaria", 2: "Livello 2 · ricerca accademica",
                3: "Livello 3 · annuncio ufficiale del vendor", 0: "Non classificata"}


@dataclass
class Fonte:
    titolo: str
    url: str
    editore: str = ""
    data: str = ""          # AAAA-MM-GG se nota
    estratto: str = ""      # testo usato dal modello
    livello: int = 0
    origine: str = ""       # "feed", "input", "link-input"
    id: str = ""            # S1, S2... assegnato dal motore
    extra: dict = field(default_factory=dict)

    def riga_riferimento(self):
        data = f" ({self.data})" if self.data else ""
        ed = f" — {self.editore}" if self.editore else ""
        verifica = " [VERIFY: fonte non classificata, controllare l'autorevolezza]" if self.livello == 0 else ""
        return f"{self.titolo}{ed}{data} — [{NOMI_LIVELLO[self.livello]}] — {self.url}{verifica}"


def normalizza_url(u):
    u = u.strip().rstrip(").,;>\"'")
    # bug noto dei feed arXiv: link con il sottodominio rss.
    u = re.sub(r"^https?://rss\.arxiv\.org/abs/", "https://arxiv.org/abs/", u)
    return u


def livello(url):
    p = urlparse(url)
    host = (p.hostname or "").lower()
    percorso = host + p.path.lower()
    for liv, domini in DOMINI_LIVELLO:
        for d in domini:
            if "/" in d:
                if percorso.startswith(d):
                    return liv
            elif host == d or host.endswith("." + d):
                return liv
    return 0


def editore(url):
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


# ---------------------------------------------------------------- testo da HTML
class _Estrattore(HTMLParser):
    SALTA = {"script", "style", "noscript", "nav", "footer", "header", "svg", "form", "aside"}
    BLOCCHI = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "tr", "br", "section", "article"}

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


def leggi_pagina(url, max_car=5000):
    """Scarica una pagina e ritorna una Fonte con l'estratto di testo. Solleva eccezioni di rete."""
    url = normalizza_url(url)
    _, corpo, tipo = comune.http(url, intestazioni={"Accept": "text/html,application/xhtml+xml,*/*;q=0.5"})
    if "pdf" in tipo.lower() or url.lower().endswith(".pdf"):
        import io
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(corpo))
        testo = "\n".join((p.extract_text() or "") for p in r.pages[:15])
        titolo = (r.metadata.title if r.metadata and r.metadata.title else "") or url.rsplit("/", 1)[-1]
    else:
        titolo, testo = testo_da_html(corpo.decode("utf-8", "replace"))
    return Fonte(titolo=html.unescape(titolo)[:200] or url, url=url, editore=editore(url),
                 estratto=testo[:max_car], livello=livello(url))


# ---------------------------------------------------------------- feed
def _data(testo):
    if not testo:
        return None
    testo = testo.strip()
    try:
        d = parsedate_to_datetime(testo)
    except Exception:
        try:
            d = datetime.fromisoformat(testo.replace("Z", "+00:00"))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _pulisci(t):
    return re.sub(r"\s+", " ", testo_da_html(html.unescape(t or ""))[1]).strip()


def leggi_feed(url, nome="", liv=None, giorni=7, max_voci=25):
    """Ritorna una lista di Fonte (le voci degli ultimi `giorni`)."""
    _, corpo, _ = comune.http(url, intestazioni={"Accept": "application/rss+xml, application/atom+xml, application/xml, */*"})
    radice = ET.fromstring(corpo)
    limite = datetime.now(timezone.utc) - timedelta(days=giorni)
    voci = []
    atom = "{http://www.w3.org/2005/Atom}"
    elementi = radice.findall(".//item") or radice.findall(f".//{atom}entry")
    for it in elementi:
        if it.tag.startswith(atom):
            titolo = (it.findtext(f"{atom}title") or "").strip()
            link_el = it.find(f"{atom}link[@rel='alternate']")
            if link_el is None:  # attenzione: un Element senza figli è "falso", serve il confronto con None
                link_el = it.find(f"{atom}link")
            link = link_el.get("href", "") if link_el is not None else ""
            data = _data(it.findtext(f"{atom}updated") or it.findtext(f"{atom}published"))
            descr = it.findtext(f"{atom}summary") or it.findtext(f"{atom}content") or ""
        else:
            titolo = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            data = _data(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date"))
            descr = it.findtext("description") or ""
        if not titolo or not link:
            continue
        if data and data < limite:
            continue
        link = normalizza_url(link)
        voci.append(Fonte(titolo=_pulisci(titolo)[:200], url=link, editore=nome or editore(link),
                          data=data.strftime("%Y-%m-%d") if data else "", estratto=_pulisci(descr)[:1200],
                          livello=liv if liv is not None else livello(link), origine="feed"))
        if len(voci) >= max_voci:
            break
    return voci


def analizza_righe_feed(righe):
    """'nome | url | livello' -> [(nome, url, livello|None)]; le righe che iniziano con # sono disattivate."""
    out = []
    for r in righe:
        r = r.strip()
        if not r or r.startswith("#"):
            continue
        parti = [p.strip() for p in r.split("|")]
        if len(parti) == 1:
            nome, url, liv = "", parti[0], None
        else:
            nome, url = parti[0], parti[1]
            liv = int(parti[2]) if len(parti) > 2 and parti[2].isdigit() else None
        if url.startswith("http"):
            out.append((nome, url, liv))
    return out


def raccogli_novita(righe_feed, giorni=7, log=lambda t: None):
    tutte, errori = [], []
    for nome, url, liv in analizza_righe_feed(righe_feed):
        try:
            v = leggi_feed(url, nome, liv, giorni)
            log(f"  {nome or url}: {len(v)} novità")
            tutte.extend(v)
        except Exception as e:
            errori.append(f"{nome or url}: {e}")
            log(f"  {nome or url}: ERRORE {e}")
    return tutte, errori


URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
