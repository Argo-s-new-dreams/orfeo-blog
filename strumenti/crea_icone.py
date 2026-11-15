"""crea_icone.py - genera le icone dell'app (PNG, ICO per Windows, iconset per macOS).

Uso:
  python strumenti/crea_icone.py                  # lettera e colore dallo standard (LETTERA_LOGO, accento #2DD4BF)
  python strumenti/crea_icone.py mia_icona.png    # parte da un PNG quadrato (almeno 1024x1024)

Serve Pillow (pip install pillow). Le icone sono sempre PNG/ICO/ICNS: niente SVG come file finale.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RADICE = Path(__file__).resolve().parent.parent
APP = RADICE / "app"
SFONDO, TESTO = (45, 212, 191, 255), (15, 17, 21, 255)  # accento e "su_accento" del tema Studio


def base_da_lettera(lettera, lato=1024):
    img = Image.new("RGBA", (lato, lato), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margine = lato // 10  # margine standard delle icone macOS
    d.rounded_rectangle([margine, margine, lato - margine, lato - margine], radius=lato // 5, fill=SFONDO)
    font = None
    for nome in ("Inter-Bold.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf",
                 "/System/Library/Fonts/SFNS.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(nome, lato // 2)
            break
        except OSError:
            continue
    font = font or ImageFont.load_default()
    box = d.textbbox((0, 0), lettera, font=font)
    x = (lato - (box[2] - box[0])) / 2 - box[0]
    y = (lato - (box[3] - box[1])) / 2 - box[1]
    d.text((x, y), lettera, font=font, fill=TESTO)
    return img


def main():
    if len(sys.argv) > 1:
        base = Image.open(sys.argv[1]).convert("RGBA").resize((1024, 1024), Image.LANCZOS)
    else:
        testo = (APP / "progetto.py").read_text(encoding="utf-8")
        lettera = re.search(r'^LETTERA_LOGO = "(.)"', testo, re.M).group(1)
        base = base_da_lettera(lettera)
    base.resize((256, 256), Image.LANCZOS).save(APP / "icon.png")
    base.save(APP / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    iconset = APP / "icon.iconset"
    iconset.mkdir(exist_ok=True)
    for lato in (16, 32, 128, 256, 512):
        base.resize((lato, lato), Image.LANCZOS).save(iconset / f"icon_{lato}x{lato}.png")
        base.resize((lato * 2, lato * 2), Image.LANCZOS).save(iconset / f"icon_{lato}x{lato}@2x.png")
    print("Icone create in app/: icon.png, icon.ico, icon.iconset/")


if __name__ == "__main__":
    main()
