# Standard delle app AI locali (famiglia Argo)

Questo repository segue lo standard nato con **Argo · Cassetta degli attrezzi AI**. Ogni app della famiglia ha la stessa struttura, lo stesso aspetto, gli stessi installer e lo stesso sistema di aggiornamento. Chi lavora sul codice (persona o AI) deve rispettare le regole qui sotto.

## 1. Principi

- **Tutto in locale.** Dati, audio e documenti non lasciano il computer. Internet serve solo per installare, scaricare i modelli e controllare gli aggiornamenti su GitHub. Ogni eccezione (es. Microsoft 365) è **facoltativa**, spenta per impostazione predefinita e dichiarata nell'interfaccia e nel README.
- **Per utenti non tecnici.** Installazione con doppio clic, messaggi in italiano semplice, nessun terminale da usare dopo l'installazione.
- **I dati dell'utente sono sacri.** Stanno in `~/<slug>-env/dati/`, mai nella cartella del programma: aggiornamenti e reinstallazioni non li toccano.
- **Codice leggibile.** Python, nomi in italiano, commenti che spiegano il *perché*. Licenza MIT, repository pubblico nell'organizzazione GitHub `Argo-s-new-dreams`.

## 2. Struttura (non cambiarla)

| Percorso | Ruolo | Si modifica? |
| --- | --- | --- |
| `app/progetto.py` | Identità dell'app: nome, slug, versione, repo, permessi | **Sì, è il primo file da compilare** |
| `app/main.py` | Finestra, menu laterale, Impostazioni, aggiornamenti | Solo l'elenco `PAGINE` |
| `app/pagina_*.py` | Una pagina per funzione (vedi `pagina_assistente.py`) | Sì: qui sta la logica dell'app |
| `app/pagine.py` | Base comune delle pagine | No |
| `app/tema.py` | Tema «Studio» scuro/chiaro, icone, menu laterale | Solo per aggiungere icone in `ICONE` |
| `app/aggiornamenti.py` | Controllo e installazione aggiornamenti da GitHub | No |
| `app/llm_locale.py` | Client Ollama: chat in streaming, embedding, download modelli | No (estendilo solo se serve) |
| `app/lavoro.py` | Thread per le operazioni lunghe | No |
| `app/dati.py` | Impostazioni dell'utente (scrittura atomica) | No |
| `app/requisiti.txt` | Librerie Python, una per riga | Sì |
| `app/icon.*` | Icone PNG, ICO e iconset macOS | Rigenera con `strumenti/crea_icone.py` |
| `app/esempi/` | File **fittizi** per provare subito l'app | Sì |
| `Installa-Mac.command`, `Installa-Windows.bat`, `installer/` | Installer standard | No |
| `strumenti/` | Versione, icone, verifica pre-pubblicazione | No |
| `docs/MANUALE.md`, `docs/screenshot-*.png` | Manuale e immagini | Sì |

## 3. Interfaccia (UX «Studio»)

- Menu laterale a icone a sinistra (84 px), logo con la lettera dell'app in alto, **Impostazioni sempre in fondo**.
- Tema scuro predefinito, chiaro e «sistema» selezionabili. Colori e stili **solo** da `tema.py`: niente `setStyleSheet` con colori fissi nelle pagine.
- Ogni pagina: titolo, una riga di spiegazione (`sottotitolo`), un solo pulsante **primario** (`setProperty("primario", True)`), pulsante **Ferma** per tutto ciò che dura più di qualche secondo, risultato copiabile o esportabile.
- Operazioni lunghe **sempre** in `Lavoro` (mai bloccare l'interfaccia); avanzamento nella barra di stato.
- Barra di stato con il bollino **🔒 100% locale** quando il modello punta a `localhost`; avviso visibile se punta altrove.
- Errori: messaggio in italiano che dice cosa fare (es. «Ollama non raggiungibile: è avviato?»), mai solo il traceback.
- Testi in italiano, tono semplice. Icone: SVG a tratto nel codice, ma i file icona dell'app sono sempre PNG/ICO/ICNS.

## 4. Versioni e aggiornamenti

- Formato versione: `AAAAMMGG.HHMM`, ora di Roma, in `app/progetto.py` → `VERSIONE`.
- **A ogni modifica pubblicata**: `python strumenti/nuova_versione.py "Titolo" "punto 1" "punto 2"`. Aggiorna la versione e apre la voce `## AAAAMMGG.HHMM: Titolo` in cima al `CHANGELOG.md`, che l'app mostra all'utente come «novità».
- L'app legge `app/progetto.py` e `CHANGELOG.md` dal ramo `main` su GitHub; se la versione è più alta propone **Aggiorna ora**: scarica lo zip, salva una copia in `app_precedente/`, sostituisce `app/`, reinstalla le librerie con `uv` solo se `requisiti.txt` è cambiato, poi si riavvia (su Mac con `open -n` sul bundle).
- Conseguenza: **ciò che va su `main` arriva agli utenti**. Prova prima in locale; per esperimenti usa un altro ramo.
- Se una correzione riguarda il codice di aggiornamento stesso, scrivilo nel CHANGELOG: vale dall'aggiornamento successivo.

## 5. Installer

- **macOS** (Apple Silicon, M1 o successivi): `Installa-Mac.command` → uv (Homebrew se c'è, altrimenti installer ufficiale), Python 3.12 in `~/<slug>-env`, librerie, copia di `app/`, bundle `~/Applications/<Nome>.app` con `Info.plist` (permesso microfono solo se `USO_MICROFONO` è compilato), icona da iconset.
- **Windows** (x64 e ARM): `Installa-Windows.bat` toglie il blocco «scaricato da Internet» e lancia `installer/installa_windows.ps1` → uv via winget, ambiente Python (x64 anche su ARM se `PYTHON_WINDOWS = "x64"`), collegamenti su Desktop e menu Start con `pythonw.exe`.
- Niente diritti di amministratore. Reinstallare è sicuro: l'ambiente viene riutilizzato e `dati/` resta.
- Installer non firmati: README e manuale spiegano come superare SmartScreen e Gatekeeper.
- Dipendenze esterne di sistema (es. FFmpeg, Ollama) vanno controllate dall'installer con un messaggio chiaro, o prese da pacchetti Python (es. `imageio-ffmpeg`) per evitare Homebrew obbligatorio.

## 6. Modelli AI

- Testo: Ollama su `http://localhost:11434`, modello scelto dall'utente in Impostazioni (consiglio per Mac da 16 GB: `gemma3:12b`; embedding: `bge-m3`).
- Altri motori (Whisper, pyannote, OCR…) girano nell'ambiente Python e scaricano i modelli al primo uso, con stato visibile.
- Token o chiavi (es. Hugging Face) in `dati/`, mai nel repository; `.gitignore` li esclude.

## 7. Documentazione obbligatoria

- `README.md`: cosa fa (tabella funzioni + motore locale), screenshot, requisiti per sistema, installazione in 4 passi, privacy e dati, **AI Act** quando pertinente (con riferimenti agli articoli e nota «non è consulenza legale»), struttura, stato del progetto, licenza, riassunto in inglese.
- `docs/MANUALE.md`: installazione, ogni funzione, impostazioni, dove stanno i dati, aggiornamenti, disinstallazione, risoluzione problemi.
- `THIRD_PARTY_LICENSES.md`: licenze di librerie e modelli usati.
- `app/esempi/`: solo dati inventati, nessun dato reale di clienti o persone.

## 8. Pubblicazione (ogni volta)

1. `python strumenti/verifica.py` deve dire ✅.
2. Commit con messaggio chiaro, push su `main` del repository GitHub.
3. Copia della stessa versione nella cartella SharePoint AIFirst **Local AI** (sincronizzata via OneDrive sul Mac): GitHub e SharePoint devono restare allineati.
4. Se la novità è rilevante: screenshot aggiornati in `docs/` e, se serve, bozza di articolo per argosnewdreams.blog.

## 9. Da non fare

- Inviare dati dell'utente in rete senza un'impostazione esplicita e visibile.
- Salvare dati dell'utente dentro `app/` (verrebbero cancellati dall'aggiornamento).
- Cambiare struttura, nomi dei file standard, formato della versione o tema per una singola app.
- Aggiungere funzioni vietate dall'AI Act (art. 5), come il riconoscimento delle emozioni sul luogo di lavoro.
