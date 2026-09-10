Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & WshShell.CurrentDirectory & "\run_247_service.bat" & chr(34), 0
Set WshShell = Nothing
