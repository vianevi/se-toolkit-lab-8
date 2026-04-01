"""MCP server exposing observability data as typed tools."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

server = Server("obs")

# Configuration from environment
VICTORIALOGS_URL = os.environ.get("VICTORIALOGS_URL", "http://victorialogs:9428")
VICTORIATRACES_URL = os.environ.get("VICTORIATRACES_URL", "http://victoriatraces:10428")


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _LogsSearchInput(BaseModel):
    query: str = Field(
        default="severity:ERROR",
        description="LogsQL query string (e.g., 'severity:ERROR service.name:\"backend\"')",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")


class _LogsErrorCountInput(BaseModel):
    service: str = Field(
        default="",
        description="Filter by service name (optional, empty means all services)",
    )
    minutes: int = Field(default=60, ge=1, description="Time window in minutes")


class _TracesListInput(BaseModel):
    service: str = Field(
        default="Learning Management Service",
        description="Service name to filter traces",
    )
    limit: int = Field(default=10, ge=1, le=50, description="Max traces to return")


class _TracesGetInput(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _http_get(url: str, params: dict[str, Any] | None = None) -> Any:
    """Make HTTP GET request."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def _http_post(url: str, data: Any) -> Any:
    """Make HTTP POST request."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=data)
        response.raise_for_status()
        return response.json()


def _text(data: Any) -> list[TextContent]:
    """Serialize data to JSON text."""
    if isinstance(data, (dict, list)):
        text = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        text = str(data)
    return [TextContent(type="text", text=text)]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchInput) -> list[TextContent]:
    """Search logs using VictoriaLogs."""
    url = f"{VICTORIALOGS_URL}/select/logsql/query"
    params = {"query": args.query, "limit": args.limit}
    try:
        result = await _http_get(url, params)
        return _text(result)
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaLogs query failed: {e}"})


async def _logs_error_count(args: _LogsErrorCountInput) -> list[TextContent]:
    """Count errors per service over a time window."""
    time_filter = f"_time:{args.minutes}m"
    service_filter = f'service.name:"{args.service}"' if args.service else ""
    query = f"{time_filter} severity:ERROR {service_filter}"

    url = f"{VICTORIALOGS_URL}/select/logsql/query"
    params = {"query": query, "limit": 1000}

    try:
        result = await _http_get(url, params)
        # Count errors
        if isinstance(result, list):
            count = len(result)
        else:
            count = 0

        return _text(
            {
                "query": query,
                "error_count": count,
                "time_window_minutes": args.minutes,
                "service": args.service or "all",
            }
        )
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaLogs query failed: {e}"})


async def _traces_list(args: _TracesListInput) -> list[TextContent]:
    """List recent traces for a service."""
    # VictoriaTraces uses Jaeger-compatible API
    url = f"{VICTORIATRACES_URL}/select/jaeger/api/traces"
    params = {"service": args.service, "limit": args.limit}

    try:
        result = await _http_get(url, params)
        # Simplify the response
        if isinstance(result, dict) and "data" in result:
            traces = result["data"]
            simplified = [
                {
                    "trace_id": t.get("traceID", ""),
                    "spans": len(t.get("spans", [])),
                    "start_time": t.get("startTime", 0),
                }
                for t in traces
            ]
            return _text({"traces": simplified, "total": len(traces)})
        return _text(result)
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaTraces query failed: {e}"})


async def _traces_get(args: _TracesGetInput) -> list[TextContent]:
    """Fetch a specific trace by ID."""
    url = f"{VICTORIATRACES_URL}/select/jaeger/api/traces/{args.trace_id}"

    try:
        result = await _http_get(url)
        # Simplify the response
        if isinstance(result, dict) and "data" in result:
            traces = result["data"]
            if traces:
                trace = traces[0]
                spans = trace.get("spans", [])
                simplified_spans = [
                    {
                        "span_id": s.get("spanID", ""),
                        "operation_name": s.get("operationName", ""),
                        "service_name": s.get("process", {}).get(
                            "serviceName", "unknown"
                        ),
                        "duration": s.get("duration", 0),
                        "tags": {t["key"]: t["value"] for t in s.get("tags", [])},
                    }
                    for s in spans
                ]
                return _text(
                    {
                        "trace_id": trace.get("traceID", ""),
                        "spans": simplified_spans,
                        "total_spans": len(spans),
                    }
                )
        return _text(result)
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaTraces query failed: {e}"})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_Tools = dict[
    str, tuple[type[BaseModel], Callable[..., Awaitable[list[TextContent]]], Tool]
]

_TOOLS: _Tools = {}


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    schema = model.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("title", None)
    _TOOLS[name] = (
        model,
        handler,
        Tool(name=name, description=description, inputSchema=schema),
    )


_register(
    "obs_logs_search",
    "Search logs in VictoriaLogs using LogsQL query.",
    _LogsSearchInput,
    _logs_search,
)
_register(
    "obs_logs_error_count",
    "Count errors per service over a time window in VictoriaLogs.",
    _LogsErrorCountInput,
    _logs_error_count,
)
_register(
    "obs_traces_list",
    "List recent traces for a service from VictoriaTraces.",
    _TracesListInput,
    _traces_list,
)
_register(
    "obs_traces_get",
    "Fetch a specific trace by ID from VictoriaTraces.",
    _TracesGetInput,
    _traces_get,
)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [entry[2] for entry in _TOOLS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    entry = _TOOLS.get(name)
    if entry is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    model_cls, handler, _ = entry
    try:
        args = model_cls.model_validate(arguments or {})
        return await handler(args)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
