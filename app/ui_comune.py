"""ui_comune.py - piccoli aiuti d'interfaccia condivisi dalle pagine di Orfeo (stili solo da tema.py)."""
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

import dati
import llm_locale as llm


def apri(percorso_o_url):
    s = str(percorso_o_url or "")
    if s:
        QDesktopServices.openUrl(QUrl(s) if s.startswith("http") else QUrl.fromLocalFile(s))


def scheda():
    f = QFrame()
    f.setProperty("ruolo", "scheda")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(14, 12, 14, 12)
    return f, lay


def testo_ricco(t=""):
    l_ = QLabel(t)
    l_.setWordWrap(True)
    l_.setTextFormat(Qt.RichText)
    l_.setTextInteractionFlags(Qt.TextBrowserInteraction)
    l_.setOpenExternalLinks(True)
    return l_


def nota(testo):
    l_ = QLabel(testo)
    l_.setWordWrap(True)
    l_.setProperty("ruolo", "tenue")
    return l_


def accessi_rete(imp=None):
    imp = imp or dati.carica_impostazioni()
    return [n for k, n in (("fonti_online", "Microsoft Learn e siti istituzionali"), ("wordpress_attivo", "WordPress"))
            if imp.get(k)]


def aggiorna_bollino(finestra, imp=None):
    """Il bollino standard dice «i tuoi dati non lasciano questo computer»: vero solo con la rete spenta.
    Se Orfeo ha accessi in rete attivi, il bollino lo dichiara (standard: eccezioni sempre visibili)."""
    imp = imp or dati.carica_impostazioni()
    rete = accessi_rete(imp)
    if rete and llm.e_locale(imp.get("ollama_url", "")) and hasattr(finestra, "badge"):
        finestra.badge.setText("🔒 Modello locale  ·  🌐 in rete: " + ", ".join(rete))
    elif hasattr(finestra, "aggiorna_badge"):
        finestra.aggiorna_badge()
