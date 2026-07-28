Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & currentDir & "\run_daily_sync.bat" & Chr(34), 0
Set WshShell = Nothing
