"""pagina_arrivo.py - il materiale per il prossimo articolo: appunti, link, documenti e immagini PNG."""
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, QTimer
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QVBoxLayout)

import comune
import ingressi
import motore
from fonti import URL_RE
from pagina_bozza import apri
from pagine import Pagina

ICONE = {"testo": "📝", "documento": "📄", "link": "🔗", "immagine": "🖼", "non-supportato": "⛔"}


class PaginaArrivo(Pagina):
    titolo = "In arrivo"

    def costruisci(self, lay):
        self.sottotitolo("Trascina qui appunti (.md, .txt, .docx, .pdf), link (.webloc, .url) e immagini PNG. "
                         "Per una rubrica scrivi in un appunto la riga «rubrica: Il Bianco e il Nero».")
        self.setAcceptDrops(True)
        r = QHBoxLayout()
        b_nuovo = QPushButton("Nuovo appunto")
        b_nuovo.setProperty("primario", True)
        b_nuovo.clicked.connect(self.nuovo_appunto)
        r.addWidget(b_nuovo)
        for testo, slot in (("Aggiungi link", self.nuovo_link), ("Aggiungi file…", self.aggiungi_file),
                            ("Apri la cartella", lambda: apri(self._cartella()))):
            b = QPushButton(testo)
            b.clicked.connect(slot)
            r.addWidget(b)
        r.addStretch(1)
        lay.addLayout(r)
        self.lista = QListWidget()
        self.lista.setMinimumHeight(380)
        self.lista.itemDoubleClicked.connect(lambda it: apri(it.data(Qt.UserRole)))
        lay.addWidget(self.lista, 1)
        nota = QLabel("Doppio clic per aprire un file. I file usati vengono spostati in «elaborati», mai cancellati.")
        nota.setProperty("ruolo", "tenue")
        lay.addWidget(nota)
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(lambda _p: QTimer.singleShot(300, self.aggiorna))
        self.aggiorna()

    def showEvent(self, e):
        super().showEvent(e)
        self.aggiorna()

    def _cartella(self):
        return comune.cartelle()["in-arrivo"]

    def aggiorna(self):
        c = self._cartella()
        if str(c) not in self.watcher.directories():
            if self.watcher.directories():
                self.watcher.removePaths(self.watcher.directories())
            self.watcher.addPath(str(c))
        self.lista.clear()
        for x in ingressi.leggi(c, max_car_file=400):
            det = x.nota or (", ".join(x.urls[:2]) if x.urls else x.testo.strip().replace("\n", " ")[:90])
            rub = f"  ·  rubrica: {x.rubrica}" if x.rubrica else ""
            it = QListWidgetItem(f"{ICONE.get(x.tipo, '•')}  {x.percorso.name}{rub}\n      {det}")
            it.setData(Qt.UserRole, str(x.percorso))
            self.lista.addItem(it)
        if not self.lista.count():
            self.lista.addItem("Nessun file in arrivo.")

    def _salva(self, nome, testo):
        motore.Esecuzione._libero(self._cartella() / nome).write_text(testo, "utf-8")
        self.aggiorna()

    def _dialogo(self, titolo):
        dlg = QDialog(self)
        dlg.setWindowTitle(titolo)
        dlg.resize(640, 460)
        v = QVBoxLayout(dlg)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        return dlg, v, bb

    def nuovo_appunto(self):
        dlg, v, bb = self._dialogo("Nuovo appunto per Orfeo")
        tema = QLineEdit()
        tema.setPlaceholderText("Tema (facoltativo)")
        rubrica = QComboBox()
        rubrica.setEditable(True)
        rubrica.addItems(["", "Il Bianco e il Nero"])
        testo = QPlainTextEdit()
        testo.setPlaceholderText("Idee, punti chiave, esperienze tue, link a fonti ufficiali (Microsoft Learn, EUR-Lex, paper)…")
        form = QFormLayout()
        form.addRow("Tema", tema)
        form.addRow("Rubrica", rubrica)
        v.addLayout(form)
        v.addWidget(testo, 1)
        v.addWidget(bb)
        if dlg.exec() != QDialog.Accepted or not (testo.toPlainText().strip() or tema.text().strip()):
            return
        corpo = f"rubrica: {rubrica.currentText().strip()}\n" if rubrica.currentText().strip() else ""
        corpo += (f"# {tema.text().strip()}\n\n" if tema.text().strip() else "") + testo.toPlainText().strip() + "\n"
        nome = comune.slugify(tema.text() or testo.toPlainText()[:40])
        self._salva(f"{datetime.now():%Y%m%d-%H%M}-{nome}.md", corpo)

    def nuovo_link(self):
        dlg, v, bb = self._dialogo("Aggiungi link")
        nota = QLabel("Uno per riga. Meglio fonti ufficiali. Orfeo li legge solo se lo attivi nella pagina Blog.")
        nota.setProperty("ruolo", "tenue")
        t = QPlainTextEdit()
        v.addWidget(nota)
        v.addWidget(t, 1)
        v.addWidget(bb)
        if dlg.exec() == QDialog.Accepted:
            urls = URL_RE.findall(t.toPlainText())
            if urls:
                self._salva(f"{datetime.now():%Y%m%d-%H%M}-link.txt", "\n".join(urls) + "\n")

    def _copia(self, percorsi):
        for p in map(Path, percorsi):
            if p.is_file():
                shutil.copy2(p, motore.Esecuzione._libero(self._cartella() / p.name))
        self.aggiorna()

    def aggiungi_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Scegli i file per Orfeo", str(Path.home()),
                                                "Input (*.md *.txt *.docx *.pdf *.webloc *.url *.png)")
        self._copia(files)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self._copia(u.toLocalFile() for u in e.mimeData().urls())
