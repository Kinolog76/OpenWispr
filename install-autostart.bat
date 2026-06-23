@echo off
REM Add OpenWispr to Windows startup (per-user). Safe to re-run.
REM Creates a shortcut to OpenWispr.vbs in the Startup folder, so the app
REM launches silently (tray only) every time you log in.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[Environment]::GetFolderPath('Startup'); $w=New-Object -ComObject WScript.Shell; $lnk=Join-Path $s 'OpenWispr.lnk'; $l=$w.CreateShortcut($lnk); $l.TargetPath='%~dp0OpenWispr.vbs'; $l.WorkingDirectory=(Split-Path $l.TargetPath); $l.Save(); Write-Host ('Autostart installed: ' + $lnk)"
echo.
echo Done. OpenWispr will start with Windows.
pause
