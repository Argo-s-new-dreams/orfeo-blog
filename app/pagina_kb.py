"""pagina_kb.py - controllo della Knowledge Base: proposte di aggiornamento da approvare una per una.

È l'unica pagina che importa kb_applica: le modifiche al blog partono solo da «Applica» e «Ripristina».
"""
import html
import re
import time
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPlainTextEdit,
                               QProgressBar, QPushButton, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser,
                               QVBoxLayout, QWidget)

import comune
import dati
import fonti as F
import kb
import kb_applica
from lavoro import Lavoro
from pagine import Pagina
from ui_comune import apri, nota

PREFISSO = "\x00PROGRESSO:"  # riconosce i messaggi di avanzamento tra le righe del registro
ESITI = {"da_aggiornare": "✏️ da aggiornare", "aggiornato": "✅ in regola", "non_verificabile": "❔ non verificabile",
         "scartata": "↷ proposta scartata", "ripristinato": "↩︎ ripristinato", "errore": "❌ errore"}


def grassetto(t):
    """**testo** → <b>testo</b>, come apparirà sul blog."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


class PaginaKB(Pagina):
    titolo = "Knowledge Base"

    def costruisci(self, lay):
        self.sottotitolo("Orfeo rilegge gli articoli della Knowledge Base, cerca le prove su Microsoft Learn e sui siti "
                         "istituzionali e ti propone le correzioni. Sul blog non cambia nulla finché non premi «Applica».")
        self.lav = None
        r = QHBoxLayout()
        self.b_vai = QPushButton("Controlla ora")
        self.b_vai.setProperty("primario", True)
        self.b_vai.clicked.connect(lambda: self.controlla())
        self.s_quanti = QSpinBox()
        self.s_quanti.setRange(1, 60)
        self.s_quanti.setValue(int(dati.carica_impostazioni().get("kb_per_esecuzione", 5)))
        self.s_quanti.setSuffix(" articoli")
        self.b_uno = QPushButton("Ricontrolla l'articolo selezionato")
        self.b_uno.clicked.connect(self._ricontrolla)
        self.b_stop = QPushButton("Ferma")
        self.b_stop.setEnabled(False)
        self.b_stop.clicked.connect(lambda: self.lav and self.lav.ferma())
        for w in (self.b_vai, self.s_quanti, self.b_uno, self.b_stop):
            r.addWidget(w)
        r.addStretch(1)
        lay.addLayout(r)

        div = QSplitter(Qt.Horizontal)
        self.tab = QTableWidget(0, 4)
        self.tab.setHorizontalHeaderLabels(["Articolo", "Controllato", "Esito", "✔ / ✏️ / ❔"])
        self.tab.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tab.setAlternatingRowColors(True)
        self.tab.verticalHeader().hide()
        self.tab.itemSelectionChanged.connect(self._mostra)
        div.addWidget(self.tab)

        destra = QWidget()
        dl = QVBoxLayout(destra)
        dl.setContentsMargins(0, 0, 0, 0)
        self.dettaglio = QTextBrowser()
        self.dettaglio.setOpenExternalLinks(True)
        dl.addWidget(self.dettaglio, 1)
        rb = QHBoxLayout()
        self.b_applica = QPushButton("Applica al blog")
        self.b_applica.clicked.connect(self._applica)
        self.b_scarta = QPushButton("Scarta")
        self.b_scarta.clicked.connect(self._scarta)
        self.b_apri = QPushButton("Apri l'articolo")
        self.b_apri.clicked.connect(lambda: apri(self._sel().get("link")))
        self.b_ripr = QPushButton("Ripristina versione precedente")
        self.b_ripr.clicked.connect(self._ripristina)
        for b in (self.b_applica, self.b_scarta, self.b_apri, self.b_ripr):
            rb.addWidget(b)
        rb.addStretch(1)
        dl.addLayout(rb)
        div.addWidget(destra)
        div.setSizes([520, 680])
        div.setMinimumHeight(380)
        lay.addWidget(div, 1)

        # avanzamento: fase corrente, barra e tempo trascorso (il modello locale può impiegare minuti per passo)
        ra = QHBoxLayout()
        self.l_fase = QLabel("Fermo.")
        self.l_fase.setWordWrap(True)
        self.barra = QProgressBar()
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setMaximumWidth(320)
        self.l_tempo = QLabel("")
        ra.addWidget(self.l_fase, 1)
        ra.addWidget(self.barra)
        ra.addWidget(self.l_tempo)
        lay.addLayout(ra)
        self._inizio = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tic)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(220)
        self.log.setPlaceholderText("Registro del controllo: qui vedi ogni passaggio (affermazioni, ricerche, esiti).")
        lay.addWidget(self.log)
        lay.addWidget(nota("Fonti ammesse: enti pubblici (Livello 1), Microsoft Learn (Livello 2), pagine ufficiali "
                           "Microsoft (Livello 3). Un'affermazione risulta superata solo se la citazione si ritrova "
                           "davvero nella fonte. Prima di ogni modifica Orfeo salva una copia dell'articolo."))
        self.righe = []
        self.aggiorna()

    def showEvent(self, e):
        super().showEvent(e)
        if not self.lav:
            self.aggiorna()

    # ------------------------------------------------------------ elenco
    def aggiorna(self):
        stato = kb.carica_stato()
        aperte = {str(p["id"]): p for p in kb.proposte_aperte()}
        ordine = {"da_aggiornare": 0, "errore": 1, "non_verificabile": 2, "scartata": 3, "ripristinato": 4, "aggiornato": 5}
        self.righe = sorted(({"id": k, **v, "proposta_dati": aperte.get(k)} for k, v in stato.items()),
                            key=lambda r: (ordine.get(r.get("esito"), 9), r.get("titolo", "")))
        sel = self._sel().get("id")
        self.tab.setRowCount(len(self.righe))
        for i, r in enumerate(self.righe):
            conta = f"{r.get('confermate', 0)} / {r.get('superate', 0)} / {r.get('non_verificabili', 0)}"
            for j, v in enumerate((r.get("titolo", ""), r.get("ultimo_controllo", ""),
                                   ESITI.get(r.get("esito"), r.get("esito", "")), conta)):
                self.tab.setItem(i, j, QTableWidgetItem(v))
            if r["id"] == sel:
                self.tab.selectRow(i)
        self.tab.resizeColumnToContents(1)
        self.tab.resizeColumnToContents(2)
        if not self.righe:
            self.dettaglio.setHtml("<p>Nessun articolo controllato finora. Premi <b>Controlla ora</b>: servono "
                                   "WordPress e le fonti online attivi nella pagina Blog.</p>")
        self._pulsanti()

    def _sel(self):
        i = self.tab.currentRow()
        return self.righe[i] if 0 <= i < len(self.righe) else {}

    def _pulsanti(self):
        r = self._sel()
        libero = self.lav is None
        self.b_applica.setEnabled(libero and bool(r.get("proposta_dati")))
        self.b_scarta.setEnabled(libero and bool(r.get("proposta_dati")))
        self.b_apri.setEnabled(bool(r.get("link")))
        self.b_ripr.setEnabled(libero and bool(r) and kb_applica.ha_backup(r["id"]))
        self.b_uno.setEnabled(libero and bool(r))

    def _mostra(self):
        r = self._sel()
        self._pulsanti()
        if not r:
            return
        e = html.escape
        h = [f"<h3>{e(r.get('titolo', ''))}</h3>",
             f"<p>Controllato il {e(r.get('ultimo_controllo', ''))} · {e(ESITI.get(r.get('esito'), r.get('esito', '')))}</p>"]
        p = r.get("proposta_dati")
        if r.get("messaggio"):
            h.append(f"<p>{e(r['messaggio'])}</p>")
        if p:
            n = len(p["modifiche"])
            h.append(f"<p><b>{n} {'modifica proposta' if n == 1 else 'modifiche proposte'}</b> (in coda all'articolo verrà aggiunta una "
                     f"nota «Aggiornato il…» con le fonti):</p>")
            for m in p["modifiche"]:
                h.append(f"<hr><p><b>Prima:</b> {e(m['prima'])}</p><p><b>Dopo:</b> {grassetto(e(m['dopo']))}</p>"
                         f"<p><b>Perché:</b> {e(m['motivo'])}</p>"
                         f"<p><b>Fonte</b> ({e(F.NOMI_LIVELLO.get(m['livello'], ''))}): "
                         f"<a href=\"{e(m['fonte_url'])}\">{e(m['fonte_titolo'])}</a><br>"
                         f"<i>«{e(m['citazione'])}»</i></p>")
                if m.get("contiene_link"):
                    h.append("<p>⚠️ Il testo originale conteneva un link: nella versione nuova va rimesso a mano.</p>")
            altri = [c for c in p["controlli"] if c["esito"] != "superata"]
            if altri:
                h.append("<hr><p><b>Altre affermazioni controllate</b></p><ul>")
                for c in altri:
                    icona = "✅" if c["esito"] == "confermata" else "❔"
                    link = f' — <a href="{e(c["fonte_url"])}">fonte</a>' if c.get("fonte_url") else ""
                    h.append(f"<li>{icona} {e(c['affermazione'])} <i>({e(c['motivo'])})</i>{link}</li>")
                h.append("</ul>")
        self.dettaglio.setHtml("".join(h))

    # ------------------------------------------------------------ azioni
    def _occupa(self, lav, messaggio):
        self.lav = lav
        self.b_vai.setEnabled(False)
        self.b_stop.setEnabled(True)
        self._pulsanti()
        self.finestra.statusBar().showMessage(messaggio)
        self.tieni(lav).start()

    def _tic(self):
        if self._inizio:
            s = int(time.monotonic() - self._inizio)
            self.l_tempo.setText(f"{self.barra.value()}% · ⏱ {s // 60}:{s % 60:02d}")

    def _avanza(self, pct, fase):
        self.barra.setValue(pct)
        self.l_fase.setText(fase)
        self._tic()

    def _libera(self):
        self._timer.stop()
        self._inizio = None
        self.lav = None
        self.b_vai.setEnabled(True)
        self.b_stop.setEnabled(False)
        self.aggiorna()

    def controlla(self, solo_id=None):
        if self.lav:
            return
        imp = dati.carica_impostazioni()
        imp["kb_per_esecuzione"] = self.s_quanti.value()
        dati.salva_impostazioni(imp)
        self.log.clear()
        # l'avanzamento viaggia sullo stesso segnale del registro, con un prefisso che non finisce nel log
        lav = Lavoro(lambda l: kb.Revisione(imp, log=l.stato, stop=l.fermato, solo_id=solo_id,
                                            progresso=lambda p, f: l.stato(f"{PREFISSO}{p}|{f}")).avvia(), self)
        lav.sig_stato.connect(self._messaggio)
        self.barra.setValue(0)
        self.l_fase.setText("Avvio: collegamento a WordPress e a Ollama…")
        self._inizio = time.monotonic()
        self.l_tempo.setText("⏱ 0:00")
        self._timer.start(1000)
        lav.sig_fatto.connect(self._fine_controllo)
        lav.sig_errore.connect(lambda e: self._fine_controllo({"esito": "errore", "messaggio": e}))
        self._occupa(lav, "Orfeo sta controllando la Knowledge Base…")

    def _messaggio(self, t):
        if t.startswith(PREFISSO):
            pct, _, fase = t[len(PREFISSO):].partition("|")
            self._avanza(int(pct), fase)
            return
        self.log.appendPlainText(t)
        if "  esito: " in t:  # un articolo è finito: la tabella mostra subito il risultato
            self.aggiorna()
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        self.finestra.statusBar().showMessage(t.split("] ", 1)[-1][:120])

    def _ricontrolla(self):
        r = self._sel()
        if r:
            self.controlla(solo_id=int(r["id"]))

    def _fine_controllo(self, ris):
        ris.setdefault("origine", "manuale")
        comune.aggiungi_storico(ris)
        self._libera()
        self.l_fase.setText({"ok": "Controllo finito.", "interrotta": "Controllo fermato."}.get(ris.get("esito"),
                                                                                              "Controllo non riuscito."))
        if ris.get("esito") == "ok":
            self.barra.setValue(100)
            self.finestra.statusBar().showMessage(ris["titolo"] + ".", 8000)
        else:
            QMessageBox.warning(self, "Knowledge Base", ris.get("messaggio", "Controllo non riuscito."))
        for p in ris.get("problemi", []):
            self.log.appendPlainText(f"⚠️ {p}")

    def _applica(self):
        r = self._sel()
        p = r.get("proposta_dati")
        if not p:
            return
        if QMessageBox.question(self, "Applica al blog",
                                f"Applico {len(p['modifiche'])} modifiche a «{r['titolo']}» sul blog?\n\n"
                                "Prima salvo una copia della versione attuale: potrai ripristinarla.") != QMessageBox.Yes:
            return
        lav = Lavoro(lambda _l: kb_applica.applica(p["_file"]), self)
        lav.sig_fatto.connect(lambda esito: (self._libera(), comune.aggiungi_storico(
            {"tipo": "kb", "esito": "ok", "origine": "manuale", "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
             "titolo": f"Applicato: {esito['titolo']}", "link": esito["link"]}),
            self.finestra.statusBar().showMessage("Aggiornamento applicato al blog.", 8000)))
        lav.sig_errore.connect(lambda e: (self._libera(), QMessageBox.warning(self, "Applica", e)))
        self._occupa(lav, "Applico l'aggiornamento al blog…")

    def _scarta(self):
        r = self._sel()
        p = r.get("proposta_dati")
        if p and QMessageBox.question(self, "Scarta", f"Scarto la proposta per «{r['titolo']}»?") == QMessageBox.Yes:
            kb_applica.scarta(p["_file"])
            self.aggiorna()

    def _ripristina(self):
        r = self._sel()
        if not r or QMessageBox.question(self, "Ripristina",
                                         f"Rimetto «{r['titolo']}» com'era prima dell'ultimo aggiornamento di Orfeo?") \
                != QMessageBox.Yes:
            return
        lav = Lavoro(lambda _l: kb_applica.ripristina(r["id"]), self)
        lav.sig_fatto.connect(lambda quando: (self._libera(), self.finestra.statusBar().showMessage(
            f"Ripristinata la versione del {quando}.", 8000)))
        lav.sig_errore.connect(lambda e: (self._libera(), QMessageBox.warning(self, "Ripristina", e)))
        self._occupa(lav, "Ripristino la versione precedente…")
