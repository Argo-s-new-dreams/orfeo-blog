"""llm_locale.py - accesso a un modello linguistico locale tramite Ollama (http://localhost:11434).

Nessuna dipendenza esterna: solo libreria standard + numpy. Tutto il traffico resta su questo computer.
"""
import json
import re
import urllib.error
import urllib.request

import numpy as np

DEFAULT_URL = "http://localhost:11434"


class ErroreLLM(RuntimeError):
    pass


def _req(url, path, payload=None, timeout=600):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url.rstrip("/") + path, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST" if data is not None else "GET")
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")[:300]
        raise ErroreLLM(f"Ollama ha risposto {e.code}: {corpo}") from None
    except Exception as e:
        raise ErroreLLM(f"Ollama non raggiungibile su {url}: {e}. È avviato?") from None


def e_locale(url):
    return bool(re.match(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?/?$", url.strip()))


def elenco_modelli(url=DEFAULT_URL):
    """Ritorna (modelli_chat, modelli_embedding) installati in Ollama."""
    with _req(url, "/api/tags", timeout=10) as r:
        dati = json.load(r)
    nomi = sorted(m.get("name", "") for m in dati.get("models", []))
    emb = [n for n in nomi if "embed" in n.lower() or n.lower().startswith(("bge", "e5", "gte"))]
    chat = [n for n in nomi if n not in emb]
    return chat, emb


def chat(messaggi, modello, url=DEFAULT_URL, temperatura=0.3, on_token=None, stop=None, contesto=None, formato=None):
    """Chat in streaming. on_token(testo) riceve i pezzi; stop() -> True interrompe. Ritorna il testo completo."""
    opzioni = {"temperature": temperatura}
    if contesto:
        opzioni["num_ctx"] = contesto
    payload = {"model": modello, "messages": messaggi, "stream": True, "options": opzioni}
    if formato:  # es. "json": Ollama vincola la risposta a un JSON valido (aggiunta di Orfeo)
        payload["format"] = formato
    out = []
    with _req(url, "/api/chat", payload) as r:
        for riga in r:
            if stop and stop():
                break
            riga = riga.strip()
            if not riga:
                continue
            pezzo = json.loads(riga)
            if pezzo.get("error"):
                raise ErroreLLM(pezzo["error"])
            t = pezzo.get("message", {}).get("content", "")
            if t:
                out.append(t)
                if on_token:
                    on_token(t)
            if pezzo.get("done"):
                break
    testo = "".join(out)
    # alcuni modelli "ragionano" tra <think>...</think>: non serve mostrarlo nel risultato finale
    return re.sub(r"<think>.*?</think>\s*", "", testo, flags=re.S).strip()


def embed(testi, modello, url=DEFAULT_URL):
    """Vettori normalizzati per una lista di testi."""
    vettori = []
    for i in range(0, len(testi), 16):
        with _req(url, "/api/embed", {"model": modello, "input": testi[i:i + 16]}) as r:
            dati = json.load(r)
        vettori.extend(dati.get("embeddings", []))
    if len(vettori) != len(testi):
        raise ErroreLLM("Il modello di embedding non ha restituito tutti i vettori.")
    m = np.asarray(vettori, dtype=np.float32)
    return m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-9)


def scarica_modello(nome, url=DEFAULT_URL, on_stato=None, stop=None):
    """Scarica un modello in Ollama (equivalente di `ollama pull`)."""
    with _req(url, "/api/pull", {"model": nome, "stream": True}, timeout=3600) as r:
        for riga in r:
            if stop and stop():
                return False
            riga = riga.strip()
            if not riga:
                continue
            d = json.loads(riga)
            if d.get("error"):
                raise ErroreLLM(d["error"])
            if on_stato:
                tot, fatto = d.get("total"), d.get("completed")
                perc = f" {fatto * 100 // tot}%" if tot and fatto else ""
                on_stato(f"{d.get('status', '')}{perc}")
            if d.get("status") == "success":
                return True
    return True


def spezza(testo, max_car=6000, sovrapposizione=0):
    """Divide un testo in blocchi di circa max_car caratteri, rispettando i paragrafi."""
    paragrafi = [p for p in re.split(r"\n\s*\n", testo) if p.strip()]
    blocchi, cur = [], ""
    for p in paragrafi:
        while len(p) > max_car:  # paragrafo enorme: taglio duro
            if cur:
                blocchi.append(cur)
                cur = ""
            blocchi.append(p[:max_car])
            p = p[max_car - sovrapposizione:]
        if len(cur) + len(p) + 2 > max_car and cur:
            blocchi.append(cur)
            cur = cur[-sovrapposizione:] if sovrapposizione else ""
        cur = (cur + "\n\n" + p) if cur else p
    if cur.strip():
        blocchi.append(cur)
    return blocchi


def piu_simili(vettore_domanda, matrice, k=5):
    if len(matrice) == 0:
        return []
    punteggi = matrice @ vettore_domanda
    idx = np.argsort(-punteggi)[:k]
    return [(int(i), float(punteggi[i])) for i in idx]


# ---------------------------------------------------------------- aggiunte di Orfeo
def chat_json(messaggi, modello, url=DEFAULT_URL, tentativi=2, **kw):
    """Come chat(), ma pretende un oggetto JSON; se il modello sbaglia riprova una volta."""
    ultimo = ""
    for _ in range(tentativi):
        ultimo = chat(messaggi, modello, url, formato="json", **kw)
        m = re.search(r"\{.*\}", ultimo, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    raise ErroreLLM(f"Il modello non ha restituito un JSON valido: {ultimo[:200]}")


def assicura_avviato(url=DEFAULT_URL, attesa=60, log=lambda t: None):
    """Se Ollama è spento prova ad aprirlo (serve alle esecuzioni pianificate) e aspetta che risponda."""
    import subprocess
    import sys
    import time
    try:
        elenco_modelli(url)
        return True
    except ErroreLLM:
        pass
    if not e_locale(url):
        return False
    log("Ollama non risponde: provo ad avviarlo…")
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-g", "-a", "Ollama"], capture_output=True)
        elif sys.platform == "win32":
            subprocess.Popen(["ollama", "serve"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        return False
    fine = time.time() + attesa
    while time.time() < fine:
        time.sleep(3)
        try:
            elenco_modelli(url)
            return True
        except ErroreLLM:
            continue
    return False
