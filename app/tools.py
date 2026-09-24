# Copyright 2026 Google LLC
# Firestore, Cloud Logging, Codebase, Diagram, GitHub, Google Maps & Image Generation tools for OpsGuard AI agent

import datetime
import json
import os
import urllib.parse
import urllib.request
from dotenv import load_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore
from google.cloud import logging as cloud_logging
from google.cloud import storage
from google.genai import types
from PIL import Image, ImageDraw

load_dotenv()

PROJECT_ID = "qwiklabs-gcp-03-0991ea70e49a"
COLLECTION_NAME = "incidents"
BUCKET_NAME = "opsguard-assets-0991ea70e49a"


def _get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_incidents(status: str = "", severity: str = "") -> str:
    """List incidents from the Firestore incident catalog, optionally filtering by status or severity.

    Args:
        status: Optional status to filter by (e.g., 'OPEN', 'INVESTIGATING', 'RESOLVED').
        severity: Optional severity to filter by (e.g., 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW').

    Returns:
        Formatted summary string of matching incident items.
    """
    db = _get_firestore_client()
    query = db.collection(COLLECTION_NAME)

    if status:
        query = query.where("status", "==", status.upper())
    if severity:
        query = query.where("severity", "==", severity.upper())

    docs = query.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        results.append(
            f"ID: {data.get('incident_id')}\n"
            f"Title: {data.get('title')}\n"
            f"Service: {data.get('service')}\n"
            f"Severity: {data.get('severity')}\n"
            f"Status: {data.get('status')}\n"
            f"Root Cause: {data.get('root_cause', 'N/A')}\n"
            f"Suggested Patch: {data.get('suggested_patch', 'N/A')}\n"
            f"Created At: {data.get('created_at', 'N/A')}\n"
            f"----------------------------------------"
        )

    if not results:
        return "No incidents found matching the criteria."

    return "\n".join(results)


def get_incident(incident_id: str) -> str:
    """Fetch details of a specific incident from Firestore by ID.

    Args:
        incident_id: The ID of the incident to retrieve (e.g., 'INC-101').

    Returns:
        String representation of the incident document details.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(incident_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Incident '{incident_id}' was not found in Firestore."

    data = doc.to_dict()
    return (
        f"Incident Details for {data.get('incident_id')}:\n"
        f"Title: {data.get('title')}\n"
        f"Service: {data.get('service')}\n"
        f"Severity: {data.get('severity')}\n"
        f"Status: {data.get('status')}\n"
        f"Stack Trace: {data.get('stack_trace', 'N/A')}\n"
        f"Root Cause: {data.get('root_cause', 'N/A')}\n"
        f"Suggested Patch: {data.get('suggested_patch', 'N/A')}\n"
        f"Created At: {data.get('created_at', 'N/A')}"
    )


def report_incident(
    title: str,
    service: str,
    severity: str,
    stack_trace: str,
    root_cause: str = "",
    suggested_patch: str = "",
) -> str:
    """Report and store a new incident in Firestore.

    Args:
        title: Short descriptive title of the failure.
        service: Name of the microservice or component affected.
        severity: Severity level ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW').
        stack_trace: Error stack trace string.
        root_cause: Description of the identified root cause.
        suggested_patch: Code snippet or patch description to fix the issue.

    Returns:
        Confirmation message with the created incident ID.
    """
    db = _get_firestore_client()
    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    incident_id = f"INC-{timestamp_str[-6:]}"

    doc_data = {
        "incident_id": incident_id,
        "title": title,
        "service": service,
        "severity": severity.upper(),
        "status": "OPEN",
        "stack_trace": stack_trace,
        "root_cause": root_cause,
        "suggested_patch": suggested_patch,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    db.collection(COLLECTION_NAME).document(incident_id).set(doc_data)
    return f"Successfully created incident document '{incident_id}' in Firestore."


def update_incident_status(
    incident_id: str, status: str, resolution_notes: str = ""
) -> str:
    """Update the status and resolution notes of an existing incident in Firestore.

    Args:
        incident_id: The ID of the incident to update (e.g., 'INC-101').
        status: The new status ('OPEN', 'INVESTIGATING', 'RESOLVED').
        resolution_notes: Optional notes explaining the resolution or triage update.

    Returns:
        Confirmation message of the update.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(incident_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Incident '{incident_id}' was not found in Firestore."

    update_payload = {
        "status": status.upper(),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    if resolution_notes:
        update_payload["resolution_notes"] = resolution_notes

    doc_ref.update(update_payload)
    return f"Successfully updated incident '{incident_id}' status to '{status.upper()}'."


def query_cloud_logs(service_name: str = "", severity: str = "ERROR", limit: int = 5) -> str:
    """Queries live runtime logs from Google Cloud Logging for error diagnosis.

    Args:
        service_name: Optional name of the microservice or cloud run service to filter logs for.
        severity: Minimum log severity ('DEFAULT', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'). Defaults to 'ERROR'.
        limit: Maximum number of log entries to retrieve (1 to 20). Defaults to 5.

    Returns:
        Formatted log entries retrieved from Google Cloud Logging.
    """
    try:
        client = cloud_logging.Client(project=PROJECT_ID)
        filter_parts = [f'severity >= "{severity.upper()}"']
        if service_name:
            filter_parts.append(f'resource.labels.service_name="{service_name}"')

        filter_expr = " AND ".join(filter_parts)
        entries = list(client.list_entries(filter_=filter_expr, page_size=limit))

        if not entries:
            return f"No Cloud Logging entries found matching filter: {filter_expr}."

        log_lines = []
        for e in entries[:limit]:
            ts = e.timestamp.isoformat() if e.timestamp else "N/A"
            payload = e.payload if e.payload else (e.text_payload or "No payload")
            log_lines.append(f"[{ts}] [{e.severity}]: {payload}")

        return "\n".join(log_lines)
    except Exception as exc:
        return f"Cloud Logging query note: {str(exc)}"


def inspect_local_codebase(file_path: str, start_line: int = 1, num_lines: int = 50) -> str:
    """Reads lines from a local source code file in the project repository.

    Args:
        file_path: Path to the source code file (relative to workspace or absolute).
        start_line: 1-indexed line number to start reading from. Defaults to 1.
        num_lines: Number of lines to read (1 to 200). Defaults to 50.

    Returns:
        Line-numbered snippet of the source file.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = file_path if os.path.isabs(file_path) else os.path.join(base_dir, file_path)

    if not os.path.exists(target_path):
        return f"File '{file_path}' does not exist at path '{target_path}'."

    if os.path.isdir(target_path):
        files = os.listdir(target_path)
        return f"Path '{file_path}' is a directory containing: {', '.join(files[:20])}"

    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), start_idx + num_lines)
        snippet = lines[start_idx:end_idx]

        output = [f"File: {file_path} (Lines {start_idx + 1} to {end_idx} of {len(lines)})"]
        for idx, line in enumerate(snippet, start=start_idx + 1):
            output.append(f"{idx:4d} | {line.rstrip()}")

        return "\n".join(output)
    except Exception as exc:
        return f"Error reading file '{file_path}': {str(exc)}"


def generate_incident_diagram(incident_id: str, title: str, service: str) -> str:
    """Generates a visual topology diagram card for an incident and uploads it to public Cloud Storage.

    Args:
        incident_id: Incident ID (e.g., 'INC-101').
        title: Short incident title.
        service: Name of the affected microservice.

    Returns:
        Public URL of the generated diagram image.
    """
    try:
        img = Image.new("RGB", (600, 300), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        draw.rectangle([10, 10, 590, 290], outline=(56, 189, 248), width=3)

        draw.text((30, 30), "OPSGUARD INCIDENT TOPOLOGY", fill=(56, 189, 248))
        draw.text((30, 65), f"{incident_id}: {title[:35]}", fill=(248, 113, 113))

        draw.rectangle([40, 120, 220, 200], outline=(148, 163, 184), fill=(30, 41, 59), width=2)
        draw.text((55, 150), "Client Gateway", fill=(226, 232, 240))

        draw.line([(220, 160), (360, 160)], fill=(248, 113, 113), width=3)
        draw.polygon([(360, 155), (370, 160), (360, 165)], fill=(248, 113, 113))
        draw.text((245, 140), "FAILED (500)", fill=(248, 113, 113))

        draw.rectangle([370, 120, 560, 200], outline=(248, 113, 113), fill=(69, 10, 10), width=3)
        draw.text((385, 145), f"[{service[:18]}]", fill=(254, 202, 202))
        draw.text((385, 170), "STATUS: ERROR", fill=(239, 68, 68))

        ts_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        draw.text((30, 255), f"Generated at: {ts_now} | OpsGuard AI Topology", fill=(148, 163, 184))

        tmp_path = f"/tmp/{incident_id}_diagram.png"
        img.save(tmp_path, format="PNG")

        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_path = f"diagrams/{incident_id}.png"
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(tmp_path, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
        return f"Incident topology diagram generated and published: {public_url}"
    except Exception as exc:
        return f"Error generating diagram: {str(exc)}"


def check_github_service_status() -> str:
    """Checks the real-time operational status of GitHub platform services (Actions, Git, API, Webhooks).

    Reads optional GITHUB_TOKEN environment variable if set.

    Returns:
        Summary string of current GitHub service operational statuses and active incidents.
    """
    url = "https://www.githubstatus.com/api/v2/summary.json"
    api_key = os.getenv("GITHUB_TOKEN", "")

    headers = {"User-Agent": "OpsGuard-AI-Agent"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        overall = data.get("status", {}).get("description", "Unknown")
        components = data.get("components", [])

        status_lines = [f"GitHub Platform Status: {overall}"]
        for comp in components:
            name = comp.get("name")
            status = comp.get("status")
            if name and status and not name.startswith("Visit"):
                status_lines.append(f"- {name}: {status.upper()}")

        incidents = data.get("incidents", [])
        if incidents:
            status_lines.append("\nActive GitHub Incidents:")
            for inc in incidents:
                status_lines.append(f"* [{inc.get('impact')}] {inc.get('name')}: {inc.get('shortlink')}")

        return "\n".join(status_lines)
    except Exception as exc:
        return f"Error checking GitHub status API: {str(exc)}"


def geocode_address(address: str) -> str:
    """Converts a street address or location name into geographic coordinates (lat/lng) using Google Geocoding API.

    Reads API key from GOOGLE_MAPS_API_KEY environment variable.

    Args:
        address: The address string or location query (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        Formatted string containing location name, coordinates (latitude, longitude), and place ID.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    encoded_address = urllib.parse.quote_plus(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        status = data.get("status")
        if status != "OK":
            return f"Geocoding API status response: {status}. Error message: {data.get('error_message', 'None')}"

        results = data.get("results", [])
        if not results:
            return f"No geocoding results found for address '{address}'."

        first_res = results[0]
        formatted_address = first_res.get("formatted_address")
        loc = first_res.get("geometry", {}).get("location", {})
        place_id = first_res.get("place_id")

        return (
            f"Geocoding Result for '{address}':\n"
            f"Formatted Address: {formatted_address}\n"
            f"Location: Lat {loc.get('lat')}, Lng {loc.get('lng')}\n"
            f"Place ID: {place_id}"
        )
    except Exception as exc:
        return f"Error executing Geocoding API call: {str(exc)}"


def find_nearby_places(latitude: float, longitude: float, place_type: str = "restaurant", radius: float = 1000.0) -> str:
    """Finds nearby points of interest around specified coordinates using Google Places API (New).

    Reads API key from GOOGLE_MAPS_API_KEY environment variable.

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g., 'restaurant', 'cafe', 'data_center', 'police'). Defaults to 'restaurant'.
        radius: Radius in meters (e.g., 1000.0). Defaults to 1000.0.

    Returns:
        Formatted string list of matching nearby places with name, address, and coordinates.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }

    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius),
            }
        },
    }

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius}m of ({latitude}, {longitude})."

        results = [f"Nearby Places of type '{place_type}' around ({latitude}, {longitude}):"]
        for p in places:
            display_name = p.get("displayName", {}).get("text", "Unknown Name")
            address = p.get("formattedAddress", "Unknown Address")
            loc = p.get("location", {})
            results.append(
                f"- Name: {display_name}\n"
                f"  Address: {address}\n"
                f"  Location: Lat {loc.get('latitude')}, Lng {loc.get('longitude')}"
            )

        return "\n".join(results)
    except Exception as exc:
        return f"Error executing Places API (New) call: {str(exc)}"


def generate_domain_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates an image for an architecture diagram or incident illustration using gemini-3.1-flash-lite-image in the global region.

    Saves the generated image as an ADK artifact and uploads image bytes directly to public Cloud Storage.

    Args:
        prompt: Detailed description of the image to generate (e.g., 'DevOps Incident Architecture Diagram showing microservices outage').
        tool_context: ADK tool execution context injected automatically.

    Returns:
        Public HTTPS URL of the uploaded image in Cloud Storage.
    """
    try:
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        part = response.candidates[0].content.parts[0]
        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"

        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
        ext = "jpg" if "jpeg" in mime_type else "png"
        filename = f"generated_diagram_{timestamp_str}.{ext}"

        # 1. Save artifact using tool_context
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to public GCS bucket (no local file write)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_path = f"generated_diagrams/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
        return public_url
    except Exception as exc:
        return f"Error generating domain image: {str(exc)}"
