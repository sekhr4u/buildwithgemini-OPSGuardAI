# ruff: noqa
# Copyright 2026 Google LLC
# OpsGuard AI Root Agent Definition

import datetime
import json
import os
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .a2ui_utils import a2ui_callback
from .tools import (
    check_github_service_status,
    find_nearby_places,
    generate_domain_image,
    generate_incident_diagram,
    geocode_address,
    get_incident,
    inspect_local_codebase,
    list_incidents,
    query_cloud_logs,
    report_incident,
    update_incident_status,
)

# Hardcoded Project ID, Location, and Memory Bank ID
PROJECT_ID = "qwiklabs-gcp-03-0991ea70e49a"
LOCATION = "us-east1"
MEMORY_BANK_ID = "5350129022758027264"

# Load Agent Engine resource name from deployment_metadata.json
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
deployment_metadata_path = os.path.join(base_dir, "deployment_metadata.json")

agent_engine_resource_name = None
sandbox_resource_name = None

if os.path.exists(deployment_metadata_path):
    try:
        with open(deployment_metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            agent_engine_resource_name = metadata.get("remote_agent_runtime_id")
            sandbox_resource_name = metadata.get("sandbox_resource_name")
            if agent_engine_resource_name:
                MEMORY_BANK_ID = agent_engine_resource_name.split("/")[-1]
    except Exception as exc:
        print(f"Warning: Could not read deployment_metadata.json: {exc}")

if sandbox_resource_name:
    code_executor = AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_resource_name
    )
else:
    code_executor = AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=agent_engine_resource_name
    )


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to extract durable facts and session information into Vertex AI Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as exc:
        print(f"Warning: Could not add session to memory: {exc}")
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are OpsGuard AI, an autonomous DevOps and Incident Triage Agent. "
        "Your mission is to help SRE and engineering teams manage software incidents, "
        "retrieve Cloud Logging error streams, inspect local codebase files for bugs, "
        "execute python analysis scripts in a safe Agent Platform sandbox environment, "
        "generate visual topology diagrams and domain images, report outages, check GitHub infrastructure status, "
        "geocode server data center addresses, find nearby facilities, update incident statuses in Firestore, "
        "and remember team preferences, user facts (such as allergies or dietary requirements), and incident history across sessions using Vertex AI Memory Bank."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        list_incidents,
        get_incident,
        report_incident,
        update_incident_status,
        query_cloud_logs,
        inspect_local_codebase,
        generate_incident_diagram,
        generate_domain_image,
        check_github_service_status,
        geocode_address,
        find_nearby_places,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

# Vertex AI Memory Bank service instance for deployed Agent Runtime
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=MEMORY_BANK_ID,
)

app = App(
    root_agent=root_agent,
    name="app",
)
