"""pagina_pianifica.py - giorno e ora in cui Orfeo prepara la bozza da solo."""
import subprocess
import sys

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QTimeEdit)

import comune
import dati
import pianificazione as pian
from pagine import Pagina

ORDINE = [1, 2, 3, 4, 5, 6, 0]  # lunedì → domenica (0 = domenica, come launchd)

NOTE_MAC = ("<b>Come funziona.</b> Orfeo registra un'attività di macOS (launchd) per il tuo utente, senza password "
            "di amministratore. A quell'ora si apre in background, controlla la Knowledge Base e ti avvisa nel "
            "Centro notifiche: quante proposte ci sono da approvare e la richiesta della bozza."
            "<br>• Se il Mac <b>dorme</b>, l'esecuzione parte al risveglio; se è <b>spento</b>, quella settimana salta."
            "<br>• Per svegliarlo qualche minuto prima, nel Terminale: <code>sudo pmset repeat wakeorpoweron M 07:35:00</code>"
            "<br>• La prima volta macOS può chiedere se Orfeo può accedere a Documenti: rispondi «Consenti»."
            "<br>• Ollama deve essere installato: se è chiuso, Orfeo prova ad aprirlo da solo.")
NOTE_WIN = ("<b>Come funziona.</b> Orfeo crea un'attività nell'Utilità di pianificazione di Windows per il tuo utente. "
            "Il computer deve essere acceso e con la sessione aperta. L'esito compare nello Storico.")


class PaginaPianifica(Pagina):
    titolo = "Pianifica"

    def costruisci(self, lay):
        self.sottotitolo("Una volta a settimana Orfeo controlla la Knowledge Base, prepara le proposte di aggiornamento "
                         "e ti chiede la bozza del prossimo articolo. Non scrive articoli da solo.")
        box = QGroupBox("Esecuzione automatica")
        form = QFormLayout(box)
        self.k_attiva = QCheckBox("Ogni settimana: controllo della Knowledge Base e richiesta della bozza")
        self.c_giorno = QComboBox()
        self.c_giorno.addItems([pian.GIORNI[g].capitalize() for g in ORDINE])
        self.t_ora = QTimeEdit()
        self.t_ora.setDisplayFormat("HH:mm")
        form.addRow("", self.k_attiva)
        form.addRow("Giorno", self.c_giorno)
        form.addRow("Ora", self.t_ora)
        lay.addWidget(box)
        r = QHBoxLayout()
        b_salva = QPushButton("Salva la pianificazione")
        b_salva.setProperty("primario", True)
        b_salva.clicked.connect(self.salva)
        b_prova = QPushButton("Prova adesso in background")
        b_prova.clicked.connect(self.prova)
        r.addWidget(b_salva)
        r.addWidget(b_prova)
        r.addStretch(1)
        lay.addLayout(r)
        self.l_stato = QLabel("")
        self.l_stato.setWordWrap(True)
        lay.addWidget(self.l_stato)
        note = QLabel(NOTE_MAC if sys.platform == "darwin" else NOTE_WIN)
        note.setWordWrap(True)
        note.setProperty("ruolo", "tenue")
        lay.addWidget(note)
        lay.addStretch(1)
        p = dati.carica_impostazioni()["pianificazione"]
        self.k_attiva.setChecked(bool(p.get("attiva")))
        self.c_giorno.setCurrentIndex(ORDINE.index(int(p.get("giorno", 1))))
        self.t_ora.setTime(QTime(int(p.get("ora", 7)), int(p.get("minuto", 40))))
        self._stato()

    def _stato(self):
        p, s = dati.carica_impostazioni()["pianificazione"], pian.stato()
        if p.get("attiva") and s["installata"]:
            self.l_stato.setText(f"✅ Attiva · prossimo controllo <b>{pian.descrivi(p['giorno'], p['ora'], p['minuto'])}</b>")
        elif p.get("attiva"):
            self.l_stato.setText("⚠️ Risulta attiva nelle impostazioni ma non nel sistema: premi «Salva la pianificazione».")
        else:
            self.l_stato.setText("Pianificazione non attiva.")

    def salva(self):
        imp = dati.carica_impostazioni()
        t = self.t_ora.time()
        nuova = {"attiva": self.k_attiva.isChecked(), "giorno": ORDINE[self.c_giorno.currentIndex()],
                 "ora": t.hour(), "minuto": t.minute()}
        try:
            if nuova["attiva"]:
                pian.attiva(nuova["giorno"], nuova["ora"], nuova["minuto"], comune.LOG_DIR)
            else:
                pian.disattiva()
        except Exception as e:
            QMessageBox.warning(self, "Pianificazione", f"{e}\n\nLa pianificazione precedente resta com'era.")
            return
        imp["pianificazione"] = nuova
        dati.salva_impostazioni(imp)
        self._stato()
        self.finestra.statusBar().showMessage("Pianificazione salvata.", 4000)

    def prova(self):
        if not pian.supportata():
            QMessageBox.information(self, "Prova", "La pianificazione è disponibile su macOS e Windows.")
            return
        try:
            subprocess.Popen(pian.comando_manuale())
        except Exception as e:
            QMessageBox.warning(self, "Prova", f"Avvio non riuscito: {e}\nSe hai spostato l'app, reinstallala.")
            return
        QMessageBox.information(self, "Prova", "Orfeo è partito in background, come farà all'ora pianificata. "
                                "Fra qualche minuto l'esito del controllo comparirà nello Storico e arriverà la notifica.")
