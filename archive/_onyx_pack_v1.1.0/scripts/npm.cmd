@echo off
REM Strip sandbox devdir so npm 11+ does not warn (Cursor / CI inject NPM_CONFIG_DEVDIR).
set "NPM_CONFIG_DEVDIR="
set "npm_config_devdir="
call npm %*
