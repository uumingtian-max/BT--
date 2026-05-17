// 预留：与渲染进程安全通信
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("agentDesktop", { version: "1.0.0" });
