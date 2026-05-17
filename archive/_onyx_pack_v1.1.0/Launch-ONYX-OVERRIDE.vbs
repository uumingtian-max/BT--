' 桌面快捷方式启动器 — 隐藏窗口运行，便于绑定高清 .ico（避免 .bat 图标被系统忽略）
Set sh = CreateObject("WScript.Shell")
root = Replace(WScript.ScriptFullName, "Launch-ONYX-OVERRIDE.vbs", "")
sh.CurrentDirectory = root
sh.Run "cmd /c """ & root & "START_APP.bat""", 0, False
