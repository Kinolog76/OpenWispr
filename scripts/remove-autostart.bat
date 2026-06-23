@echo off
REM Remove OpenWispr from Windows startup.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$lnk=Join-Path ([Environment]::GetFolderPath('Startup')) 'OpenWispr.lnk'; if (Test-Path $lnk) { Remove-Item $lnk -Force; Write-Host ('Removed: ' + $lnk) } else { Write-Host 'Not installed.' }"
pause
