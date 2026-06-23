' Silent launcher for running OpenWispr from source with no console window.
' (The installed .exe is launched directly; this is for dev / source runs.)
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
pkgdir = fso.GetParentFolderName(WScript.ScriptFullName)
root   = fso.GetParentFolderName(pkgdir)
sh.CurrentDirectory = root
pythonw = root & "\.venv\Scripts\pythonw.exe"
sh.Run """" & pythonw & """ -m openwispr", 0, False
