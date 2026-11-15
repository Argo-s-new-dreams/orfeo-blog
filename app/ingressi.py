"""ingressi.py - legge la cartella in-arrivo: appunti, documenti, link e immagini PNG."""
import plistlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from fonti import URL_RE, normalizza_url

TESTO = {".md", ".txt", ".markdown", ".text"}
DOC = {".docx", ".pdf"}
LINK = {".webloc", ".url"}
IMMAGINI = {".png"}
IGNORA = {".ds_store", "thumbs.db", "desktop.ini"}


@dataclass
class Ingresso:
    percorso: Path
    tipo: str              # testo | documento | link | immagine | non-supportato
    testo: str = ""
    urls: list = field(default_factory=list)
    rubrica: str = ""
    nota: str = ""


def _leggi_docx(p):
    import docx
    d = docx.Document(str(p))
    righe = [par.text for par in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            righe.append(" | ".join(c.text for c in r.cells))
    return "\n".join(righe)


def _leggi_pdf(p):
    from pypdf import PdfReader
    r = PdfReader(str(p))
    return "\n".join((pg.extract_text() or "") for pg in r.pages[:30])


def _leggi_link(p):
    if p.suffix.lower() == ".webloc":
        try:
            return [plistlib.loads(p.read_bytes()).get("URL", "")]
        except Exception:
            pass
    return URL_RE.findall(p.read_text("utf-8", "replace"))


def elenca(cartella):
    """File utilizzabili in in-arrivo (niente file nascosti, niente sottocartelle)."""
    if not cartella.exists():
        return []
    return sorted((f for f in cartella.iterdir()
                   if f.is_file() and not f.name.startswith(".") and f.name.lower() not in IGNORA),
                  key=lambda f: f.stat().st_mtime)


def leggi(cartella, max_car_file=8000):
    out = []
    for f in elenca(cartella):
        est = f.suffix.lower()
        try:
            if est in TESTO:
                ing = Ingresso(f, "testo", f.read_text("utf-8", "replace"))
            elif est == ".docx":
                ing = Ingresso(f, "documento", _leggi_docx(f))
            elif est == ".pdf":
                ing = Ingresso(f, "documento", _leggi_pdf(f))
            elif est in LINK:
                ing = Ingresso(f, "link", "", [u for u in _leggi_link(f) if u])
            elif est in IMMAGINI:
                ing = Ingresso(f, "immagine")
            else:
                ing = Ingresso(f, "non-supportato", nota=f"formato {est or 'senza estensione'} non gestito: lasciato in in-arrivo")
        except Exception as e:
            ing = Ingresso(f, "non-supportato", nota=f"lettura non riuscita: {e}")
        if ing.testo:
            m = re.search(r"^\s*rubrica\s*:\s*(.+)$", ing.testo, flags=re.I | re.M)
            if m:
                ing.rubrica = m.group(1).strip()
            ing.urls = list(dict.fromkeys(ing.urls + URL_RE.findall(ing.testo)))
            ing.testo = ing.testo[:max_car_file]
        ing.urls = [normalizza_url(u) for u in ing.urls][:8]
        out.append(ing)
    return out
