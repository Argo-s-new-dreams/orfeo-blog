@echo off
rem Doppio clic per installare l'app su Windows (x64 e ARM).
rem Toglie il contrassegno "scaricato da Internet" ai file del pacchetto, poi avvia l'installer.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -LiteralPath '%~dp0' -Recurse | Unblock-File"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\installa_windows.ps1"
echo.
pause
