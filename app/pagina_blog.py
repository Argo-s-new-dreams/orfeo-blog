"""pagina_blog.py - cartella di lavoro, regole di scrittura e collegamenti in rete FACOLTATIVI (fonti, WordPress).

Standard famiglia Argo: tutto ciò che va in rete è spento di default e si accende qui, in modo visibile.
"""
from urllib.parse import urlparse

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QInputDialog, QLineEdit, QMessageBox, QPushButton, QSpinBox, QWidget)

import comune
import dati
import motore
import wordpress as wp
import wpcom_oauth
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
        self.c_metodo = QComboBox()
        self.c_metodo.addItem("WordPress.com (OAuth) — consigliato per i siti ospitati su WordPress.com", "wpcom")
        self.c_metodo.addItem("Password applicazione (REST API del sito)", "password")
        self.c_metodo.setCurrentIndex(0 if imp.get("wp_metodo", "wpcom") == "wpcom" else 1)
        f.addRow("", self.k_wp)
        f.addRow("Sito", self.e_sito)
        f.addRow("Metodo", self.c_metodo)

        # --- WordPress.com OAuth
        self.box_wpcom = QWidget()
        fw = QFormLayout(self.box_wpcom)
        fw.setContentsMargins(0, 0, 0, 0)
        self.e_cid = QLineEdit(str(imp.get("wpcom_client_id", "")))
        self.e_secret = QLineEdit()
        self.e_secret.setEchoMode(QLineEdit.Password)
        if imp.get("wpcom_client_id") and wpcom_oauth.leggi_secret(imp["wpcom_client_id"]):
            self.e_secret.setPlaceholderText("già salvato nel portachiavi")
        self.e_redirect = QLineEdit(imp.get("wpcom_redirect") or wpcom_oauth.REDIRECT_PREDEFINITO)
        rw = QHBoxLayout()
        self.b_collega = QPushButton("Collega con WordPress.com")
        self.b_collega.clicked.connect(self._collega_wpcom)
        self.b_incolla = QPushButton("Incolla indirizzo di ritorno…")
        self.b_incolla.clicked.connect(self._incolla_ritorno)
        rw.addWidget(self.b_collega)
        rw.addWidget(self.b_incolla)
        rw.addStretch(1)
        self.l_wpcom = nota("")
        fw.addRow("Client ID", self.e_cid)
        fw.addRow("Client Secret", self.e_secret)
        fw.addRow("Redirect URL", self.e_redirect)
        fw.addRow("", rw)
        fw.addRow("", self.l_wpcom)
        fw.addRow("", nota("Una volta sola: su <b>developer.wordpress.com/apps</b> crea un'applicazione «Orfeo» con "
                           "Redirect URL <code>http://127.0.0.1:8765/orfeo</code> e copia qui Client ID e Client Secret. "
                           "Poi «Collega con WordPress.com»: si apre il browser, approvi l'accesso al blog e il token "
                           "finisce nel portachiavi."))
        f.addRow(self.box_wpcom)

        # --- password applicazione
        self.box_pw = QWidget()
        fp = QFormLayout(self.box_pw)
        fp.setContentsMargins(0, 0, 0, 0)
        self.e_utente = QLineEdit(imp["wp_utente"])
        self.e_pw = QLineEdit()
        self.e_pw.setEchoMode(QLineEdit.Password)
        if imp["wp_utente"] and comune.leggi_password(imp["wp_utente"]):
            self.e_pw.setPlaceholderText("già salvata nel portachiavi")
        fp.addRow("Utente", self.e_utente)
        fp.addRow("Password applicazione", self.e_pw)
        fp.addRow("", nota("Crea la password del sito con wp-admin/authorize-application.php (non la password di "
                           "accesso). Sui siti WordPress.com questa via può essere fermata dalla verifica anti-bot: in "
                           "quel caso usa il metodo WordPress.com."))
        f.addRow(self.box_pw)

        r = QHBoxLayout()
        self.b_wp = QPushButton("Verifica collegamento")
        self.b_wp.clicked.connect(self._verifica_wp)
        r.addWidget(self.b_wp)
        r.addStretch(1)
        f.addRow("", r)
        f.addRow("", nota("Le credenziali restano nel portachiavi del sistema, mai su file. Gli articoli nuovi "
                          "diventano solo bozze; gli articoli della Knowledge Base cambiano solo quando premi «Applica»."))
        lay.addWidget(g)
        self.c_metodo.currentIndexChanged.connect(self._mostra_metodo)
        self._mostra_metodo()

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

    def _mostra_metodo(self):
        wpcom = self.c_metodo.currentData() == "wpcom"
        self.box_wpcom.setVisible(wpcom)
        self.box_pw.setVisible(not wpcom)
        imp = dati.carica_impostazioni()
        if wpcom:
            ok = imp.get("wpcom_blog_id") and wpcom_oauth.leggi_token(imp)
            self.l_wpcom.setText(f"✅ Autorizzato (blog {imp['wpcom_blog_id']})." if ok else "Non ancora autorizzato.")

    def _imp_dal_modulo(self):
        """Impostazioni come sono scritte ora nel modulo (anche se non ancora salvate)."""
        imp = dati.carica_impostazioni()
        imp.update(wordpress_attivo=True, wp_sito=self.e_sito.text().strip().rstrip("/"),
                   wp_metodo=self.c_metodo.currentData(), wpcom_client_id=self.e_cid.text().strip(),
                   wpcom_redirect=self.e_redirect.text().strip(), wp_utente=wp.pulisci_utente(self.e_utente.text()))
        return imp

    def _salva_wpcom(self, dati_token=None):
        imp = dati.carica_impostazioni()
        imp.update(wp_metodo="wpcom", wpcom_client_id=self.e_cid.text().strip(),
                   wpcom_redirect=self.e_redirect.text().strip(), wp_sito=self.e_sito.text().strip().rstrip("/"))
        if dati_token:
            imp["wpcom_blog_id"] = str(dati_token.get("blog_id", ""))
        dati.salva_impostazioni(imp)
        self.e_secret.clear()
        self.e_secret.setPlaceholderText("già salvato nel portachiavi")
        self._mostra_metodo()

    def _dati_app(self):
        cid = self.e_cid.text().strip()
        secret = self.e_secret.text().strip() or wpcom_oauth.leggi_secret(cid)
        if not (cid and secret):
            QMessageBox.information(self, "WordPress.com", "Inserisci Client ID e Client Secret dell'app registrata "
                                    "su developer.wordpress.com/apps.")
            return None
        blog = urlparse(self.e_sito.text().strip()).hostname or self.e_sito.text().strip()
        return cid, secret, blog, self.e_redirect.text().strip()

    def _collega_wpcom(self):
        app = self._dati_app()
        if not app:
            return
        cid, secret, blog, redirect = app
        lav = Lavoro(lambda l: wpcom_oauth.autorizza(cid, secret, blog, redirect, stop=l.fermato), self)
        lav.sig_fatto.connect(lambda d: (self.b_collega.setEnabled(True), self._salva_wpcom(d), QMessageBox.information(
            self, "WordPress.com", f"Autorizzato per {d.get('blog_url', blog)}. Ora premi «Verifica collegamento».")))
        lav.sig_errore.connect(lambda e: (self.b_collega.setEnabled(True), QMessageBox.warning(self, "WordPress.com", e)))
        self.b_collega.setEnabled(False)
        self.l_wpcom.setText("Si è aperto il browser: approva l'accesso di Orfeo al blog, poi torna qui…")
        self.tieni(lav).start()

    def _incolla_ritorno(self):
        """Alternativa se WordPress.com non accetta un Redirect URL locale: si incolla l'indirizzo di ritorno."""
        app = self._dati_app()
        if not app:
            return
        cid, secret, blog, redirect = app
        import secrets as _s
        state = _s.token_urlsafe(12)
        url = wpcom_oauth.url_autorizzazione(cid, redirect, blog, state)
        QDesktopServices.openUrl(QUrl(url))
        testo, ok = QInputDialog.getText(self, "Indirizzo di ritorno",
                                         "Si è aperto il browser. Dopo aver approvato, copia qui l'indirizzo completo "
                                         "della pagina su cui arrivi (contiene «code=»):")
        if not ok or not testo.strip():
            return
        try:
            codice = wpcom_oauth.codice_da_url(testo, state)
            d = wpcom_oauth.scambia_codice(cid, secret, redirect, codice)
            wpcom_oauth.salva(cid, secret, d)
            self._salva_wpcom(d)
            QMessageBox.information(self, "WordPress.com", "Autorizzato. Ora premi «Verifica collegamento».")
        except Exception as e:
            QMessageBox.warning(self, "WordPress.com", str(e))

    def _verifica_wp(self):
        imp = self._imp_dal_modulo()
        if imp["wp_metodo"] == "password" and self.e_pw.text().strip():
            comune.salva_password(imp["wp_utente"], self.e_pw.text().strip())
        try:
            conn = wp.connessione(imp)
        except wp.ErroreWP as e:
            QMessageBox.information(self, "WordPress", str(e))
            return
        lav = Lavoro(lambda _l: wp.verifica(conn), self)
        lav.sig_fatto.connect(lambda nome: (self.b_wp.setEnabled(True), QMessageBox.information(
            self, "WordPress", f"Collegamento riuscito ({conn.descrizione}): utente «{nome}». Ricordati di premere Salva.")))
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
                   kb_per_esecuzione=self.s_kb.value(), wordpress_attivo=self.k_wp.isChecked(),
                   wp_sito=self.e_sito.text().strip().rstrip("/"), wp_utente=utente,
                   wp_metodo=self.c_metodo.currentData(), wpcom_client_id=self.e_cid.text().strip(),
                   wpcom_redirect=self.e_redirect.text().strip())
        try:
            if self.e_secret.text().strip() and self.e_cid.text().strip():
                comune.salva_segreto(wpcom_oauth.SERVIZIO, f"secret-{self.e_cid.text().strip()}", self.e_secret.text().strip())
                self.e_secret.clear()
                self.e_secret.setPlaceholderText("già salvato nel portachiavi")
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
