# Manuale di Orfeo

## 1. Cos'è

Orfeo è l'agente editoriale di argosnewdreams.blog: una volta alla settimana (o quando vuoi tu) trasforma i tuoi appunti, oppure le novità della settimana, in una **bozza** di articolo. Scrive con un modello linguistico che gira sul tuo computer tramite Ollama. Non pubblica mai: l'ultima parola è tua.

## 2. Installazione

### macOS (Apple Silicon)
1. Tasto destro su `Installa-Mac.command` → *Apri* (se macOS lo blocca: *Impostazioni di Sistema → Privacy e sicurezza → Apri comunque*).
2. L'installer crea l'ambiente in `~/orfeo-blog-env` e l'app `~/Applications/Orfeo.app`. Non servono password di amministratore.
3. Alla prima bozza macOS chiede se Orfeo può accedere alla cartella Documenti: rispondi **Consenti**, altrimenti le esecuzioni automatiche non vedranno la cartella.

### Windows (x64 e ARM)
1. Doppio clic su `Installa-Windows.bat` (se compare SmartScreen: *Ulteriori informazioni → Esegui comunque*).
2. L'installer crea l'ambiente in `%USERPROFILE%\orfeo-blog-env` e i collegamenti su Desktop e menu Start.

### Ollama e modelli
Installa [Ollama](https://ollama.com), poi in *Impostazioni → Nuovo modello* scrivi `gemma3:12b` e premi **Scarica modello** (circa 8 GB). Sceglilo come *Modello per i testi* e premi **Salva impostazioni**.

## 3. Le funzioni

### Bozza
Il riquadro in alto riassume lo stato: modello, file in arrivo, stile, accessi in rete, pianificazione. **Prepara la bozza ora** avvia il lavoro; **Ferma** lo interrompe al passo successivo. Orfeo:
1. legge *In arrivo*; se è vuota e hai attivato i feed, sceglie un tema dalle novità della settimana e spiega perché (il motivo e le alternative scartate sono nell'intestazione del file);
2. progetta la struttura (titolo, TL;DR, 3-6 sezioni, 3-5 FAQ, categorie e tag proposti);
3. scrive l'attacco, ogni sezione, le FAQ e le conclusioni;
4. compone i Riferimenti con le sole pagine scaricate, ognuna con il suo livello;
5. salva la bozza in `bozze/` (`.md` leggibile e `.html` a blocchi Gutenberg) e, se attivo, la crea su WordPress **come bozza**;
6. sposta gli input usati in `elaborati/AAAA-MM-GG/` (casella *Sposta gli input usati*).

Alla fine trovi titolo, numero di **[VERIFY]**, categorie e tag proposti ed eventuali avvisi. **Copia la bozza** mette il Markdown negli appunti; **Apri in WordPress** apre l'editor del post.

### In arrivo
- **Nuovo appunto**: tema, rubrica e testo; diventa un file `.md`.
- **Aggiungi link**: uno per riga; Orfeo li legge solo se in *Blog* è attivo «Leggi le pagine dei link».
- **Aggiungi file…** o trascinamento: `.md`, `.txt`, `.docx`, `.pdf`, `.webloc`, `.url`, `.png`. Gli altri formati restano in cartella e vengono segnalati.
- Le immagini PNG non vengono caricate sul blog: Orfeo inserisce un segnaposto `[VERIFY: immagine …]` con una didascalia proposta.
- Per una rubrica scrivi in un appunto la riga `rubrica: Il Bianco e il Nero`.

### Storico
Ogni esecuzione con data, titolo, esito, [VERIFY] e tipo di avvio (manuale o pianificata). Doppio clic per aprire la bozza; **Apri il registro** mostra tutti i passi di quell'esecuzione.

### Pianifica
Scegli giorno e ora e premi **Salva la pianificazione**. **Prova adesso in background** avvia Orfeo esattamente come farà il sistema all'ora stabilita.
- **macOS**: launchd apre Orfeo in background; se il Mac dorme parte al risveglio, se è spento quella settimana salta. Per svegliarlo qualche minuto prima: `sudo pmset repeat wakeorpoweron M 07:35:00`. A fine lavoro arriva una notifica.
- **Windows**: un'attività dell'Utilità di pianificazione; il PC deve essere acceso con la sessione aperta. L'esito è nello Storico.

### Blog
- **Cartella di lavoro** (di serie `~/Documents/Orfeo`): `in-arrivo`, `bozze`, `elaborati`, `config`. In `config/prompt-editoriale-v2-compact.md` va il tuo stile editoriale: prevale sullo stile di base, mai sulle regole di sicurezza (niente fatti inventati, niente link).
- **Scrittura**: lunghezza in parole, contesto in token, creatività.
- **Rete (facoltativa, spenta di default)**: lettura dei link, novità dai feed (formato `nome | url | livello`, le righe con `#` sono disattivate, **Prova i feed** li controlla), WordPress.
- **WordPress**: sito, utente e *password applicazione* (wp-admin → Utenti → Profilo → Password applicazione). **Verifica collegamento** la prova; la password resta nel portachiavi del sistema.

## 4. Impostazioni
Tema (scuro, chiaro, sistema), indirizzo di Ollama e modello per i testi, download di nuovi modelli, controllo degli aggiornamenti.

## 5. Dove stanno i dati
| Cosa | Dove |
| --- | --- |
| Appunti, bozze, input elaborati, stile | cartella di lavoro (di serie `~/Documents/Orfeo`) |
| Impostazioni, storico, registri | `~/orfeo-blog-env/dati/` |
| Password applicazione WordPress | Portachiavi (macOS) o Gestore credenziali (Windows), voce «Orfeo-WordPress» |
| Pianificazione | `~/Library/LaunchAgents/blog.argosnewdreams.orfeoblog.plist` (macOS) o attività «Orfeo - bozza settimanale» (Windows) |

## 6. Aggiornamenti
All'avvio Orfeo legge da GitHub solo il numero di versione. Se ce n'è una nuova propone **Aggiorna ora**: sostituisce i file del programma (una copia resta in `app_precedente/`) e si riavvia. Dati, cartella di lavoro e pianificazione restano.

## 7. Disinstallazione
1. In *Pianifica* togli la spunta e premi **Salva la pianificazione**.
2. Cancella `~/Applications/Orfeo.app` (Mac) o i collegamenti (Windows), poi la cartella `~/orfeo-blog-env`.
3. La cartella di lavoro e la voce nel portachiavi restano: cancellale a mano se non ti servono più.

## 8. Risoluzione dei problemi
- **«Ollama non risponde»**: apri l'app Ollama e riprova; controlla l'indirizzo in Impostazioni.
- **«Il modello … non è installato»**: scaricalo da *Impostazioni → Nuovo modello* e sceglilo.
- **«Nessuna bozza (nessun-tema)»**: *In arrivo* è vuota e i feed sono spenti; aggiungi un appunto o attiva i feed in *Blog*.
- **WordPress risponde 401 o 403**: controlla utente e password applicazione (non la password di accesso) con **Verifica collegamento**.
- **La pianificazione non parte (Mac)**: in *Impostazioni di Sistema → Privacy e sicurezza → File e cartelle* controlla che Orfeo possa accedere a Documenti; guarda `~/orfeo-blog-env/dati/log/launchd.log`.
- **Tanti [VERIFY]**: è normale con un modello da 12B; gli appunti più ricchi e i link a fonti ufficiali li riducono.

## 9. Privacy
Il modello è locale: appunti e bozze non vanno a servizi di AI. Escono in rete solo gli accessi che attivi in *Blog* (pagine dei link, feed, WordPress) e il controllo degli aggiornamenti su GitHub. Il bollino in basso dice sempre quali sono attivi.
