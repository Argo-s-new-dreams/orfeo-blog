#!/bin/bash
# Doppio clic (o tasto destro → Apri) per installare l'app su macOS Apple Silicon (M1 o successivi).
# Standard comune a tutte le app AI locali: legge nome e impostazioni da app/progetto.py.
# Non servono diritti di amministratore: tutto va nella cartella utente.
DIR="$(cd "$(dirname "$0")" && pwd)"

errore() { echo; echo "ERRORE: $1"; echo "Copia questo messaggio e mandalo a chi ti assiste."; read -r -p "Premi Invio per chiudere..."; exit 1; }
passo() { echo; echo "[$1/5] $2"; }

SLUG="$(sed -n 's/^SLUG = "\([^"]*\)".*/\1/p' "$DIR/app/progetto.py")"
[ -n "$SLUG" ] || errore "SLUG non trovato in app/progetto.py"
CASA="$HOME/$SLUG-env"

[ "$(uname -m)" = "arm64" ] || errore "Serve un Mac Apple Silicon (M1 o successivi)."

passo 1 "Strumenti di base (uv)"
for b in /opt/homebrew/bin/brew /usr/local/bin/brew "$HOME/.homebrew/bin/brew"; do
  [ -x "$b" ] && eval "$("$b" shellenv)" && break
done
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null && command -v brew >/dev/null; then
  brew install uv || echo "  (uv via Homebrew non riuscito: provo il sito ufficiale)"
fi
if ! command -v uv >/dev/null; then
  echo "  Scarico uv da astral.sh (installer ufficiale, nella tua cartella utente)..."
  curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh || errore "installazione di uv non riuscita (serve Internet)"
fi
command -v uv >/dev/null || errore "uv non trovato dopo l'installazione"

passo 2 "Ambiente Python"
if [ -x "$CASA/bin/python" ]; then
  echo "  Ambiente esistente riutilizzato: impostazioni e dati restano."
else
  uv venv "$CASA" --python 3.12 --allow-existing || errore "creazione dell'ambiente Python non riuscita"
fi
PY="$CASA/bin/python"
leggi() { (cd "$DIR/app" && "$PY" -c "import progetto as P; print(P.$1)"); }
NOME="$(leggi NOME)"; VERSIONE="$(leggi VERSIONE)"; BUNDLE_ID="$(leggi BUNDLE_ID)"; MICRO="$(leggi USO_MICROFONO)"
echo "=== Installazione $NOME (versione $VERSIONE) in $CASA ==="

passo 3 "Librerie (alcuni minuti la prima volta)"
uv pip install --python "$PY" -r "$DIR/app/requisiti.txt" || errore "installazione delle librerie non riuscita"

passo 4 "Copia dell'applicazione"
mkdir -p "$CASA/app" "$CASA/dati"
cp -R "$DIR/app/." "$CASA/app/" || errore "copia dei file non riuscita"

passo 5 "Creazione di $NOME.app in ~/Applications"
BUNDLE="$HOME/Applications/$NOME.app"
ESEGUIBILE="$(echo "$SLUG" | tr -d '-')"
mkdir -p "$BUNDLE/Contents/MacOS" "$BUNDLE/Contents/Resources"
cat > "$BUNDLE/Contents/MacOS/$ESEGUIBILE" <<EOF
#!/bin/bash
# Le app aperte dal Finder non vedono il PATH del Terminale: aggiungo ambiente dell'app, uv e Homebrew.
export PATH="$CASA/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH"
exec "$PY" "$CASA/app/main.py"
EOF
chmod +x "$BUNDLE/Contents/MacOS/$ESEGUIBILE"
MICRO_PLIST=""
[ -n "$MICRO" ] && MICRO_PLIST="<key>NSMicrophoneUsageDescription</key><string>$MICRO</string>"
cat > "$BUNDLE/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>$NOME</string>
  <key>CFBundleDisplayName</key><string>$NOME</string>
  <key>CFBundleIdentifier</key><string>$BUNDLE_ID</string>
  <key>CFBundleVersion</key><string>$VERSIONE</string>
  <key>CFBundleShortVersionString</key><string>$VERSIONE</string>
  <key>CFBundleExecutable</key><string>$ESEGUIBILE</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>NSHighResolutionCapable</key><true/>
  $MICRO_PLIST
</dict></plist>
EOF
iconutil -c icns "$CASA/app/icon.iconset" -o "$BUNDLE/Contents/Resources/icon.icns" 2>/dev/null || echo "  (icona non creata, nessun problema)"
touch "$BUNDLE"

echo
echo "INSTALLAZIONE COMPLETATA"
echo "Apri '$NOME' da Finder > Applicazioni (cartella Inizio) o con Spotlight."
if ! command -v ollama >/dev/null && [ ! -d /Applications/Ollama.app ]; then
  echo
  echo "NOTA: per le funzioni AI serve Ollama: scaricalo da https://ollama.com"
fi
open -R "$BUNDLE"
read -r -p "Premi Invio per chiudere..."
