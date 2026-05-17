' BT desktop launcher wrapper
Set fso = CreateObject("Scripting.FileSystemObject")
projectRoot = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = projectRoot
sh.Run "cmd /c """ & projectRoot & "\launcher\START_APP.bat""", 0, False

