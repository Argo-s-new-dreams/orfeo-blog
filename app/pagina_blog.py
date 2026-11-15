"""pagina_blog.py - cartella di lavoro, regole di scrittura e collegamenti in rete FACOLTATIVI (feed, link, WordPress).

Standard famiglia Argo: tutto ciò che va in rete è spento di default e si accende qui, in modo visibile.
"""
from PySide6.QtWidgets import (QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox)

import comune
import dati
import fonti as F
import motore
import wordpress as wp
from lavoro import Lavoro
from pagina_bozza import aggiorna_bollino
from pagine import Pagina


def nota(testo):
    l_ = QLabel(testo)
    l_.setWordWrap(True)
    l_.setProperty("ruolo", "tenue")
    return l_


class PaginaBlog(Pagina):
    titolo = "Blog"

    def costruisci(self, lay):
        self.sottotitolo("Dove lavora Orfeo, come scrive e, solo se lo attivi, cosa può leggere e scrivere in rete.")
        imp = dati.carica_impostazioni()

        g = QGroupBox("Cartella di lavoro")
        f = QFormLayout(g)
        self.e_cart = QLineEdit(imp["cartella"])
        r = QHBoxLayout()
        b = QPushButton("Scegli…")
        b.clicked.connect(self._scegli)
        r.addWidget(self.e_cart, 1)
        r.addWidget(b)
        f.addRow("Cartella", r)
        f.addRow("", nota(f"Sottocartelle: in-arrivo, bozze, elaborati, config. Il tuo stile editoriale va in "
                          f"config/{motore.FILE_STILE}."))
        lay.addWidget(g)

        g = QGroupBox("Scrittura")
        f = QFormLayout(g)
        self.s_parole = QSpinBox()
        self.s_parole.setRange(500, 4000)
        self.s_parole.setSingleStep(100)
        self.s_parole.setValue(int(imp["parole"]))
        self.s_ctx = QSpinBox()
        self.s_ctx.setRange(4096, 131072)
        self.s_ctx.setSingleStep(4096)
        self.s_ctx.setValue(int(imp["contesto"]))
        self.s_temp = QDoubleSpinBox()
        self.s_temp.setRange(0, 1.5)
        self.s_temp.setSingleStep(0.1)
        self.s_temp.setValue(float(imp["temperatura"]))
        f.addRow("Lunghezza (parole)", self.s_parole)
        f.addRow("Contesto (token)", self.s_ctx)
        f.addRow("Creatività", self.s_temp)
        f.addRow("", nota("Il modello si sceglie in Impostazioni. Per un Mac da 16 GB: gemma3:12b con 16384 token."))
        lay.addWidget(g)

        g = QGroupBox("Rete (facoltativa, spenta di default)")
        f = QFormLayout(g)
        self.k_link = QCheckBox("Leggi le pagine dei link messi negli appunti (diventano le fonti citate)")
        self.k_link.setChecked(bool(imp["leggi_link"]))
        self.k_feed = QCheckBox("Se «In arrivo» è vuota, cerca un tema nelle novità dei feed ufficiali")
        self.k_feed.setChecked(bool(imp["usa_feed"]))
        self.s_giorni = QSpinBox()
        self.s_giorni.setRange(1, 31)
        self.s_giorni.setValue(int(imp["giorni_novita"]))
        self.e_temi = QLineEdit(imp["temi_novita"])
        self.t_feed = QPlainTextEdit("\n".join(imp["feed"]))
        self.t_feed.setFixedHeight(100)
        r = QHBoxLayout()
        self.b_feed = QPushButton("Prova i feed")
        self.b_feed.clicked.connect(self._prova_feed)
        r.addWidget(self.b_feed)
        r.addStretch(1)
        f.addRow("", self.k_link)
        f.addRow("", self.k_feed)
        f.addRow("Ultimi giorni", self.s_giorni)
        f.addRow("Temi", self.e_temi)
        f.addRow("Feed", self.t_feed)
        f.addRow("", r)
        f.addRow("", nota("Una riga per feed: <code>nome | url | livello</code> (1 fonte ufficiale, 2 ricerca "
                          "accademica, 3 annuncio del vendor). Le righe che iniziano con # sono disattivate. "
                          "Esce in rete solo la richiesta della pagina: i tuoi appunti restano sul computer."))
        lay.addWidget(g)

        g = QGroupBox("WordPress (solo bozze, spento di default)")
        f = QFormLayout(g)
        self.k_wp = QCheckBox("Crea la bozza anche sul blog e leggi i post pubblicati per i link interni")
        self.k_wp.setChecked(bool(imp["wordpress_attivo"]))
        self.e_sito = QLineEdit(imp["wp_sito"])
        self.e_utente = QLineEdit(imp["wp_utente"])
        self.e_pw = QLineEdit()
        self.e_pw.setEchoMode(QLineEdit.Password)
        if imp["wp_utente"] and comune.leggi_password(imp["wp_utente"]):
            self.e_pw.setPlaceholderText("già salvata nel portachiavi")
        r = QHBoxLayout()
        self.b_wp = QPushButton("Verifica collegamento")
        self.b_wp.clicked.connect(self._verifica_wp)
        r.addWidget(self.b_wp)
        r.addStretch(1)
        f.addRow("", self.k_wp)
        f.addRow("Sito", self.e_sito)
        f.addRow("Utente", self.e_utente)
        f.addRow("Password applicazione", self.e_pw)
        f.addRow("", r)
        f.addRow("", nota("Crea una <i>password applicazione</i> in wp-admin → Utenti → Profilo (non la password di "
                          "accesso). Resta nel portachiavi del sistema, mai su file. Orfeo può solo creare bozze: "
                          "non pubblica e non modifica post esistenti."))
        lay.addWidget(g)

        r = QHBoxLayout()
        b = QPushButton("Salva")
        b.setProperty("primario", True)
        b.clicked.connect(self.salva)
        r.addWidget(b)
        r.addStretch(1)
        lay.addLayout(r)
        lay.addStretch(1)

    def _scegli(self):
        d = QFileDialog.getExistingDirectory(self, "Cartella di lavoro di Orfeo", self.e_cart.text())
        if d:
            self.e_cart.setText(d)

    def _verifica_wp(self):
        sito, utente = self.e_sito.text().strip(), self.e_utente.text().strip()
        pw = self.e_pw.text().strip() or comune.leggi_password(utente)
        if not (utente and pw):
            QMessageBox.information(self, "WordPress", "Inserisci utente e password applicazione.")
            return
        lav = Lavoro(lambda _l: wp.verifica(sito, utente, pw), self)
        lav.sig_fatto.connect(lambda nome: (self.b_wp.setEnabled(True), QMessageBox.information(
            self, "WordPress", f"Collegamento riuscito: utente «{nome}». Ricordati di premere Salva.")))
        lav.sig_errore.connect(lambda e: (self.b_wp.setEnabled(True), QMessageBox.warning(self, "WordPress", e)))
        self.b_wp.setEnabled(False)
        self.tieni(lav).start()

    def _prova_feed(self):
        righe, giorni = self.t_feed.toPlainText().splitlines(), self.s_giorni.value()

        def fn(l):
            out = []
            for nome, url, liv in F.analizza_righe_feed(righe):
                if l.fermato():
                    break
                try:
                    out.append(f"✅ {nome or url}: {len(F.leggi_feed(url, nome, liv, giorni))} novità in {giorni} giorni")
                except Exception as e:
                    out.append(f"❌ {nome or url}: {e}")
            return "\n".join(out) or "Nessun feed attivo."
        lav = Lavoro(fn, self)
        lav.sig_fatto.connect(lambda t: (self.b_feed.setEnabled(True), QMessageBox.information(self, "Prova feed", t)))
        lav.sig_errore.connect(lambda e: (self.b_feed.setEnabled(True), QMessageBox.warning(self, "Prova feed", e)))
        self.b_feed.setEnabled(False)
        self.tieni(lav).start()

    def salva(self):
        imp = dati.carica_impostazioni()
        utente = self.e_utente.text().strip()
        imp.update(cartella=self.e_cart.text().strip(), parole=self.s_parole.value(), contesto=self.s_ctx.value(),
                   temperatura=round(self.s_temp.value(), 2), leggi_link=self.k_link.isChecked(),
                   usa_feed=self.k_feed.isChecked(), giorni_novita=self.s_giorni.value(),
                   temi_novita=self.e_temi.text().strip(),
                   feed=[r for r in self.t_feed.toPlainText().splitlines() if r.strip()],
                   wordpress_attivo=self.k_wp.isChecked(), wp_sito=self.e_sito.text().strip().rstrip("/"),
                   wp_utente=utente)
        try:
            if self.e_pw.text().strip():
                comune.salva_password(utente, self.e_pw.text().strip())
                self.e_pw.clear()
                self.e_pw.setPlaceholderText("già salvata nel portachiavi")
            comune.cartelle(imp)
        except Exception as e:
            QMessageBox.warning(self, "Salvataggio", f"Non riesco a salvare: {e}")
            return
        dati.salva_impostazioni(imp)
        aggiorna_bollino(self.finestra, imp)
        self.finestra.statusBar().showMessage("Impostazioni del blog salvate.", 4000)
