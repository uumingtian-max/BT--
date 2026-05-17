' 旧快捷方式兼容 → Launch-BT-Heiguang.vbs
Set sh = CreateObject("WScript.Shell")
dir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.Run "wscript.exe """ & dir & "\..\Launch-BT-Heiguang.vbs""", 0, False
