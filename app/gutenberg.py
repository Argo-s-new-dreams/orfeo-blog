"""gutenberg.py - da Markdown semplice (### ####, elenchi, grassetto, corsivo, link) a blocchi Gutenberg."""
import html
import re


def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", lambda m: f'<a href="{html.escape(html.unescape(m.group(2)))}">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[VERIFY:?([^\]]*)\]", lambda m: f'<mark>[VERIFY{":" if m.group(1) else ""}{m.group(1)}]</mark>', t)
    return t


def _titolo(livello, testo):
    return (f'<!-- wp:heading {{"level":{livello}}} -->\n<h{livello} class="wp-block-heading">{_inline(testo)}</h{livello}>\n'
            f"<!-- /wp:heading -->")


def _paragrafo(testo):
    return f"<!-- wp:paragraph -->\n<p>{_inline(testo)}</p>\n<!-- /wp:paragraph -->"


def _elenco(voci, ordinato):
    tag = "ol" if ordinato else "ul"
    attr = ' {"ordered":true}' if ordinato else ""
    li = "\n".join(f"<!-- wp:list-item -->\n<li>{_inline(v)}</li>\n<!-- /wp:list-item -->" for v in voci)
    cls = ' class="wp-block-list"'
    return f"<!-- wp:list{attr} -->\n<{tag}{cls}>{li}</{tag}>\n<!-- /wp:list -->"


def converti(md):
    blocchi, para, voci, ordinato = [], [], [], False

    def chiudi_para():
        if para:
            blocchi.append(_paragrafo(" ".join(s.strip() for s in para)))
            para.clear()

    def chiudi_elenco():
        if voci:
            blocchi.append(_elenco(list(voci), ordinato))
            voci.clear()

    for riga in md.splitlines():
        s = riga.rstrip()
        m_h = re.match(r"^(#{2,6})\s+(.+)$", s)
        m_ul = re.match(r"^\s*[-*•]\s+(.+)$", s)
        m_ol = re.match(r"^\s*\d+[.)]\s+(.+)$", s)
        if m_h:
            chiudi_para(); chiudi_elenco()  # noqa: E702
            blocchi.append(_titolo(min(max(len(m_h.group(1)), 2), 6), m_h.group(2).strip()))
        elif m_ul or m_ol:
            chiudi_para()
            nuovo_ord = bool(m_ol)
            if voci and nuovo_ord != ordinato:
                chiudi_elenco()
            ordinato = nuovo_ord
            voci.append((m_ul or m_ol).group(1).strip())
        elif not s.strip():
            chiudi_para(); chiudi_elenco()  # noqa: E702
        elif re.match(r"^\s*(-{3,}|\*{3,})\s*$", s):
            chiudi_para(); chiudi_elenco()  # noqa: E702
            blocchi.append('<!-- wp:separator -->\n<hr class="wp-block-separator has-alpha-channel-opacity"/>\n<!-- /wp:separator -->')
        else:
            chiudi_elenco()
            para.append(s)
    chiudi_para()
    chiudi_elenco()
    return "\n\n".join(blocchi)
