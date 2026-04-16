Set WshShell = CreateObject("WScript.Shell")
dossier = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
WshShell.CurrentDirectory = dossier
WshShell.Run "cmd /c """ & dossier & "START.bat""", 1, False
