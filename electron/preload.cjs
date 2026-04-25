const { contextBridge, app } = require("electron");
const pkg = require("../package.json");

contextBridge.exposeInMainWorld("desktop", {
  platform: process.platform,
  isElectron: true,
  version: pkg.version,
  appName: pkg.name,
});
