' BKLT / BT（黑光）桌面启动 — 相对路径，可随仓库移动
Set fso = CreateObject("Scripting.FileSystemObject")
projectRoot = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = projectRoot
If fso.FileExists(projectRoot & "\START.bat") Then
  sh.Run "cmd /c """ & projectRoot & "\START.bat""", 0, False
Else
  sh.Run "cmd /c """ & projectRoot & "\START_APP.bat""", 0, False
End If
