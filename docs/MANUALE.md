# Manuale di Orfeo

## 1. Cos'è

Orfeo è l'agente editoriale di argosnewdreams.blog e fa due lavori:

1. **tiene aggiornata la Knowledge Base del blog**: rilegge gli articoli, trova ciò che è superato e ti propone le correzioni, con la prova presa da Microsoft Learn o da un sito istituzionale;
2. **sviluppa le tue bozze** in articoli completi, salvati come bozze.

Scrive con un modello linguistico che gira sul tuo computer tramite Ollama. Usa solo fonti istituzionali e Microsoft ufficiali. Non pubblica mai e non cambia nulla sul blog senza la tua approvazione.

## 2. Installazione

### macOS (Apple Silicon)
1. Tasto destro su `Installa-Mac.command` → *Apri* (se macOS lo blocca: *Impostazioni di Sistema → Privacy e sicurezza → Apri comunque*).
2. L'installer crea l'ambiente in `~/orfeo-blog-env` e l'app `~/Applications/Orfeo.app`. Non servono password di amministratore.
3. La prima volta che Orfeo usa la cartella di lavoro, macOS chiede l'accesso a Documenti: rispondi **Consenti**, altrimenti le esecuzioni automatiche non la vedranno.

### Windows (x64 e ARM)
1. Doppio clic su `Installa-Windows.bat` (se compare SmartScreen: *Ulteriori informazioni → Esegui comunque*).
2. L'installer crea l'ambiente in `%USERPROFILE%\orfeo-blog-env` e i collegamenti su Desktop e menu Start.

### Ollama e modelli
Installa [Ollama](https://ollama.com), poi in *Impostazioni → Nuovo modello* scrivi `gemma3:12b` e premi **Scarica modello** (circa 8 GB). Sceglilo come *Modello per i testi* e premi **Salva impostazioni**.

### Primo collegamento
Nella pagina **Blog**:
1. spunta **Cerca le fonti su Microsoft Learn e leggi i link ammessi** e premi **Prova Microsoft Learn**;
2. spunta **Collega il blog** e scegli il metodo **WordPress.com (consigliato)**. Serve una sola volta registrare Orfeo come applicazione:
   - apri <https://developer.wordpress.com/apps/> → **Create New Application**;
   - *Name* `Orfeo`, *Website URL* l'indirizzo del blog, **Redirect URLs** `http://127.0.0.1:8765/orfeo`, *Type* **Native**; salva;
   - copia **Client ID** e **Client Secret** nei campi della pagina Blog;
3. premi **Collega con WordPress.com**: si apre il browser, approvi l'accesso al blog e torni in Orfeo. Se il browser mostra «pagina non raggiungibile», copia l'indirizzo dalla barra e usa **Incolla indirizzo di ritorno…**;
4. premi **Verifica collegamento** e poi **Salva**.

Il metodo **Password applicazione** (`/wp-json`) resta disponibile per i siti WordPress non ospitati su WordPress.com. Sui siti WordPress.com spesso non funziona: la *modalità difensiva* blocca i programmi e l'autenticazione con password applicazione può essere rifiutata (401).

## 3. Le funzioni

### Knowledge Base
**Controlla ora** esamina il numero di articoli indicato accanto, scegliendo prima quelli mai controllati o cambiati dall'ultimo controllo, poi i meno recenti. Gli articoli con una proposta in attesa non vengono ricontrollati finché non la applichi o la scarti. Per ogni articolo Orfeo:
1. individua fino a 6 affermazioni che invecchiano: prezzi, licenze, nomi di prodotti e funzioni, limiti, ruoli, procedure, stato (anteprima o disponibile), date, norme;
2. cerca le prove su Microsoft Learn (Microsoft Learn MCP Server ufficiale) e rilegge i link dell'articolo che puntano a fonti ammesse;
3. per ogni affermazione decide: ✅ **confermata**, ✏️ **superata**, ❔ **non verificabile**. «Superata» vale solo se la citazione indicata si ritrova parola per parola nella fonte; altrimenti diventa «non verificabile» con il motivo;
4. per le affermazioni superate prepara la **proposta**: riscrive solo il paragrafo, titolo, voce o cella interessati e aggiunge in coda una nota «Aggiornato il… Fonti: …».

A destra vedi, per l'articolo selezionato, **Prima**, **Dopo**, **Perché**, **Fonte** con livello e citazione, e l'esito delle altre affermazioni. Poi:
- **Applica al blog**: Orfeo rilegge l'articolo, rifiuta se è stato modificato dopo il controllo, salva una copia di sicurezza e aggiorna solo il testo;
- **Scarta**: la proposta va in archivio, l'articolo tornerà in coda più avanti;
- **Ripristina versione precedente**: rimette l'articolo com'era prima dell'ultimo «Applica» (facendo a sua volta una copia della versione attuale);
- **Ricontrolla l'articolo selezionato**: un nuovo controllo solo di quell'articolo.

Se il testo originale conteneva un link, la proposta te lo segnala: nella versione nuova va rimesso a mano.

Gli articoli che parlano di prodotti non Microsoft (per esempio Anthropic e Claude) o i system prompt di solito risultano «non verificabili»: le fonti ammesse non ne parlano.

### Scrivi
1. Scrivi la bozza: **Tema** (facoltativo), **Rubrica** (es. «Il Bianco e il Nero») e il testo con idee, punti, episodi vissuti, link. I link servono solo se puntano a fonti ammesse.
2. Puoi **allegare** documenti (`.md`, `.txt`, `.docx`, `.pdf`), link (`.webloc`, `.url`) e immagini PNG, anche trascinandoli.
3. **Sviluppa l'articolo**: Orfeo salva la bozza in `in-arrivo`, cerca su Microsoft Learn la documentazione sui temi tecnici, progetta la struttura e scrive attacco, sezioni, FAQ e conclusioni. **Ferma** interrompe al passo successivo.
4. Risultato: titolo, numero di **[VERIFY]**, categorie e tag proposti, eventuali avvisi. **Copia l'articolo** (Markdown), **Apri in WordPress** (se il blog è collegato, l'articolo è una bozza), **Apri il file**.

Struttura di ogni articolo: TL;DR, sezioni H3 formulate come domande, FAQ in H4, Conclusioni, Riferimenti con il livello della fonte, nota di trasparenza (art. 50 AI Act). Le immagini PNG non vengono caricate: Orfeo inserisce un segnaposto `[VERIFY: immagine …]` con una didascalia proposta.

### Storico
Ogni esecuzione: data, tipo (Articolo o Knowledge Base), titolo, esito, [VERIFY], avvio (manuale o pianificato). Doppio clic apre la bozza, l'articolo o il registro.

### Pianifica
Scegli giorno e ora e premi **Salva la pianificazione**. A quell'ora Orfeo **controlla la Knowledge Base** e ti manda una notifica: quante proposte ci sono da approvare e la richiesta della **bozza del prossimo articolo**. Non scrive articoli da solo. **Prova adesso in background** avvia Orfeo come farà il sistema.
- **macOS**: launchd; se il Mac dorme parte al risveglio, se è spento quella settimana salta. Per svegliarlo qualche minuto prima: `sudo pmset repeat wakeorpoweron M 07:35:00`.
- **Windows**: Utilità di pianificazione; il PC deve essere acceso con la sessione aperta. L'esito è nello Storico.

### Blog
- **Cartella di lavoro** (di serie `~/Documents/Orfeo`): `in-arrivo`, `bozze`, `elaborati`, `config`. In `config/prompt-editoriale-v2-compact.md` va il tuo stile editoriale: prevale sullo stile di base, mai sulle regole di sicurezza.
- **Scrittura**: lunghezza in parole, contesto in token, creatività.
- **Fonti online** (spente di default): Microsoft Learn e link ammessi; numero di articoli della Knowledge Base per esecuzione.
- **WordPress** (spento di default): sito e metodo. *WordPress.com*: Client ID, Client Secret (nel portachiavi), indirizzo di ritorno, **Collega con WordPress.com**. *Password applicazione*: utente e password.

## 4. Le fonti ammesse
| Livello | Fonti |
| --- | --- |
| 1 · Ente pubblico | EUR-Lex e `*.europa.eu`, `*.gov.it`, Gazzetta Ufficiale, Normattiva, Garante privacy, Senato, Camera, Banca d'Italia, Consob, Istat, siti `.gov` |
| 2 · Microsoft Learn | `learn.microsoft.com` (tramite il Microsoft Learn MCP Server) |
| 3 · Microsoft ufficiale | altre pagine `microsoft.com`, `azure.com`, `office.com` |

Qualsiasi altro sito viene ignorato e segnalato, sia nelle bozze sia negli articoli della Knowledge Base.

## 5. Impostazioni
Tema (scuro, chiaro, sistema), indirizzo di Ollama e modello per i testi, download di nuovi modelli, controllo degli aggiornamenti.

## 6. Dove stanno i dati
| Cosa | Dove |
| --- | --- |
| Bozze, allegati, articoli, stile | cartella di lavoro (di serie `~/Documents/Orfeo`) |
| Impostazioni, storico, registri | `~/orfeo-blog-env/dati/` |
| Stato dei controlli della Knowledge Base | `~/orfeo-blog-env/dati/kb/stato.json` |
| Proposte in attesa / applicate o scartate | `~/orfeo-blog-env/dati/kb/proposte/` · `dati/kb/archivio/` |
| Copie di sicurezza degli articoli | `~/orfeo-blog-env/dati/kb/backup/` |
| Password applicazione WordPress | Portachiavi (macOS) o Gestore credenziali (Windows), voce «Orfeo-WordPress» |
| Pianificazione | `~/Library/LaunchAgents/blog.argosnewdreams.orfeoblog.plist` (macOS) o attività «Orfeo - bozza settimanale» (Windows) |

## 7. Aggiornamenti
All'avvio Orfeo legge da GitHub solo il numero di versione. Se ce n'è una nuova propone **Aggiorna ora**: sostituisce i file del programma (una copia resta in `app_precedente/`) e si riavvia. Dati, cartella di lavoro e pianificazione restano.

## 8. Disinstallazione
1. In *Pianifica* togli la spunta e premi **Salva la pianificazione**.
2. Cancella `~/Applications/Orfeo.app` (Mac) o i collegamenti (Windows), poi la cartella `~/orfeo-blog-env`.
3. La cartella di lavoro e la voce nel portachiavi restano: cancellale a mano se non ti servono più.

## 9. Risoluzione dei problemi
- **«Ollama non risponde»**: apri l'app Ollama e riprova; controlla l'indirizzo in Impostazioni.
- **«Il modello … non è installato»**: scaricalo da *Impostazioni → Nuovo modello* e sceglilo.
- **«Microsoft Learn non raggiungibile»**: controlla la connessione; con **Prova Microsoft Learn** (pagina Blog) verifichi il collegamento.
- **«… non offre più lo strumento microsoft_docs_search»**: Microsoft ha cambiato il server MCP; serve un aggiornamento di Orfeo.
- **«L'articolo è stato modificato dopo il controllo»**: qualcuno l'ha cambiato in WordPress; **Scarta** la proposta e usa **Ricontrolla l'articolo selezionato**.
- **WordPress risponde 401 o 403** con il metodo password applicazione: sui siti WordPress.com passa al metodo **WordPress.com**.
- **«Collega con WordPress.com»** con errore *redirect_uri*: l'indirizzo di ritorno registrato su developer.wordpress.com deve essere identico a quello nella pagina Blog.
- **Token scaduto o revocato**: premi di nuovo **Collega con WordPress.com**.
- **«Nessun articolo (nessuna-bozza)»**: scrivi la bozza nella pagina Scrivi.
- **La pianificazione non parte (Mac)**: in *Impostazioni di Sistema → Privacy e sicurezza → File e cartelle* controlla che Orfeo possa accedere a Documenti; guarda `~/orfeo-blog-env/dati/log/launchd.log`.
- **Tanti «non verificabile»**: è normale per gli articoli su prodotti non Microsoft o con molte opinioni; il modello da 12B è prudente per costruzione.

## 10. Privacy
Il modello è locale: bozze e articoli non vanno a servizi di AI. Escono in rete solo gli accessi che attivi in *Blog* (ricerche e pagine delle fonti ammesse, WordPress) e il controllo degli aggiornamenti su GitHub. Il bollino in basso dice sempre quali sono attivi.
