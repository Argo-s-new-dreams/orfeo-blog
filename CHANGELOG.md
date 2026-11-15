# Novità di Orfeo

Le versioni hanno il formato `AAAAMMGG.HHMM` (ora di Roma). Il manuale completo è in [docs/MANUALE.md](docs/MANUALE.md).

## 20261115.1542: Collegamento a WordPress.com con OAuth
- Nuovo metodo consigliato «WordPress.com»: Orfeo usa l'API ufficiale public-api.wordpress.com e non viene più bloccato dalla modalità difensiva del sito
- Registrazione una tantum su developer.wordpress.com/apps, poi «Collega con WordPress.com» dal browser; token e segreto solo nel portachiavi
- La password applicazione resta disponibile per i siti WordPress non ospitati su WordPress.com

## 20261115.1515: WordPress: modalità difensiva riconosciuta
- Se WordPress.com mostra la verifica anti-bot «Checking your browser…», Orfeo lo dice chiaramente e spiega come disattivarla, invece di dare la colpa alle credenziali
- Il nome utente WordPress viene ripulito dalla «@» iniziale; la password già salvata resta valida

## 20261115.1457: Knowledge Base e bozze dell'utente
- Nuova pagina Knowledge Base: Orfeo rilegge gli articoli, trova le affermazioni superate e propone le correzioni con fonte e citazione verificata; Applica, Scarta e Ripristina, con copia di sicurezza
- Nuova pagina Scrivi: Orfeo sviluppa la tua bozza in un articolo, cercando le fonti su Microsoft Learn (Microsoft Learn MCP Server ufficiale)
- Fonti ammesse solo istituzionali e Microsoft ufficiali, controllate dal codice; rimossi feed e temi scelti in automatico
- La pianificazione settimanale controlla la Knowledge Base e ti chiede la bozza del prossimo articolo

## 20261115.1434: Repository orfeo-blog
- Lo slug diventa orfeo-blog: ambiente in ~/orfeo-blog-env e aggiornamenti da Argo-s-new-dreams/orfeo-blog
- Messaggio più chiaro quando «In arrivo» è vuota e i feed sono spenti

## 20261115.1431: Prima versione di Orfeo
- Bozze settimanali dagli appunti di «In arrivo» o, se attivate, dalle novità dei feed ufficiali
- Scrittura a tappe con il modello locale (consigliato gemma3:12b) e struttura TL;DR, domande H3, FAQ H4, Conclusioni, Riferimenti
- Link inventati rimossi dal codice e marcati [VERIFY]; Riferimenti composti solo con pagine scaricate davvero
- WordPress facoltativo e solo bozze, con password applicazione nel portachiavi
- Pianificazione settimanale con launchd (macOS) e Utilità di pianificazione (Windows)

