# 生成 SGLang 用的 config.json（backbone -> model 层名）
$ErrorActionPreference = "Stop"
$src = "D:\models\Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4"
$dstDir = "D:\models\Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4-sglang-win"
$dst = Join-Path $dstDir "config.json"

if (-not (Test-Path (Join-Path $src "config.json"))) {
    throw "模型目录不存在: $src"
}
New-Item -ItemType Directory -Force -Path $dstDir | Out-Null

$py = @'
import json, os, sys
src, dst = sys.argv[1], sys.argv[2]
with open(os.path.join(src, "config.json"), encoding="utf-8-sig") as f:
    cfg = json.load(f)
q = cfg.get("quantization_config")
if isinstance(q, dict) and isinstance(q.get("quantized_layers"), dict):
    q["quantized_layers"] = {
        k.replace("language_model.backbone.", "language_model.model."): v
        for k, v in q["quantized_layers"].items()
    }
with open(dst, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
print("OK", dst)
'@
$tmp = Join-Path $env:TEMP "bt_patch_nemotron_config.py"
Set-Content -LiteralPath $tmp -Value $py -Encoding UTF8
python $tmp $src $dst
Write-Host "补丁 config 已写入: $dst" -ForegroundColor Green
