' BT（黑光）桌面快捷方式 — 官方链：根目录 START_APP.bat -> launcher\START_APP.bat
Set fso = CreateObject("Scripting.FileSystemObject")
launcherDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(launcherDir)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = projectRoot
sh.Run "cmd /c """ & projectRoot & "\START_APP.bat""", 0, False
