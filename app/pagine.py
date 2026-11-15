"""pagine.py - base comune delle pagine: titolo, sottotitolo, area scorrevole, lavori in background."""
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class Pagina(QScrollArea):
    titolo = "Pagina"

    def __init__(self, finestra):
        super().__init__()
        self.finestra = finestra
        self._lavori = []
        self.setWidgetResizable(True)
        corpo = QWidget()
        corpo.setObjectName("pagina")
        self.lay = QVBoxLayout(corpo)
        self.lay.setContentsMargins(28, 22, 28, 22)
        self.lay.setSpacing(12)
        t = QLabel(self.titolo)
        t.setProperty("ruolo", "titolo")
        self.lay.addWidget(t)
        self.setWidget(corpo)
        self.costruisci(self.lay)

    def sottotitolo(self, testo):
        l = QLabel(testo)
        l.setProperty("ruolo", "tenue")
        l.setWordWrap(True)
        self.lay.insertWidget(1, l)
        return l

    def tieni(self, lavoro):
        """Tiene un riferimento al thread finché lavora (altrimenti Python lo distrugge a metà)."""
        self._lavori.append(lavoro)
        lavoro.finished.connect(lambda: self._lavori.remove(lavoro) if lavoro in self._lavori else None)
        return lavoro

    def costruisci(self, lay):
        raise NotImplementedError
