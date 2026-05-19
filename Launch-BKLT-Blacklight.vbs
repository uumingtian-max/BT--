' BKLT ???????????
Set sh = CreateObject("WScript.Shell")
root = Replace(WScript.ScriptFullName, "Launch-BKLT-Blacklight.vbs", "")
sh.CurrentDirectory = root
sh.Run "cmd /c """ & root & "START_APP.bat""", 0, False
