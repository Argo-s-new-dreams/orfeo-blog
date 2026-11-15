"""learn_mcp.py - ricerca su Microsoft Learn tramite il Microsoft Learn MCP Server ufficiale.

Endpoint pubblico, senza autenticazione: https://learn.microsoft.com/api/mcp (streamable HTTP).
La documentazione Microsoft chiede di usarlo con un client MCP (non come API REST) e di leggere l'elenco
degli strumenti a ogni connessione, perché nomi e formati possono cambiare: qui usiamo l'SDK MCP ufficiale
e controlliamo che gli strumenti attesi esistano prima di chiamarli.
"""
import json
import os
import re

import anyio

import fonti as F

URL_LEARN = os.environ.get("ORFEO_LEARN_MCP", "https://learn.microsoft.com/api/mcp")
CERCA, LEGGI = "microsoft_docs_search", "microsoft_docs_fetch"


class ErroreLearn(RuntimeError):
    pass


async def _chiama(strumento, argomenti, timeout=60):
    import mcp
    async with mcp.Client(URL_LEARN, read_timeout_seconds=timeout) as c:
        disponibili = {t.name for t in (await c.list_tools()).tools}
        if strumento not in disponibili:
            raise ErroreLearn(f"Il server di Microsoft Learn non offre più lo strumento {strumento} "
                              f"(disponibili: {', '.join(sorted(disponibili))}). Serve un aggiornamento di Orfeo.")
        ris = await c.call_tool(strumento, argomenti)
        testo = "\n".join(getattr(p, "text", "") for p in ris.content if getattr(p, "type", "") == "text")
        if getattr(ris, "isError", False) or getattr(ris, "is_error", False):
            raise ErroreLearn(f"Microsoft Learn ha risposto con un errore: {testo[:200]}")
        return testo


def _esegui(strumento, argomenti):
    try:
        return anyio.run(_chiama, strumento, argomenti)
    except ErroreLearn:
        raise
    except Exception as e:
        raise ErroreLearn(f"Microsoft Learn non raggiungibile ({e.__class__.__name__}: {e}). "
                          "Controlla la connessione a Internet.") from None


def cerca(domanda, quanti=3):
    """Ritorna una lista di Fonte (Livello 2, Microsoft Learn) con l'estratto restituito dalla ricerca."""
    testo = _esegui(CERCA, {"query": domanda})
    try:
        risultati = json.loads(testo).get("results", [])
    except (json.JSONDecodeError, AttributeError):
        risultati = []
    out, visti = [], set()
    for r in risultati:
        url = F.normalizza_url(r.get("contentUrl") or r.get("url") or "")
        if not url or url in visti or not F.ammessa(url):
            continue
        visti.add(url)
        out.append(F.Fonte(titolo=(r.get("title") or url)[:200], url=url, editore="Microsoft Learn",
                           estratto=(r.get("content") or "")[:4000], livello=F.livello(url), origine="learn"))
        if len(out) >= quanti:
            break
    if not out and not risultati:  # formato cambiato: tengo almeno i link a Learn presenti nel testo
        for url in dict.fromkeys(re.findall(r"https://learn\.microsoft\.com/[^\s)\"']+", testo)):
            out.append(F.Fonte(titolo=url, url=url, editore="Microsoft Learn", livello=2, origine="learn"))
            if len(out) >= quanti:
                break
    return out


def leggi(url, max_car=12000):
    """Testo completo (markdown) di una pagina Microsoft Learn."""
    if not F.ammessa(url):
        raise ErroreLearn(f"Fonte non ammessa: {url}")
    return _esegui(LEGGI, {"url": url})[:max_car]
