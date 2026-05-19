# 预热并 pin 全部岗位模型（keep_alive），黑光启动时也会自动跑一遍
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$resolve = Join-Path $Root "scripts\resolve-python.cjs"
$Python = (& node $resolve 2>$null).Trim()
if (-not (Test-Path $Python)) { $Python = "python" }

Write-Host "[pin-ollama] 仅预热常驻 4 模型（coder 按需，不预热）" -ForegroundColor Cyan
& $Python -c @"
import sys
sys.path.insert(0, r'$Root\backend')
from env_bootstrap import load_backend_dotenv
load_backend_dotenv()
from ollama_pins import warm_all_pinned_models, role_map_for_ui, keep_alive_duration, strict_model_roles
import json
print('keep_alive:', keep_alive_duration())
print('strict_roles:', strict_model_roles())
print(json.dumps(warm_all_pinned_models(), ensure_ascii=False, indent=2))
print('--- 岗位表 ---')
for row in role_map_for_ui():
    print(f\"  {row['model']}: {row['role']}\")
"@

Write-Host "`n查看当前加载: ollama ps" -ForegroundColor DarkGray
ollama ps 2>$null
