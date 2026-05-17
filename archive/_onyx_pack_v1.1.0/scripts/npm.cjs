#!/usr/bin/env node
/**
 * Run npm with NPM_CONFIG_DEVDIR stripped (Cursor sandbox injects it; npm 11 warns as unknown).
 */
'use strict';

const { spawnSync } = require('child_process');

const env = { ...process.env };
for (const k of Object.keys(env)) {
  if (k.toLowerCase() === 'npm_config_devdir') delete env[k];
}
delete env.NPM_CONFIG_DEVDIR;

const args = process.argv.slice(2);
const cmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const r = spawnSync(cmd, args, { stdio: 'inherit', env, shell: true });
process.exit(r.status === null ? 1 : r.status);
