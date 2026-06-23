' Silent launcher for OpenWispr: starts the app in the background with no
' console window. The tray icon is the only visible part.
' Double-click this file to run OpenWispr like Wispr Flow.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
here = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = here
pythonw = here & "\.venv\Scripts\pythonw.exe"
script  = here & "\flow.py"
' 0 = hidden window, False = don't wait for it to exit
sh.Run """" & pythonw & """ """ & script & """", 0, False
