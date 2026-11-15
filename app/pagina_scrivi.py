"""pagina_scrivi.py - la bozza di Luca diventa un articolo: Orfeo cerca le fonti ammesse e la sviluppa."""
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton)

import comune
import dati
import ingressi
import llm_locale as llm
import motore
from lavoro import Lavoro
from pagine import Pagina
from ui_comune import accessi_rete, aggiorna_bollino, apri, scheda, testo_ricco

ICONE = {"testo": "📝", "documento": "📄", "link": "🔗", "immagine": "🖼", "non-supportato": "⛔"}


class PaginaScrivi(Pagina):
    titolo = "Scrivi"

    def costruisci(self, lay):
        self.sottotitolo("Scrivi qui la bozza del prossimo articolo: idee, punti chiave, esperienze tue, link a fonti "
                         "ammesse. Orfeo cerca le fonti su Microsoft Learn e la sviluppa. Non pubblica mai.")
        self.lav = None
        self._ultimo = {}
        card, cl = scheda()
        self.l_stato = testo_ricco()
        cl.addWidget(self.l_stato)
        lay.addWidget(card)

        form = QFormLayout()
        self.e_tema = QLineEdit()
        self.e_tema.setPlaceholderText("Titolo provvisorio o tema (facoltativo)")
        self.c_rubrica = QComboBox()
        self.c_rubrica.setEditable(True)
        self.c_rubrica.addItems(["", "Il Bianco e il Nero"])
        form.addRow("Tema", self.e_tema)
        form.addRow("Rubrica", self.c_rubrica)
        lay.addLayout(form)
        self.t_bozza = QPlainTextEdit()
        self.t_bozza.setMinimumHeight(220)
        self.t_bozza.setPlaceholderText(
            "La tua bozza: cosa vuoi raccontare, i punti da toccare, un episodio vissuto, il messaggio finale…\n"
            "Link utili solo da fonti ammesse: learn.microsoft.com, EUR-Lex e siti istituzionali, pagine Microsoft.")
        lay.addWidget(self.t_bozza)

        ra = QHBoxLayout()
        sez = QLabel("ALLEGATI (cartella in-arrivo)")
        sez.setProperty("ruolo", "sezione")
        ra.addWidget(sez)
        ra.addStretch(1)
        for testo, slot in (("Allega file…", self.allega), ("Apri la cartella", lambda: apri(self._cartella()))):
            b = QPushButton(testo)
            b.clicked.connect(slot)
            ra.addWidget(b)
        lay.addLayout(ra)
        self.lista = QListWidget()
        self.lista.setMaximumHeight(110)
        self.lista.itemDoubleClicked.connect(lambda it: apri(it.data(Qt.UserRole)))
        lay.addWidget(self.lista)
        self.setAcceptDrops(True)

        r = QHBoxLayout()
        self.b_vai = QPushButton("Sviluppa l'articolo")
        self.b_vai.setProperty("primario", True)
        self.b_vai.clicked.connect(self.avvia)
        self.b_stop = QPushButton("Ferma")
        self.b_stop.setEnabled(False)
        self.b_stop.clicked.connect(self.ferma)
        self.k_sposta = QCheckBox("Sposta bozza e allegati usati in «elaborati»")
        self.k_sposta.setChecked(True)
        for w in (self.b_vai, self.b_stop, self.k_sposta):
            r.addWidget(w)
        r.addStretch(1)
        lay.addLayout(r)

        self.esito, el = scheda()
        self.l_esito = testo_ricco()
        el.addWidget(self.l_esito)
        r2 = QHBoxLayout()
        self.b_copia = QPushButton("Copia l'articolo")
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
        self.log.setMinimumHeight(200)
        self.log.setPlaceholderText("Qui vedi passo per passo cosa fa Orfeo. Con un modello da 12B su un Mac M4 "
                                    "un articolo richiede in genere qualche minuto.")
        lay.addWidget(self.log, 1)
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(lambda _p: QTimer.singleShot(300, self.aggiorna_allegati))
        self.aggiorna()

    # ------------------------------------------------------------ stato
    def showEvent(self, e):
        super().showEvent(e)
        if not self.lav:
            self.aggiorna()

    def _cartella(self):
        return comune.cartelle()["in-arrivo"]

    def aggiorna(self):
        imp = dati.carica_impostazioni()
        d = comune.cartelle(imp)
        try:
            chat, _ = llm.elenco_modelli(imp["ollama_url"])
            mod = imp.get("modello_chat", "")
            oll = (f"✅ Modello locale: {mod}" if mod in chat or mod + ":latest" in chat
                   else f"⚠️ Il modello «{mod or 'nessuno'}» non è installato: sceglilo in Impostazioni")
        except llm.ErroreLLM:
            oll = "⚠️ Ollama non risponde: aprilo (Orfeo prova comunque ad avviarlo)"
        stile = (d["config"] / motore.FILE_STILE).exists()
        rete = accessi_rete(imp)
        righe = [oll,
                 "✍️ Stile: il tuo v2-compact" if stile else f"✍️ Stile di base (il tuo va in config/{motore.FILE_STILE})",
                 "🌐 In rete: " + ", ".join(rete) if rete else
                 "🌐 Rete spenta: niente fonti da Microsoft Learn né bozza su WordPress (si attivano nella pagina Blog)"]
        self.l_stato.setText("<br>".join(righe))
        self.aggiorna_allegati()
        if hasattr(self.finestra, "badge"):
            aggiorna_bollino(self.finestra, imp)

    def aggiorna_allegati(self):
        c = self._cartella()
        if str(c) not in self.watcher.directories():
            if self.watcher.directories():
                self.watcher.removePaths(self.watcher.directories())
            self.watcher.addPath(str(c))
        self.lista.clear()
        for x in ingressi.leggi(c, max_car_file=300):
            det = x.nota or (", ".join(x.urls[:2]) if x.urls else x.testo.strip().replace("\n", " ")[:80])
            it = QListWidgetItem(f"{ICONE.get(x.tipo, '•')}  {x.percorso.name} — {det}")
            it.setData(Qt.UserRole, str(x.percorso))
            self.lista.addItem(it)
        if not self.lista.count():
            self.lista.addItem("Nessun allegato. Puoi trascinare qui documenti, link (.webloc) e immagini PNG.")

    def _copia_file(self, percorsi):
        for p in map(Path, percorsi):
            if p.is_file():
                shutil.copy2(p, motore.Esecuzione._libero(self._cartella() / p.name))
        self.aggiorna_allegati()

    def allega(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Allega file alla bozza", str(Path.home()),
                                                "Allegati (*.md *.txt *.docx *.pdf *.webloc *.url *.png)")
        self._copia_file(files)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self._copia_file(u.toLocalFile() for u in e.mimeData().urls())

    # ------------------------------------------------------------ esecuzione
    def _salva_bozza(self):
        testo, tema, rub = self.t_bozza.toPlainText().strip(), self.e_tema.text().strip(), self.c_rubrica.currentText().strip()
        if not (testo or tema):
            return None
        corpo = (f"rubrica: {rub}\n" if rub else "") + (f"# {tema}\n\n" if tema else "") + testo + "\n"
        nome = f"{datetime.now():%Y%m%d-%H%M}-bozza-{comune.slugify(tema or testo[:40])}.md"
        p = motore.Esecuzione._libero(self._cartella() / nome)
        p.write_text(corpo, "utf-8")
        return p

    def avvia(self):
        if self.lav:
            return
        salvata = self._salva_bozza()
        if not salvata and not ingressi.elenca(self._cartella()):
            QMessageBox.information(self, "Scrivi", "Scrivi prima la tua bozza (bastano poche righe e i punti chiave).")
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
        self.finestra.statusBar().showMessage("Orfeo sta sviluppando la bozza con il modello locale…")
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
            self.t_bozza.clear()
            self.e_tema.clear()
            t = f"<b>{ris['titolo']}</b><br>{ris['verify']} segnaposto [VERIFY] da controllare"
            if ris.get("categorie") or ris.get("tag"):
                t += f"<br>Categorie proposte: {', '.join(ris.get('categorie', []))} · Tag: {', '.join(ris.get('tag', []))}"
        else:
            t = f"<b>Nessun articolo</b> ({ris.get('esito')}): {ris.get('messaggio', '')}"
        for p in ris.get("problemi", []):
            t += f"<br>⚠️ {p}"
        self.l_esito.setText(t)
        self.b_copia.setVisible(bool(ris.get("file")))
        self.b_wp.setVisible(bool(ris.get("wp")))
        self.b_file.setVisible(bool(ris.get("file")))
        self.esito.show()
        self.finestra.statusBar().showMessage("Articolo pronto: rivedilo prima di pubblicare." if ris.get("esito") == "ok"
                                              else "Nessun articolo: leggi il riepilogo.", 8000)
        self.aggiorna()

    def copia(self):
        f = self._ultimo.get("file")
        if f and Path(f).exists():
            QGuiApplication.clipboard().setText(Path(f).read_text("utf-8"))
            self.finestra.statusBar().showMessage("Articolo copiato negli appunti (Markdown).", 4000)
