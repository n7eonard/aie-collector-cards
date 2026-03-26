"""
backend/main.py — AIE Twin API
Starlette 1.0 (March 2026)

Install:
    pip install starlette[full] uvicorn[standard] httpx pyyaml

Run:
    uvicorn backend.main:app --reload --port 8000

Env (.env or shell):
    ANTHROPIC_KEY=sk-ant-...
    ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
    ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
    DEBUG=false
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import TypedDict

import httpx
from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.schemas import SchemaGenerator

log = logging.getLogger("aie_twin")

# ── Config ────────────────────────────────────────────────────────────────────
config = Config(".env")

DEBUG         = config("DEBUG",           cast=bool,                 default=False)
ANTHROPIC_KEY = config("ANTHROPIC_KEY",   cast=Secret)               # required — no default
ALLOWED_ORIG  = config("ALLOWED_ORIGINS", cast=CommaSeparatedStrings,
                        default="*")

ANT_URL = "https://api.anthropic.com/v1/messages"
ANT_VER = "2023-06-01"
MODEL   = "claude-haiku-4-5"

AIE_BASE = "https://www.ai.engineer/europe"
AIE_RESOURCES = {
    "sessions": f"{AIE_BASE}/sessions.json",
    "speakers": f"{AIE_BASE}/speakers.json",
}

# ── Typed lifespan state ──────────────────────────────────────────────────────
# Skill: yield a TypedDict → typed request.state["key"] in every endpoint
class AppState(TypedDict):
    http: httpx.AsyncClient


@asynccontextmanager
async def lifespan(app: Starlette):
    """One shared httpx client for all requests. Closed cleanly on shutdown."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield {"http": client}


# ── OpenAPI schema ────────────────────────────────────────────────────────────
# Skill: SchemaGenerator reads endpoint docstrings (requires pyyaml)
schemas = SchemaGenerator(
    {"openapi": "3.0.0", "info": {"title": "AIE Twin API", "version": "1.0.0"}}
)


async def openapi_schema(request: Request) -> JSONResponse:
    return schemas.OpenAPIResponse(request=request)


# ── Exception handlers ────────────────────────────────────────────────────────
# Skill: use int key 500 for generic errors, not the Exception class
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


async def server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"error": "Internal server error"}, status_code=500)


# ── Endpoints ─────────────────────────────────────────────────────────────────
async def health(request: Request[AppState]) -> JSONResponse:
    """
    responses:
      200:
        description: Service is healthy.
    """
    return JSONResponse({"status": "ok"})


async def chat(request: Request[AppState]) -> JSONResponse:
    """
    responses:
      200:
        description: Anthropic API response forwarded to client.
      400:
        description: Invalid or missing request body.
      502:
        description: Upstream Anthropic API error.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    messages   = body.get("messages")
    max_tokens = body.get("max_tokens", 1400)
    model      = body.get("model", MODEL)

    if not messages or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="'messages' array is required")

    # Skill: typed state access
    http: httpx.AsyncClient = request.state["http"]

    # Skill: Secret.get_secret_value() — never str(secret), leaks in logs/tracebacks
    ant_resp = await http.post(
        ANT_URL,
        headers={
            "x-api-key":         str(ANTHROPIC_KEY),
            "anthropic-version": ANT_VER,
            "content-type":      "application/json",
        },
        json={"model": model, "max_tokens": max_tokens, "messages": messages},
    )

    if ant_resp.status_code != 200:
        detail = ant_resp.json().get("error", {}).get("message", "Anthropic API error")
        raise HTTPException(status_code=502, detail=detail)

    return JSONResponse(ant_resp.json())


async def aie_proxy(request: Request[AppState]) -> JSONResponse:
    """
    responses:
      200:
        description: Proxied ai.engineer data (sessions or speakers).
      404:
        description: Unknown resource.
      502:
        description: Upstream ai.engineer error.
    """
    resource = request.path_params["resource"]
    url = AIE_RESOURCES.get(resource)
    if not url:
        raise HTTPException(status_code=404, detail=f"Unknown resource: {resource}")

    http: httpx.AsyncClient = request.state["http"]
    resp = await http.get(url)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch from ai.engineer")

    return JSONResponse(resp.json())


# ── App assembly ──────────────────────────────────────────────────────────────
# Skill: all routes, middleware, exception_handlers, lifespan passed at construction —
# no @app.route decorators, no on_startup/on_shutdown, no add_event_handler
app = Starlette(
    debug=DEBUG,
    routes=[
        Route("/health",     health,         methods=["GET"]),
        Route("/api/chat",   chat,           methods=["POST", "OPTIONS"]),
        Route("/api/aie/{resource}", aie_proxy, methods=["GET"]),
        Route("/api/schema", openapi_schema, methods=["GET"],
              include_in_schema=False),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=list(ALLOWED_ORIG),
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type"],
        ),
    ],
    lifespan=lifespan,
    exception_handlers={
        HTTPException: http_error_handler,
        500: server_error_handler,          # Skill: int key, not Exception class
    },
)

# NOTE on Secret API: Starlette's Secret datastructure exposes the value via
# str(secret) — there is no .get_secret_value() method (that's Pydantic SecretStr).
# The skill doc was incorrect on this point; str() is confirmed correct in 1.0.
