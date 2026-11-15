"""pagina_bozza.py - la funzione principale: dagli appunti (o dalle novità della settimana) a una bozza da rivedere."""
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout

import comune
import dati
import ingressi
import llm_locale as llm
import motore
import pianificazione as pian
from lavoro import Lavoro
from pagine import Pagina


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


def aggiorna_bollino(finestra, imp=None):
    """Il bollino standard dice «i tuoi dati non lasciano questo computer»: vero solo con la rete spenta.
    Se Orfeo ha qualche accesso in rete attivo, il bollino lo dichiara (standard: eccezioni sempre visibili)."""
    imp = imp or dati.carica_impostazioni()
    rete = [n for k, n in (("leggi_link", "link"), ("usa_feed", "feed"), ("wordpress_attivo", "WordPress"))
            if imp.get(k)]
    if rete and llm.e_locale(imp.get("ollama_url", "")):
        finestra.badge.setText("🔒 Modello locale  ·  🌐 in rete: " + ", ".join(rete))
    elif hasattr(finestra, "aggiorna_badge"):
        finestra.aggiorna_badge()


class PaginaBozza(Pagina):
    titolo = "Bozza"

    def costruisci(self, lay):
        self.sottotitolo("Orfeo legge «In arrivo» (o, se è vuota e lo hai attivato, le novità della settimana), "
                         "scrive con il modello locale e ti lascia una bozza da rivedere. Non pubblica mai.")
        self.lav = None
        self._ultimo = {}
        card, cl = scheda()
        self.l_stato = testo_ricco()
        cl.addWidget(self.l_stato)
        lay.addWidget(card)

        r = QHBoxLayout()
        self.b_vai = QPushButton("Prepara la bozza ora")
        self.b_vai.setProperty("primario", True)
        self.b_vai.clicked.connect(self.avvia)
        self.b_stop = QPushButton("Ferma")
        self.b_stop.setEnabled(False)
        self.b_stop.clicked.connect(self.ferma)
        self.k_sposta = QCheckBox("Sposta gli input usati in «elaborati»")
        self.k_sposta.setChecked(True)
        for w in (self.b_vai, self.b_stop, self.k_sposta):
            r.addWidget(w)
        r.addStretch(1)
        lay.addLayout(r)

        self.esito, el = scheda()
        self.l_esito = testo_ricco()
        el.addWidget(self.l_esito)
        r2 = QHBoxLayout()
        self.b_copia = QPushButton("Copia la bozza")
        self.b_copia.clicked.connect(self.copia)
        self.b_wp = QPushButton("Apri in WordPress")
        self.b_wp.clicked.connect(lambda: apri((self._ultimo.get("wp") or {}).get("modifica")))
        self.b_file = QPushButton("Apri il file")
        self.b_file.clicked.connect(lambda: apri(self._ultimo.get("file")))
        for b in (self.b_copia, self.b_wp, self.b_file):
            r2.addWidget(b)
        r2.addStretch(1)
        el.addLayout(r2)
        self.esito.hide()
        lay.addWidget(self.esito)

        sez = QLabel("REGISTRO")
        sez.setProperty("ruolo", "sezione")
        lay.addWidget(sez)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(260)
        self.log.setPlaceholderText("Qui vedi passo per passo cosa fa Orfeo. Con un modello da 12B su un Mac M4 "
                                    "una bozza richiede in genere qualche minuto.")
        lay.addWidget(self.log, 1)
        self.aggiorna()

    def showEvent(self, e):
        super().showEvent(e)
        if not self.lav:
            self.aggiorna()

    def aggiorna(self):
        imp = dati.carica_impostazioni()
        d = comune.cartelle(imp)
        n_in = len(ingressi.elenca(d["in-arrivo"]))
        try:
            chat, _ = llm.elenco_modelli(imp["ollama_url"])
            mod = imp.get("modello_chat", "")
            oll = (f"✅ Modello locale: {mod}" if mod in chat or mod + ":latest" in chat
                   else f"⚠️ Il modello «{mod or 'nessuno'}» non è installato: sceglilo in Impostazioni")
        except llm.ErroreLLM:
            oll = "⚠️ Ollama non risponde: aprilo (Orfeo prova comunque ad avviarlo)"
        stile = (d["config"] / motore.FILE_STILE).exists()
        rete = [n for k, n in (("leggi_link", "link degli appunti"), ("usa_feed", "feed delle novità"),
                               ("wordpress_attivo", "bozza su WordPress")) if imp.get(k)]
        p = imp["pianificazione"]
        righe = [
            oll,
            f"📥 In arrivo: {n_in} file" + ("" if n_in else (" — Orfeo sceglierà un tema dalle novità della settimana"
                                                           if imp.get("usa_feed") else " — aggiungi un appunto")),
            "✍️ Stile: il tuo v2-compact" if stile else f"✍️ Stile di base (il tuo va in config/{motore.FILE_STILE})",
            "🌐 In rete: " + ", ".join(rete) if rete else "🌐 Nessun accesso alla rete (attivabile nella pagina Blog)",
            f"🗓 Prossima esecuzione: {pian.descrivi(p['giorno'], p['ora'], p['minuto'])}"
            if p.get("attiva") and pian.stato()["installata"] else "🗓 Pianificazione non attiva",
        ]
        self.l_stato.setText("<br>".join(righe))
        if hasattr(self.finestra, "badge"):
            aggiorna_bollino(self.finestra, imp)

    def avvia(self):
        if self.lav:
            return
        self.log.clear()
        self.esito.hide()
        sposta = self.k_sposta.isChecked()
        self.lav = Lavoro(lambda l: motore.Esecuzione(log=l.stato, stop=l.fermato, sposta_input=sposta).avvia(), self)
        self.lav.sig_stato.connect(self._riga)
        self.lav.sig_fatto.connect(self._fine)
        self.lav.sig_errore.connect(lambda e: self._fine({"esito": "errore", "messaggio": e}))
        self.b_vai.setEnabled(False)
        self.b_stop.setEnabled(True)
        self.finestra.statusBar().showMessage("Orfeo sta scrivendo con il modello locale…")
        self.tieni(self.lav).start()

    def _riga(self, t):
        self.log.appendPlainText(t)
        self.finestra.statusBar().showMessage(t.split("] ", 1)[-1][:120])

    def ferma(self):
        if self.lav:
            self.lav.ferma()
            self.b_stop.setEnabled(False)
            self.log.appendPlainText("Interruzione richiesta: mi fermo al prossimo passo…")

    def _fine(self, ris):
        self.lav = None
        self._ultimo = ris
        self.b_vai.setEnabled(True)
        self.b_stop.setEnabled(False)
        if ris.get("esito") == "ok":
            t = f"<b>{ris['titolo']}</b><br>{ris['verify']} segnaposto [VERIFY] da controllare"
            if ris.get("categorie") or ris.get("tag"):
                t += f"<br>Categorie proposte: {', '.join(ris.get('categorie', []))} · Tag: {', '.join(ris.get('tag', []))}"
        else:
            t = f"<b>Nessuna bozza</b> ({ris.get('esito')}): {ris.get('messaggio', '')}"
        for p in ris.get("problemi", []):
            t += f"<br>⚠️ {p}"
        self.l_esito.setText(t)
        self.b_copia.setVisible(bool(ris.get("file")))
        self.b_wp.setVisible(bool(ris.get("wp")))
        self.b_file.setVisible(bool(ris.get("file")))
        self.esito.show()
        self.finestra.statusBar().showMessage("Bozza pronta: rivedila prima di pubblicare." if ris.get("esito") == "ok"
                                              else "Nessuna bozza: leggi il riepilogo.", 8000)
        self.aggiorna()

    def copia(self):
        f = self._ultimo.get("file")
        if f and Path(f).exists():
            QGuiApplication.clipboard().setText(Path(f).read_text("utf-8"))
            self.finestra.statusBar().showMessage("Bozza copiata negli appunti (Markdown).", 4000)
