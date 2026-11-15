"""progetto.py - carta d'identità dell'app. È l'UNICO file da personalizzare per una nuova app.

Installer, aggiornamenti, finestra e bundle macOS leggono tutto da qui.
Regola: VERSIONE ha il formato AAAAMMGG.HHMM (ora di Roma) e va aggiornata a ogni modifica
con `python strumenti/nuova_versione.py "titolo della novità"`, che aggiorna anche il CHANGELOG.
"""
import os
from pathlib import Path

VERSIONE = "20261115.1554"

# --- identità -------------------------------------------------------------------------------
NOME = "Orfeo"                           # nome mostrato (finestra, menu Start, ~/Applications)
SOTTOTITOLO = "L'agente editoriale di argosnewdreams.blog"
SLUG = "orfeo-blog"                      # minuscole e trattini: cartella dati, repo, file
LETTERA_LOGO = "O"                       # lettera nel logo del menu laterale
BUNDLE_ID = f"blog.argosnewdreams.{SLUG.replace('-', '')}"
AUTORE = "Luca Borio"

# --- GitHub (aggiornamenti dall'app) -------------------------------------------------------
REPO = f"Argo-s-new-dreams/{SLUG}"
RAMO = "main"

# --- dove stanno le cose sul computer dell'utente -------------------------------------------
# <CASA>/app       -> file del programma (sostituiti dagli aggiornamenti)
# <CASA>/dati      -> impostazioni e dati dell'utente (MAI toccati dagli aggiornamenti)
# <CASA>/bin|Scripts -> ambiente Python creato da uv
CASA = Path(os.environ.get(f"{SLUG.upper().replace('-', '_')}_HOME", Path.home() / f"{SLUG}-env"))
DATI = CASA / "dati"
IMPOSTAZIONI = DATI / "impostazioni.json"

# --- permessi macOS (testo mostrato all'utente; lascia vuoto se non serve) ------------------
USO_MICROFONO = ""  # es. "Usa il microfono solo per la dettatura, elaborata su questo Mac."

# --- impostazioni predefinite ---------------------------------------------------------------
IMPOSTAZIONI_BASE = {
    "tema": "scuro",                     # scuro | chiaro | sistema
    "ollama_url": "http://localhost:11434",
    "controlla_aggiornamenti": True,     # all'avvio legge da GitHub solo il numero di versione
    "modello_chat": "gemma3:12b",
    # --- Orfeo: scrittura ---
    "cartella": str(Path.home() / "Documents" / "Orfeo"),  # in-arrivo, bozze, elaborati, config
    "contesto": 16384,                   # token di contesto chiesti a Ollama (num_ctx)
    "temperatura": 0.5,
    "parole": 1400,
    # --- Orfeo: rete (facoltativa, SPENTA di default come da standard) ---
    # Fonti ammesse SOLO: enti pubblici, Microsoft Learn (server MCP ufficiale), pagine ufficiali Microsoft.
    "fonti_online": False,               # ricerca su Microsoft Learn e lettura dei link ammessi
    "kb_per_esecuzione": 5,              # articoli della Knowledge Base controllati a ogni esecuzione
    "wordpress_attivo": False,           # legge post e KB, crea bozze; modifica la KB solo con «Applica»
    "wp_sito": "https://argosnewdreams.blog",
    "wp_metodo": "wpcom",                # «wpcom»: API di WordPress.com con OAuth (consigliato) · «password»: /wp-json
    "wpcom_client_id": "",               # app registrata su developer.wordpress.com/apps (il secret sta nel portachiavi)
    "wpcom_redirect": "http://127.0.0.1:8765/orfeo",
    "wpcom_blog_id": "",                 # restituito da WordPress.com al momento dell'autorizzazione
    "wp_utente": "",                     # solo metodo «password»: la password applicazione sta nel portachiavi
    "pianificazione": {"attiva": False, "giorno": 1, "ora": 7, "minuto": 40},  # giorno: 0 = domenica
}

# --- Windows su ARM (es. Snapdragon) --------------------------------------------------------
# "x64": Python x64 in emulazione (collaudato con Argo: funziona anche con librerie senza versione ARM64).
# "nativo": Python ARM64, più veloce, solo se TUTTE le librerie di requisiti.txt esistono per win_arm64.
PYTHON_WINDOWS = "x64"
