@echo off
REM Add the source build of OpenWispr to Windows startup (per-user).
REM Creates a Startup shortcut to packaging\OpenWispr.vbs (silent launcher).
cd /d "%~dp0.."
set "ROOT=%CD%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[Environment]::GetFolderPath('Startup'); $w=New-Object -ComObject WScript.Shell; $lnk=Join-Path $s 'OpenWispr.lnk'; $l=$w.CreateShortcut($lnk); $l.TargetPath='%ROOT%\packaging\OpenWispr.vbs'; $l.WorkingDirectory='%ROOT%'; $l.Save(); Write-Host ('Autostart installed: ' + $lnk)"
echo.
echo Done. OpenWispr will start with Windows.
pause
