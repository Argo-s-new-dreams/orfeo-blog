"""pagina_blog.py - cartella di lavoro, regole di scrittura e collegamenti in rete FACOLTATIVI (fonti, WordPress).

Standard famiglia Argo: tutto ciò che va in rete è spento di default e si accende qui, in modo visibile.
"""
from PySide6.QtWidgets import (QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLineEdit, QMessageBox, QPushButton, QSpinBox)

import comune
import dati
import motore
import wordpress as wp
from lavoro import Lavoro
from ui_comune import aggiorna_bollino, nota
from pagine import Pagina


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

        g = QGroupBox("Fonti online (facoltative, spente di default)")
        f = QFormLayout(g)
        self.k_fonti = QCheckBox("Cerca le fonti su Microsoft Learn e leggi i link ammessi")
        self.k_fonti.setChecked(bool(imp["fonti_online"]))
        self.s_kb = QSpinBox()
        self.s_kb.setRange(1, 60)
        self.s_kb.setValue(int(imp.get("kb_per_esecuzione", 5)))
        r = QHBoxLayout()
        self.b_learn = QPushButton("Prova Microsoft Learn")
        self.b_learn.clicked.connect(self._prova_learn)
        r.addWidget(self.b_learn)
        r.addStretch(1)
        f.addRow("", self.k_fonti)
        f.addRow("Articoli KB per esecuzione", self.s_kb)
        f.addRow("", r)
        f.addRow("", nota("Fonti ammesse, e solo queste: <b>enti pubblici</b> (EUR-Lex e siti *.europa.eu, *.gov.it, "
                          "Gazzetta Ufficiale, Normattiva, Garante privacy…), <b>Microsoft Learn</b> (tramite il server "
                          "MCP ufficiale learn.microsoft.com/api/mcp) e <b>pagine ufficiali Microsoft</b>. "
                          "Esce in rete solo la richiesta di ricerca o di pagina: le tue bozze restano sul computer."))
        lay.addWidget(g)

        g = QGroupBox("WordPress (spento di default)")
        f = QFormLayout(g)
        self.k_wp = QCheckBox("Collega il blog: leggi post e Knowledge Base, crea gli articoli come bozze")
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
                          "accesso). Resta nel portachiavi del sistema, mai su file. Gli articoli nuovi diventano solo "
                          "bozze; gli articoli della Knowledge Base cambiano solo quando premi «Applica»."))
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
        sito, utente = self.e_sito.text().strip(), wp.pulisci_utente(self.e_utente.text())
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

    def _prova_learn(self):
        import learn_mcp
        lav = Lavoro(lambda _l: learn_mcp.cerca("Microsoft 365 Copilot licensing", 3), self)
        lav.sig_fatto.connect(lambda r: (self.b_learn.setEnabled(True), QMessageBox.information(
            self, "Microsoft Learn", "✅ Collegamento riuscito. Prime pagine trovate:\n\n" +
            "\n".join(f"• {f.titolo}" for f in r) if r else "Collegato, ma la ricerca non ha restituito pagine.")))
        lav.sig_errore.connect(lambda e: (self.b_learn.setEnabled(True), QMessageBox.warning(self, "Microsoft Learn", e)))
        self.b_learn.setEnabled(False)
        self.tieni(lav).start()

    def salva(self):
        imp = dati.carica_impostazioni()
        utente = wp.pulisci_utente(self.e_utente.text())
        self.e_utente.setText(utente)
        imp.update(cartella=self.e_cart.text().strip(), parole=self.s_parole.value(), contesto=self.s_ctx.value(),
                   temperatura=round(self.s_temp.value(), 2), fonti_online=self.k_fonti.isChecked(),
                   kb_per_esecuzione=self.s_kb.value(), wordpress_attivo=self.k_wp.isChecked(), wp_sito=self.e_sito.text().strip().rstrip("/"),
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
