from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import env_bootstrap

env_bootstrap.load_backend_dotenv()

import skill_pack


def main() -> int:
    skills = skill_pack._load_all_skills()
    if not skills:
        print(json.dumps({"ok": False, "error": "no skills found"}, ensure_ascii=False))
        return 1
    try:
        index = skill_pack._build_embedding_index(skills)
    except Exception as e:
        print(
            json.dumps(
                {
                    "ok": False,
                    "model": skill_pack.EMBED_MODEL,
                    "ollama_base": skill_pack._ollama_base_url(),
                    "error": str(e),
                    "hint": "先运行: ollama pull nomic-embed-text，并确保 Ollama 服务已启动。",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "ok": True,
                "model": index.get("model"),
                "ollama_base": index.get("ollama_base"),
                "vectors": len(index.get("vectors", {})),
                "index_path": str(skill_pack.EMBED_INDEX_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
