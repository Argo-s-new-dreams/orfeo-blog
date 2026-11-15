"""main.py - finestra principale: menu laterale, pagine, barra di stato, impostazioni, aggiornamenti.

Per aggiungere una funzione:
  1. crea un file pagina_<nome>.py con una classe che eredita da pagine.Pagina;
  2. aggiungi la sua icona in tema.ICONE;
  3. registrala in PAGINE qui sotto (Impostazioni resta sempre l'ultima).
"""
import os
import sys
from pathlib import Path

# Esecuzione pianificata, senza finestra (Orfeo): su Mac launchd passa ORFEO_ESEGUI=1 con `open --env`
# (l'installer standard non inoltra argomenti al bundle), su Windows l'Utilità di pianificazione passa --esegui.
# Il controllo sta prima degli import di Qt, così l'esecuzione in background parte in fretta.
if __name__ == "__main__" and (os.environ.get("ORFEO_ESEGUI") == "1" or "--esegui" in sys.argv):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from motore import esegui_senza_finestra
    sys.exit(esegui_senza_finestra())

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget,
)

import aggiornamenti
import dati
import llm_locale as llm
import progetto as P
import tema
from lavoro import Lavoro
from pagina_blog import PaginaBlog
from pagina_kb import PaginaKB
from pagina_pianifica import PaginaPianifica
from pagina_scrivi import PaginaScrivi
from pagina_storico import PaginaStorico
from pagine import Pagina

# (chiave icona, etichetta completa, etichetta breve sotto l'icona, classe della pagina)
PAGINE = [
    ("bozza", "Scrivi", "Scrivi", PaginaScrivi),
    ("kb", "Knowledge Base", "KB", PaginaKB),
    ("storico", "Storico", "Storico", PaginaStorico),
    ("pianifica", "Pianifica", "Pianifica", PaginaPianifica),
    ("blog", "Blog", "Blog", PaginaBlog),
]


class PaginaImpostazioni(Pagina):
    titolo = "Impostazioni"

    def costruisci(self, lay):
        self.sottotitolo(f"{P.NOME} versione {P.VERSIONE}")
        imp = dati.carica_impostazioni()

        g_asp = QGroupBox("Aspetto")
        f = QFormLayout(g_asp)
        self.c_tema = QComboBox()
        self.c_tema.addItems(["scuro", "chiaro", "sistema"])
        self.c_tema.setCurrentText(imp["tema"])
        self.c_tema.currentTextChanged.connect(self.finestra.cambia_tema)
        f.addRow("Tema", self.c_tema)
        lay.addWidget(g_asp)

        g_llm = QGroupBox("Modello linguistico locale (Ollama)")
        f = QFormLayout(g_llm)
        self.e_url = QLineEdit(imp["ollama_url"])
        f.addRow("Indirizzo", self.e_url)
        riga = QHBoxLayout()
        self.c_chat = QComboBox()
        self.c_chat.setMinimumWidth(260)
        b_agg = QPushButton("Aggiorna elenco")
        b_agg.clicked.connect(self.leggi_modelli)
        riga.addWidget(self.c_chat, 1)
        riga.addWidget(b_agg)
        f.addRow("Modello per i testi", riga)
        riga2 = QHBoxLayout()
        self.e_pull = QLineEdit()
        self.e_pull.setPlaceholderText("es. gemma3:12b")
        b_pull = QPushButton("Scarica modello")
        b_pull.clicked.connect(self.scarica_modello)
        riga2.addWidget(self.e_pull, 1)
        riga2.addWidget(b_pull)
        f.addRow("Nuovo modello", riga2)
        self.l_llm = QLabel("")
        self.l_llm.setProperty("ruolo", "tenue")
        f.addRow("", self.l_llm)
        lay.addWidget(g_llm)

        g_agg = QGroupBox(f"Aggiornamenti · versione installata {P.VERSIONE}")
        v = QVBoxLayout(g_agg)
        self.k_agg = QCheckBox("Controlla gli aggiornamenti all'avvio (legge da GitHub solo il numero di versione)")
        self.k_agg.setChecked(bool(imp["controlla_aggiornamenti"]))
        v.addWidget(self.k_agg)
        r = QHBoxLayout()
        b_ora = QPushButton("Controlla ora")
        b_ora.clicked.connect(lambda: self.finestra.controlla_aggiornamenti(silenzioso=False))
        b_gh = QPushButton("Apri su GitHub")
        b_gh.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(aggiornamenti.URL_GITHUB)))
        r.addWidget(b_ora)
        r.addWidget(b_gh)
        r.addStretch(1)
        v.addLayout(r)
        self.finestra.l_agg = QLabel("")
        self.finestra.l_agg.setProperty("ruolo", "tenue")
        v.addWidget(self.finestra.l_agg)
        lay.addWidget(g_agg)

        r = QHBoxLayout()
        b_salva = QPushButton("Salva impostazioni")
        b_salva.setProperty("primario", True)
        b_salva.clicked.connect(self.salva)
        b_dati = QPushButton("Apri cartella dati")
        b_dati.clicked.connect(lambda: (P.DATI.mkdir(parents=True, exist_ok=True),
                                        QDesktopServices.openUrl(QUrl.fromLocalFile(str(P.DATI)))))
        r.addWidget(b_salva)
        r.addWidget(b_dati)
        r.addStretch(1)
        lay.addLayout(r)
        nota = QLabel(f"Dati in: {P.DATI}  ·  Testi e documenti non lasciano questo computer.")
        nota.setProperty("ruolo", "tenue")
        lay.addWidget(nota)
        lay.addStretch(1)
        QTimer.singleShot(300, self.leggi_modelli)

    def leggi_modelli(self):
        url = self.e_url.text().strip()
        attuale = dati.carica_impostazioni().get("modello_chat", "")
        try:
            chat, _emb = llm.elenco_modelli(url)
        except llm.ErroreLLM as e:
            self.l_llm.setText(f"⚠️ {e}  Scarica Ollama da ollama.com")
            return
        self.c_chat.clear()
        self.c_chat.addItems(chat)
        if attuale in chat:
            self.c_chat.setCurrentText(attuale)
        self.l_llm.setText(f"{len(chat)} modelli installati." if chat else "Nessun modello: scaricane uno qui sotto.")

    def scarica_modello(self):
        nome = self.e_pull.text().strip()
        if not nome:
            return
        url = self.e_url.text().strip()
        lav = Lavoro(lambda l: llm.scarica_modello(nome, url, on_stato=l.stato, stop=l.fermato), self)
        lav.sig_stato.connect(self.l_llm.setText)
        lav.sig_fatto.connect(lambda _r: (self.l_llm.setText(f"✅ {nome} scaricato."), self.leggi_modelli()))
        lav.sig_errore.connect(lambda e: self.l_llm.setText(f"⚠️ {e}"))
        self.tieni(lav).start()

    def salva(self):
        imp = dati.carica_impostazioni()
        imp.update({"tema": self.c_tema.currentText(), "ollama_url": self.e_url.text().strip(),
                    "modello_chat": self.c_chat.currentText(), "controlla_aggiornamenti": self.k_agg.isChecked()})
        dati.salva_impostazioni(imp)
        self.finestra.aggiorna_badge()
        self.finestra.statusBar().showMessage("Impostazioni salvate.", 4000)


class Finestra(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{P.NOME} · versione {P.VERSIONE}")
        self.resize(1200, 780)
        self.l_agg = None
        voci = [(k, et, br) for k, et, br, _c in PAGINE] + [("impostazioni", "Impostazioni", "Impostaz.")]
        self.nav = tema.NavLaterale(voci)
        self.pila = QStackedWidget()
        self.pagine = [cls(self) for _k, _e, _b, cls in PAGINE] + [PaginaImpostazioni(self)]
        for p in self.pagine:
            self.pila.addWidget(p)
        self.nav.scelto.connect(self.pila.setCurrentIndex)
        self.nav.seleziona(0)
        centro = QWidget()
        h = QHBoxLayout(centro)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self.nav)
        h.addWidget(self.pila, 1)
        self.setCentralWidget(centro)
        self.badge = QLabel("")
        self.statusBar().addPermanentWidget(self.badge)
        self.aggiorna_badge()
        self.statusBar().showMessage("Pronto. Tutto viene elaborato in locale.")
        if dati.carica_impostazioni().get("controlla_aggiornamenti", True):
            QTimer.singleShot(2500, lambda: self.controlla_aggiornamenti(silenzioso=True))

    # ---------------------------------------------------------------- stato "100% locale"
    def aggiorna_badge(self):
        url = dati.carica_impostazioni().get("ollama_url", "")
        if llm.e_locale(url):
            self.badge.setText("🔒 100% locale: i tuoi dati non lasciano questo computer")
        else:
            self.badge.setText(f"⚠️ Modello remoto: {url}")

    def cambia_tema(self, nome):
        tema.applica(QApplication.instance(), nome)
        self.nav.ricolora()

    # ---------------------------------------------------------------- aggiornamenti
    def controlla_aggiornamenti(self, silenzioso=True):
        lav = Lavoro(lambda _l: aggiornamenti.controlla(P.VERSIONE), self)

        def fatto(esito):
            nuova, remota, novita = esito
            if nuova:
                self.proponi_aggiornamento(remota, novita)
            else:
                if self.l_agg:
                    self.l_agg.setText(f"✅ Hai l'ultima versione ({P.VERSIONE}).")
                if not silenzioso:
                    QMessageBox.information(self, "Aggiornamenti", f"Hai già l'ultima versione ({P.VERSIONE}).")

        def errore(msg):
            if self.l_agg:
                self.l_agg.setText(f"⚠️ Controllo non riuscito: {msg}")
            if not silenzioso:
                QMessageBox.warning(self, "Aggiornamenti", f"Controllo non riuscito:\n{msg}")

        lav.sig_fatto.connect(fatto)
        lav.sig_errore.connect(errore)
        self._lav_agg = lav
        lav.start()

    def proponi_aggiornamento(self, remota, novita):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Nuova versione di {P.NOME}")
        dlg.resize(560, 420)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"<b>È disponibile la versione {remota}</b> (hai la {P.VERSIONE}).<br>"
                             "L'aggiornamento sostituisce solo i file del programma: impostazioni e dati restano."))
        tb = QTextBrowser()
        tb.setMarkdown(novita or "_Nessuna nota di versione._")
        lay.addWidget(tb, 1)
        bb = QDialogButtonBox()
        b_ok = bb.addButton("Aggiorna ora", QDialogButtonBox.AcceptRole)
        b_ok.setProperty("primario", True)
        bb.addButton("Più tardi", QDialogButtonBox.RejectRole)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if dlg.exec() == QDialog.Accepted:
            self.installa_aggiornamento()

    def installa_aggiornamento(self):
        cartella = Path(__file__).resolve().parent  # la cartella app/ da cui gira il programma
        lav = Lavoro(lambda l: aggiornamenti.installa(cartella, l.stato), self)
        lav.sig_stato.connect(lambda t: self.statusBar().showMessage(t))

        def fatto(esito):
            msg = f"Aggiornato alla versione {esito['versione']}."
            if esito["librerie"] == "manca_uv":
                msg += "\nServono librerie nuove ma uv non è stato trovato: rilancia l'installer."
            elif str(esito["librerie"]).startswith("errore"):
                msg += f"\nLibrerie non aggiornate: {esito['librerie']}"
            QMessageBox.information(self, "Aggiornamento completato", msg + f"\n\n{P.NOME} ora si riavvia.")
            aggiornamenti.riavvia()
            QApplication.instance().quit()

        lav.sig_fatto.connect(fatto)
        lav.sig_errore.connect(lambda e: QMessageBox.warning(self, "Aggiornamento non riuscito",
                                                             f"{e}\n\nLa versione attuale resta installata."))
        self._lav_inst = lav
        self.statusBar().showMessage("Aggiornamento in corso…")
        lav.start()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(P.NOME)
    icona = Path(__file__).with_name("icon.png")
    if icona.exists():
        app.setWindowIcon(QIcon(str(icona)))
    tema.applica(app, dati.carica_impostazioni().get("tema", "scuro"))
    w = Finestra()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
