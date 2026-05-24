"""Typed settings (validated after env_bootstrap loads backend/.env)."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    # env 由 env_bootstrap.load_backend_dotenv() 预先注入 os.environ
    model_config = SettingsConfigDict(extra="ignore", env_file=None)

    backend_host: str = Field(default="127.0.0.1", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    mobile_access_token: str = Field(default="", alias="MOBILE_ACCESS_TOKEN")
    require_api_token_on_lan: bool = Field(default=True, alias="REQUIRE_API_TOKEN_ON_LAN")
    agent_tool_auto_confirm: bool = Field(default=True, alias="AGENT_TOOL_AUTO_CONFIRM")
    smart_router_enabled: bool = Field(default=True, alias="SMART_ROUTER_ENABLED")
    llm_backend: str = Field(default="ollama", alias="LLM_BACKEND")

    @field_validator("backend_port")
    @classmethod
    def _port_range(cls, v: int) -> int:
        return max(1, min(65535, int(v)))

    @field_validator("backend_host", "llm_backend", mode="before")
    @classmethod
    def _strip(cls, v: object) -> object:
        return str(v).strip() if v is not None else v


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


def validate_startup_settings() -> list[str]:
    warnings: list[str] = []
    s = get_settings()
    host = (s.backend_host or "").strip()
    if host in ("0.0.0.0", "::") and s.require_api_token_on_lan and not s.mobile_access_token:
        warnings.append(
            "BACKEND_HOST 监听所有网卡但未设置 MOBILE_ACCESS_TOKEN；"
            "远程/LAN 访问将无法鉴权。请设置 MOBILE_ACCESS_TOKEN 或将 REQUIRE_API_TOKEN_ON_LAN=0（不推荐）。"
        )
    if (
        s.llm_backend.lower() in ("openai", "openai_compatible", "vllm")
        and not os.environ.get("OPENAI_BASE_URL", "").strip()
    ):
        warnings.append("LLM_BACKEND 为网关类但 OPENAI_BASE_URL 为空，将回退 Ollama。")
    return warnings
