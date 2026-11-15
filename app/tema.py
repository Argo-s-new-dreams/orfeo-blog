"""tema.py - aspetto standard delle app AI locali (stile «Studio» di Argo): tema scuro/chiaro, icone, menu laterale.

Non modificare colori e QSS per una singola app: l'aspetto comune è parte dello standard.
Per una nuova pagina aggiungi solo la sua icona in ICONE (SVG a tratto, viewBox 24x24).
"""
import progetto as P
from PySide6.QtCore import QByteArray, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QButtonGroup, QLabel, QSizePolicy, QToolButton, QVBoxLayout, QWidget

ACCENTO = "#2DD4BF"
TEMI = {
    "scuro": {
        "bg": "#0F1115", "pannello": "#14171D", "pannello2": "#1A1E25", "nav": "#15181E", "bordo": "#23272F",
        "bordo2": "#2E333D", "testo": "#E6E8EE", "testo2": "#D4D8E0", "tenue": "#98A1B2", "debole": "#6B7280",
        "accento": "#2DD4BF", "su_accento": "#0F1115", "accento_bg": "#1F2A2E", "ok": "#6EE7B7", "warn": "#FBBF24",
        "err": "#FCA5A5", "sel": "#1F2A2E",
        "serie": ["#2DD4BF", "#F59E0B", "#A78BFA", "#F472B6", "#60A5FA", "#A3E635", "#FB923C", "#E879F9"],
    },
    "chiaro": {
        "bg": "#F6F7F9", "pannello": "#FFFFFF", "pannello2": "#F2F4F7", "nav": "#FFFFFF", "bordo": "#E4E7EC",
        "bordo2": "#D0D5DD", "testo": "#1F2430", "testo2": "#2B3240", "tenue": "#5B6475", "debole": "#6B7280",
        "accento": "#0F766E", "su_accento": "#FFFFFF", "accento_bg": "#E6F4F2", "ok": "#067647", "warn": "#B54708",
        "err": "#B42318", "sel": "#E6F4F2",
        "serie": ["#0F766E", "#B45309", "#6D28D9", "#BE185D", "#1D4ED8", "#4D7C0F", "#C2410C", "#A21CAF"],
    },
}
_attuale = {"nome": "scuro"}


def risolvi(nome):
    if nome in TEMI:
        return nome
    try:  # "sistema"
        sch = QGuiApplication.styleHints().colorScheme()
        return "chiaro" if sch == Qt.ColorScheme.Light else "scuro"
    except Exception:
        return "scuro"


def colori():
    return TEMI[_attuale["nome"]]


def qss(c):
    return f"""
* {{ font-family: "Inter", "SF Pro Text", "Segoe UI", system-ui, sans-serif; font-size: 13px; }}
QMainWindow, QDialog, QWidget#pagina {{ background: {c['bg']}; }}
QWidget {{ color: {c['testo']}; }}
QLabel {{ background: transparent; }}
QLabel[ruolo="titolo"] {{ font-size: 20px; font-weight: 600; }}
QLabel[ruolo="tenue"] {{ color: {c['tenue']}; }}
QLabel[ruolo="sezione"] {{ color: {c['tenue']}; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
QWidget#nav {{ background: {c['nav']}; border-right: 1px solid {c['bordo']}; }}
QLabel#logo {{ background: {c['accento']}; color: {c['su_accento']}; border-radius: 12px; font-weight: 800; font-size: 17px; }}
QToolButton[nav="true"] {{ background: transparent; color: {c['tenue']}; border: none; border-radius: 12px;
    padding: 6px 2px; font-size: 10px; }}
QToolButton[nav="true"]:hover {{ background: {c['pannello2']}; color: {c['testo']}; }}
QToolButton[nav="true"]:checked {{ background: {c['accento_bg']}; color: {c['accento']}; }}
QTabWidget::pane {{ border: none; background: {c['bg']}; }}
QGroupBox {{ background: {c['pannello']}; border: 1px solid {c['bordo']}; border-radius: 12px; margin-top: 22px;
    padding: 14px 12px 12px 12px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; top: 2px; color: {c['testo']}; }}
QPushButton, QToolButton {{ background: {c['pannello2']}; color: {c['testo']}; border: 1px solid {c['bordo2']};
    border-radius: 8px; padding: 7px 14px; min-height: 20px; }}
QPushButton:hover, QToolButton:hover {{ border-color: {c['accento']}; }}
QPushButton:pressed {{ background: {c['accento_bg']}; }}
QPushButton:disabled {{ color: {c['debole']}; border-color: {c['bordo']}; }}
QPushButton[primario="true"] {{ background: {c['accento']}; color: {c['su_accento']}; border: none; font-weight: 600; }}
QPushButton[primario="true"]:hover {{ background: {c['accento']}; border: 1px solid {c['testo']}; }}
QPushButton[pillola="true"] {{ border-radius: 14px; padding: 5px 14px; color: {c['tenue']}; }}
QPushButton[pillola="true"]:checked {{ background: {c['accento_bg']}; color: {c['accento']}; border-color: {c['accento']}; }}
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {c['pannello2']}; color: {c['testo']}; border: 1px solid {c['bordo2']}; border-radius: 8px;
    padding: 6px 8px; selection-background-color: {c['accento']}; selection-color: {c['su_accento']}; }}
QPlainTextEdit, QTextEdit, QTextBrowser {{ background: {c['pannello']}; border-color: {c['bordo']}; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {c['accento']}; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; width: 18px; border: none; background: transparent; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-position: bottom right; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ width: 0; height: 0; border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-bottom: 5px solid {c['tenue']}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ width: 0; height: 0; border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-top: 5px solid {c['tenue']}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {c['tenue']}; }}
QComboBox QAbstractItemView {{ background: {c['pannello2']}; color: {c['testo']}; selection-background-color: {c['accento_bg']};
    selection-color: {c['accento']}; border: 1px solid {c['bordo2']}; }}
QTableWidget, QTableView, QListWidget {{ background: {c['pannello']}; alternate-background-color: {c['pannello2']};
    border: 1px solid {c['bordo']}; border-radius: 10px; gridline-color: {c['bordo']};
    selection-background-color: {c['sel']}; selection-color: {c['testo']}; }}
QHeaderView::section {{ background: {c['pannello2']}; color: {c['tenue']}; border: none; border-bottom: 1px solid {c['bordo']};
    padding: 6px 8px; font-weight: 600; }}
QTableCornerButton::section {{ background: {c['pannello2']}; border: none; }}
QProgressBar {{ background: {c['bordo']}; border: none; border-radius: 4px; height: 8px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {c['accento']}; border-radius: 4px; }}
QSplitter::handle {{ background: {c['bordo']}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
QScrollArea {{ border: none; background: {c['bg']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['bordo2']}; border-radius: 4px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {c['bordo2']}; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QStatusBar {{ background: {c['nav']}; color: {c['tenue']}; border-top: 1px solid {c['bordo']}; }}
QStatusBar QLabel {{ color: {c['tenue']}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1.5px solid {c['bordo2']}; border-radius: 4px; background: {c['pannello2']}; }}
QCheckBox::indicator:hover {{ border-color: {c['accento']}; }}
QCheckBox::indicator:checked {{ background: {c['accento']}; border-color: {c['accento']}; }}
QCheckBox::indicator:disabled {{ border-color: {c['bordo']}; background: transparent; }}
QToolTip {{ background: {c['pannello2']}; color: {c['testo']}; border: 1px solid {c['bordo2']}; padding: 6px; }}
QMenu {{ background: {c['pannello2']}; color: {c['testo']}; border: 1px solid {c['bordo2']}; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {c['accento_bg']}; color: {c['accento']}; }}
QFrame[ruolo="scheda"] {{ background: {c['pannello']}; border: 1px solid {c['bordo']}; border-radius: 12px; }}
"""


def applica(app, nome="scuro"):
    n = risolvi(nome)
    _attuale["nome"] = n
    c = TEMI[n]
    app.setStyle("Fusion")
    pal = QPalette()
    for ruolo, chiave in ((QPalette.Window, "bg"), (QPalette.Base, "pannello"), (QPalette.AlternateBase, "pannello2"),
                          (QPalette.Button, "pannello2"), (QPalette.Text, "testo"), (QPalette.WindowText, "testo"),
                          (QPalette.ButtonText, "testo"), (QPalette.ToolTipBase, "pannello2"),
                          (QPalette.ToolTipText, "testo"), (QPalette.PlaceholderText, "debole"),
                          (QPalette.Highlight, "accento"), (QPalette.HighlightedText, "su_accento"),
                          (QPalette.Link, "accento")):
        pal.setColor(ruolo, QColor(c[chiave]))
    app.setPalette(pal)
    app.setStyleSheet(qss(c))
    return n


# ---------------------------------------------------------------- icone (SVG a tratto, colorate al volo)
ICONE = {
    "bozza": '<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16z"/><path d="M13.5 6.5l4 4M4 20l2-2"/>',
    "kb": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3H6.5"/><path d="M9 8l2 2 4-4"/>',
    "storico": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "pianifica": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/><circle cx="12" cy="15" r="2.5"/>',
    "blog": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.7 2.5 14.3 0 17M12 3.5c-2.5 2.7-2.5 14.3 0 17"/>',
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "assistente": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    "documenti": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "verbale": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
    "dettatura": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
    "traduzione": '<path d="M4 5h8M8 3v2M6 5c0 4 3 7 6 8M10 5c0 3-2 6-6 8"/><path d="M13 21l4-9 4 9M14.5 18h5"/>',
    "audio": '<path d="M3 12h2M7 8v8M11 4v16M15 8v8M19 11v2"/>',
    "posta": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5l8.5 6.5 8.5-6.5"/>',
    "agenda": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4M8 14h3M8 17h6"/>',
    "persone": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6 6 0 0 1 3.5 6"/>',
    "impostazioni": '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
}


def icona(nome, colore, lato=22):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{colore}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONE[nome]}</svg>')
    r = QSvgRenderer(QByteArray(svg.encode()))
    pm = QPixmap(lato * 2, lato * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    r.render(p, QRectF(0, 0, lato * 2, lato * 2))
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


def icona_stato(nome):
    """Icona con colore normale e colore 'selezionato' (accento)."""
    c = colori()
    ic = QIcon()
    ic.addPixmap(icona(nome, c["tenue"]), QIcon.Normal, QIcon.Off)
    ic.addPixmap(icona(nome, c["accento"]), QIcon.Normal, QIcon.On)
    ic.addPixmap(icona(nome, c["accento"]), QIcon.Active, QIcon.On)
    return ic


class NavLaterale(QWidget):
    """Menu laterale a icone che comanda un QTabWidget (la barra delle schede resta nascosta)."""
    scelto = Signal(int)

    def __init__(self, voci, parent=None):
        super().__init__(parent)
        self.setObjectName("nav")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(84)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 14, 10, 14)
        lay.setSpacing(4)
        logo = QLabel(P.LETTERA_LOGO)
        logo.setObjectName("logo")
        logo.setFixedSize(42, 42)
        logo.setAlignment(Qt.AlignCenter)
        logo.setToolTip(f"{P.NOME} · {P.SOTTOTITOLO}")
        lay.addWidget(logo, alignment=Qt.AlignHCenter)
        lay.addSpacing(14)
        self.gruppo = QButtonGroup(self)
        self.gruppo.setExclusive(True)
        self.bottoni = []
        for i, (chiave, etichetta, breve) in enumerate(voci):
            if chiave == "impostazioni":
                lay.addStretch(1)
            b = QToolButton()
            b.setProperty("nav", True)
            b.setCheckable(True)
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setIcon(icona_stato(chiave))
            b.setIconSize(QSize(22, 22))
            b.setText(breve)
            b.setToolTip(etichetta)
            b.setAccessibleName(etichetta)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setMinimumHeight(56)
            b.setCursor(Qt.PointingHandCursor)
            self.gruppo.addButton(b, i)
            self.bottoni.append((chiave, b))
            lay.addWidget(b)
        self.gruppo.idClicked.connect(self.scelto.emit)

    def seleziona(self, i):
        b = self.gruppo.button(i)
        if b and not b.isChecked():
            b.setChecked(True)

    def ricolora(self):
        for chiave, b in self.bottoni:
            b.setIcon(icona_stato(chiave))
