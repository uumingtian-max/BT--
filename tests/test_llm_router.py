from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict

from backend.llm_router import LLMRouter, parse_fallback_order


class RouteMockHandler(BaseHTTPRequestHandler):
    model_id = "mock-model"
    response_text = "mock route ok"
    expected_authorization = "Bearer local"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._send_json({"object": "list", "data": [{"id": self.model_id}]})
        else:
            self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._send_json({"error": "not found"}, status=404)
            return
        assert self.headers.get("Authorization") == self.expected_authorization
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        assert payload["model"] == self.model_id
        self._send_json({"choices": [{"message": {"role": "assistant", "content": self.response_text}}]})

    def log_message(self, format: str, *args: object) -> None:
        return


def make_handler(model_id: str, response_text: str, expected_authorization: str = "Bearer local"):
    class CustomHandler(RouteMockHandler):
        pass
    CustomHandler.model_id = model_id
    CustomHandler.response_text = response_text
    CustomHandler.expected_authorization = expected_authorization
    return CustomHandler


def start_server(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_address[1]}/v1"


def stop_server(server: HTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    thread.join(timeout=2)


def patch_env(values: Dict[str, str]) -> Dict[str, str | None]:
    old = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    return old


def restore_env(old: Dict[str, str | None]) -> None:
    for key, value in old.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_parse_fallback_order_filters_invalid_values() -> None:
    assert parse_fallback_order("gpu,npu,api") == ["gpu", "npu", "api"]
    assert parse_fallback_order("bad,npu") == ["npu"]
    assert parse_fallback_order("bad") == ["gpu", "npu", "api"]


def test_router_supports_gpu_npu_api_routes_and_sk_key() -> None:
    gpu_server, gpu_thread, gpu_url = start_server(make_handler("gpu-model", "gpu ok"))
    npu_server, npu_thread, npu_url = start_server(make_handler("npu-model", "npu ok"))
    api_server, api_thread, api_url = start_server(make_handler("api-model", "api ok", "Bearer sk-test-key"))
    old = patch_env({
        "GPU_OPENAI_BASE_URL": gpu_url,
        "GPU_OPENAI_API_KEY": "local",
        "GPU_MODEL": "gpu-model",
        "NPU_OPENAI_BASE_URL": npu_url,
        "NPU_OPENAI_API_KEY": "local",
        "NPU_MODEL": "npu-model",
        "API_OPENAI_BASE_URL": api_url,
        "API_OPENAI_API_KEY": "sk-test-key",
        "API_MODEL": "api-model",
        "BKLT_LLM_FALLBACK_ORDER": "gpu,npu,api",
    })
    try:
        router = LLMRouter.from_env()
        health = router.healthcheck("auto")
        assert health["ok"] is True
        assert health["routes"]["gpu"]["model_available"] is True
        assert health["routes"]["npu"]["model_available"] is True
        assert health["routes"]["api"]["model_available"] is True
        assert router.chat("ping", route="gpu") == "gpu ok"
        assert router.chat("ping", route="npu") == "npu ok"
        assert router.chat("ping", route="api") == "api ok"
        assert router.chat("ping", route="auto") == "gpu ok"
    finally:
        restore_env(old)
        stop_server(gpu_server, gpu_thread)
        stop_server(npu_server, npu_thread)
        stop_server(api_server, api_thread)
