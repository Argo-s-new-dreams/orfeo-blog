"""lavoro.py - esegue le operazioni lunghe (modelli, download, file) fuori dall'interfaccia.

Uso:
    lav = Lavoro(lambda l: fai_qualcosa(on_token=l.token, stato=l.stato, stop=l.fermato), parent)
    lav.sig_token.connect(...); lav.sig_fatto.connect(...); lav.sig_errore.connect(...)
    lav.start()          # lav.ferma() per interrompere
"""
import traceback

from PySide6.QtCore import QThread, Signal


class Lavoro(QThread):
    sig_token = Signal(str)
    sig_stato = Signal(str)
    sig_fatto = Signal(object)
    sig_errore = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn
        self._stop = False

    def token(self, t):
        self.sig_token.emit(t)

    def stato(self, t):
        self.sig_stato.emit(t)

    def fermato(self):
        return self._stop

    def ferma(self):
        self._stop = True

    def run(self):
        try:
            self.sig_fatto.emit(self.fn(self))
        except Exception as e:  # l'errore arriva all'interfaccia come messaggio leggibile
            traceback.print_exc()
            self.sig_errore.emit(str(e) or e.__class__.__name__)
