"""pagina_storico.py - le bozze preparate finora, con esito, [VERIFY] aperti e registro di ogni esecuzione."""
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
                               QTableWidgetItem)

import comune
import motore
from ui_comune import apri
from pagine import Pagina

ESITI = {"ok": "✅ fatto", "errore": "❌ errore", "nessuna-bozza": "— nessuna bozza", "interrotta": "⏹ fermata",
         "saltata": "↷ saltata"}
TIPI = {"kb": "Knowledge Base", "articolo": "Articolo"}


class PaginaStorico(Pagina):
    titolo = "Storico"

    def costruisci(self, lay):
        self.sottotitolo("Articoli sviluppati e controlli della Knowledge Base, manuali e pianificati. Doppio clic: "
                         "apre la bozza in WordPress o, se è rimasta sul computer, il file.")
        r = QHBoxLayout()
        b_apri = QPushButton("Apri la bozza selezionata")
        b_apri.setProperty("primario", True)
        b_apri.clicked.connect(lambda: self._apri(self.tab.currentRow()))
        b_copia = QPushButton("Copia il riepilogo")
        b_copia.clicked.connect(self._copia)
        b_log = QPushButton("Apri il registro")
        b_log.clicked.connect(self._log)
        b_cart = QPushButton("Cartella bozze")
        b_cart.clicked.connect(lambda: apri(comune.cartelle()["bozze"]))
        for b in (b_apri, b_copia, b_log, b_cart):
            r.addWidget(b)
        r.addStretch(1)
        lay.addLayout(r)
        self.tab = QTableWidget(0, 6)
        self.tab.setHorizontalHeaderLabels(["Data", "Cosa", "Titolo", "Esito", "[VERIFY]", "Avvio"])
        self.tab.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setAlternatingRowColors(True)
        self.tab.verticalHeader().hide()
        self.tab.setMinimumHeight(420)
        self.tab.cellDoubleClicked.connect(lambda riga, _c: self._apri(riga))
        lay.addWidget(self.tab, 1)
        self.vuoto = QLabel("Ancora nessuna esecuzione.")
        self.vuoto.setProperty("ruolo", "tenue")
        lay.addWidget(self.vuoto)
        self.st = []

    def showEvent(self, e):
        super().showEvent(e)
        self.aggiorna()

    def aggiorna(self):
        self.st = comune.carica_storico()
        self.tab.setRowCount(len(self.st))
        for i, r in enumerate(self.st):
            for j, v in enumerate((r.get("data", ""), TIPI.get(r.get("tipo"), "Articolo"),
                                   r.get("titolo") or r.get("messaggio", ""),
                                   ESITI.get(r.get("esito"), r.get("esito", "")), str(r.get("verify", "")),
                                   r.get("origine", ""))):
                self.tab.setItem(i, j, QTableWidgetItem(v))
        self.tab.resizeColumnToContents(0)
        self.vuoto.setVisible(not self.st)

    def _riga(self):
        i = self.tab.currentRow()
        return self.st[i] if 0 <= i < len(self.st) else None

    def _apri(self, i):
        if 0 <= i < len(self.st):
            r = self.st[i]
            apri((r.get("wp") or {}).get("modifica") or r.get("file") or r.get("link") or r.get("log"))

    def _copia(self):
        r = self._riga()
        if r:
            QGuiApplication.clipboard().setText(motore.report_breve(r))
            self.finestra.statusBar().showMessage("Riepilogo copiato.", 4000)

    def _log(self):
        r = self._riga()
        if r and r.get("log"):
            apri(r["log"])
