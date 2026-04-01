#!/usr/bin/env python3
"""Entrypoint for nanobot gateway Docker container.

Resolves environment variables into config.json at runtime,
then launches nanobot gateway.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    config_path = Path("/app/nanobot/config.json")
    resolved_path = Path("/app/nanobot/config.resolved.json")
    workspace_path = Path("/app/nanobot/workspace")

    # Read base config
    with open(config_path) as f:
        config = json.load(f)

    # Override provider API key and base URL from env vars
    # Note: We use QWEN_CODE_API_KEY (the gateway's key), not LLM_API_KEY (the upstream key)
    llm_api_key = os.environ.get("QWEN_CODE_API_KEY") or os.environ.get("LLM_API_KEY")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
        # Qwen Code API expects X-API-Key header
        config["providers"]["custom"]["extraHeaders"] = {
            "X-API-Key": llm_api_key
        }
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model

    # Override gateway settings from env vars
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")

    if gateway_host:
        config.setdefault("gateway", {})["host"] = gateway_host
    if gateway_port:
        config.setdefault("gateway", {})["port"] = int(gateway_port)

    # Configure webchat channel from env vars
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT")
    access_key = os.environ.get("NANOBOT_ACCESS_KEY")

    if "channels" not in config:
        config["channels"] = {}

    config["channels"]["webchat"] = {
        "enabled": True,
        "allowFrom": ["*"],
    }

    if webchat_host:
        config["channels"]["webchat"]["host"] = webchat_host
    if webchat_port:
        config["channels"]["webchat"]["port"] = int(webchat_port)
    if access_key:
        config["channels"]["webchat"]["accessKey"] = access_key

    # Configure MCP servers from env vars
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")

    if "tools" not in config:
        config["tools"] = {}
    if "mcpServers" not in config["tools"]:
        config["tools"]["mcpServers"] = {}

    # LMS MCP server
    if lms_backend_url or lms_api_key:
        config["tools"]["mcpServers"]["lms"] = {
            "command": "python",
            "args": ["-m", "mcp_lms"],
        }
        env = {}
        if lms_backend_url:
            env["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
        if lms_api_key:
            env["NANOBOT_LMS_API_KEY"] = lms_api_key
        if env:
            config["tools"]["mcpServers"]["lms"]["env"] = env

    # WebChat MCP server for structured UI messages
    webchat_ui_relay_url = os.environ.get("NANOBOT_WEBCHAT_UI_RELAY_URL")
    webchat_ui_token = os.environ.get("NANOBOT_WEBCHAT_UI_TOKEN")

    if webchat_ui_relay_url or webchat_ui_token:
        env = {}
        if webchat_ui_relay_url:
            env["NANOBOT_WEBCHAT_UI_RELAY_URL"] = webchat_ui_relay_url
        if webchat_ui_token:
            env["NANOBOT_WEBCHAT_UI_TOKEN"] = webchat_ui_token
        if env:
            config["tools"]["mcpServers"]["webchat"] = {
                "command": "python",
                "args": ["-m", "mcp_webchat"],
                "env": env,
            }

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}", file=sys.stderr)

    # Run nanobot gateway
    subprocess.run([
        "nanobot",
        "gateway",
        "--config",
        str(resolved_path),
        "--workspace",
        str(workspace_path),
    ], check=True)


if __name__ == "__main__":
    main()
