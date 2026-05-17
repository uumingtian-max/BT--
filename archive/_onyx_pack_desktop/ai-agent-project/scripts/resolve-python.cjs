/**
 * Print one line: absolute path to python.exe, or "python" for PATH lookup.
 * Used by start-backend.cmd and Electron. Override with AI_AGENT_PYTHON.
 */
/* eslint-disable no-console */
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const envPy = (process.env.AI_AGENT_PYTHON || "").trim();
if (envPy) {
  console.log(envPy);
  process.exit(0);
}

const home = process.env.USERPROFILE || process.env.HOME || "";
const candidates = [
  path.join(home, "miniconda3", "envs", "quant", "python.exe"),
  path.join(home, "miniconda3", "python.exe"),
  path.join(home, "anaconda3", "python.exe"),
];
for (const p of candidates) {
  try {
    if (p && fs.existsSync(p)) {
      console.log(p);
      process.exit(0);
    }
  } catch (_) {
    /* continue */
  }
}

if (process.platform === "win32") {
  try {
    const o = execSync("where.exe python", { encoding: "utf8", windowsHide: true });
    const first = o
      .split(/\r?\n/)
      .map((s) => s.trim())
      .find(Boolean);
    if (first) {
      console.log(first);
      process.exit(0);
    }
  } catch (_) {
    /* continue */
  }
  try {
    const out = execSync('py -3 -c "import sys; print(sys.executable)"', {
      encoding: "utf8",
      windowsHide: true,
    }).trim();
    if (out) {
      console.log(out);
      process.exit(0);
    }
  } catch (_) {
    /* continue */
  }
}

console.log("python");
