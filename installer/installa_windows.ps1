# Installer Windows (x64 e ARM) comune a tutte le app AI locali. Avviato da "Installa-Windows.bat".
# Legge nome e impostazioni da app\progetto.py. Non servono diritti di amministratore.
$ErrorActionPreference = "Stop"
$Src = Join-Path (Split-Path $PSScriptRoot -Parent) "app"

function Passo($n, $testo) { Write-Host "`n[$n/5] $testo" -ForegroundColor Cyan }
function Aggiorna-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}
function Installa-Se-Manca($comando, $id) {
    if (Get-Command $comando -ErrorAction SilentlyContinue) { Write-Host "  $comando gia' presente."; return }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget non trovato. Installa 'Programma di installazione app' dal Microsoft Store e riprova."
    }
    Write-Host "  Installo $comando..."
    winget install -e --id $id --accept-source-agreements --accept-package-agreements | Out-Host
    Aggiorna-Path
    if (-not (Get-Command $comando -ErrorAction SilentlyContinue)) {
        throw "$comando installato ma non ancora visibile: chiudi questa finestra e rilancia l'installer."
    }
}
function Valore($nome) {
    $riga = Select-String -Path (Join-Path $Src "progetto.py") -Pattern "^$nome\s*=\s*`"([^`"]*)`"" | Select-Object -First 1
    if (-not $riga) { throw "$nome non trovato in app\progetto.py" }
    return $riga.Matches[0].Groups[1].Value
}

try {
    $Slug = Valore "SLUG"
    $Nome = Valore "NOME"
    $Versione = Valore "VERSIONE"
    $PyWin = Valore "PYTHON_WINDOWS"
    $Casa = Join-Path $HOME "$Slug-env"
    Write-Host "=== Installazione $Nome (versione $Versione) ===" -ForegroundColor Green
    Write-Host "Cartella: $Casa"

    Passo 1 "Strumenti di base (uv)"
    Installa-Se-Manca "uv" "astral-sh.uv"

    Passo 2 "Ambiente Python"
    $py = Join-Path $Casa "Scripts\python.exe"
    # chiude eventuali istanze dell'app ancora aperte (bloccano i file)
    Get-Process python, pythonw -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -and $_.Path.StartsWith($Casa, [StringComparison]::OrdinalIgnoreCase) } |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    $attesa = if ($PyWin -eq "x64") { "win-amd64" } else { "" }
    if (Test-Path $py) {
        # sysconfig dice la vera architettura dell'interprete (platform.machine() su ARM mente in emulazione)
        $plat = ""; $sano = $false
        try { $plat = (& $py -c "import sysconfig; print(sysconfig.get_platform())" 2>$null) } catch {}
        try { & $py -c "import encodings" 2>$null; $sano = ($LASTEXITCODE -eq 0) } catch {}
        if ($sano -and (($attesa -eq "") -or ($plat -eq $attesa))) {
            Write-Host "  Ambiente esistente ($plat) riutilizzato: impostazioni e dati restano."
        } else {
            Write-Host "  Ambiente esistente non utilizzabile ($plat): lo ricreo." -ForegroundColor Yellow
            Get-ChildItem $Casa -Force -Exclude "dati" | Remove-Item -Recurse -Force
        }
    }
    if (-not (Test-Path $py)) {
        if ($PyWin -eq "x64") { uv venv $Casa --python cpython-3.12-windows-x86_64-none --allow-existing | Out-Host }
        else { uv venv $Casa --python 3.12 --allow-existing | Out-Host }
        if ($LASTEXITCODE -ne 0) { throw "Creazione dell'ambiente Python non riuscita." }
    }

    Passo 3 "Librerie (alcuni minuti la prima volta)"
    uv pip install --python $py -r (Join-Path $Src "requisiti.txt") | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Installazione delle librerie non riuscita (vedi messaggi sopra)." }

    Passo 4 "Copia dell'applicazione"
    $Dest = Join-Path $Casa "app"
    New-Item -ItemType Directory -Force -Path $Dest, (Join-Path $Casa "dati") | Out-Null
    Copy-Item (Join-Path $Src "*") $Dest -Recurse -Force

    Passo 5 "Collegamenti su Desktop e menu Start"
    $ws = New-Object -ComObject WScript.Shell
    foreach ($cartella in @([Environment]::GetFolderPath("Desktop"), [Environment]::GetFolderPath("Programs"))) {
        $lnk = $ws.CreateShortcut((Join-Path $cartella "$Nome.lnk"))
        $lnk.TargetPath = Join-Path $Casa "Scripts\pythonw.exe"
        $lnk.Arguments = '"' + (Join-Path $Dest "main.py") + '"'
        $lnk.WorkingDirectory = $Dest
        $lnk.IconLocation = Join-Path $Dest "icon.ico"
        $lnk.Description = "$Nome (AI locale)"
        $lnk.Save()
    }

    Write-Host "`nINSTALLAZIONE COMPLETATA" -ForegroundColor Green
    Write-Host "Apri '$Nome' dal Desktop o dal menu Start."
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Write-Host "NOTA: per le funzioni AI serve Ollama: https://ollama.com" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "`nERRORE: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Copia questo messaggio e mandalo a chi ti assiste."
    exit 1
}
