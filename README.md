# 🛡️ OpsGuard AI — Autonomous DevOps & Incident Triage Agent

![OpsGuard AI Demo](demo.gif)

> 🎥 **Full Demo Video**: High-definition video with upbeat lo-fi audio track is included in the repository: [`opsguard_demo.mp4`](opsguard_demo.mp4)

**OpsGuard AI** is an autonomous SRE and DevOps incident triage agent built with the **Google Agent Development Kit (ADK)**. It empowers engineering teams to analyze Cloud Logging error streams, inspect local codebase source files, generate visual infrastructure topology diagrams, update incident states in Firestore, execute diagnostic code in a sandboxed Python environment, and persist cross-session operational memory using Vertex AI Memory Bank.

---

## 🛠️ Implemented Features & Tooling Architecture

All capabilities listed below are fully implemented in the [`app/`](app/) codebase:

### 1. 🧠 Memory & Persistent Context
- **Vertex AI Memory Bank Service**: Persists long-term operational memory, on-call engineer data, team preferences, and incident triage history across user chat sessions using `VertexAiMemoryBankService` and `PreloadMemoryTool`.

### 2. 🗄️ Database & Incident Management
- **Google Cloud Firestore**: Stores structured incident records in the `incidents` NoSQL collection. Supported operations:
  - `list_incidents`: Filter incidents by status (`OPEN`, `INVESTIGATING`, `RESOLVED`) or severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
  - `get_incident`: Retrieve detailed stack traces, root causes, and suggested patches for specific incident IDs.
  - `report_incident`: Store new incident reports with timestamps and microservice metadata.
  - `update_incident_status`: Update incident states and add resolution notes.

### 3. 🔍 Observability & Repository Inspection
- **Google Cloud Logging**: Query live error logs and runtime exception streams from GCP resources via `query_cloud_logs`.
- **Local Repository Inspector**: Inspect source code files line-by-line within the project repository to identify root causes using `inspect_local_codebase`.

### 4. 🎨 Visual Media & Storage
- **Google Cloud Storage (GCS)**: Stores generated visual assets and topology diagrams in public GCS bucket `opsguard-assets-0991ea70e49a`.
- **System Topology Diagrams**: Generates system architecture and blast radius diagrams using Pillow and publishes them to GCS (`generate_incident_diagram`).
- **Gemini / Imagen 3 Image Generation**: Generates AI domain images using `gemini-3.1-flash-lite-image` and uploads them to Cloud Storage (`generate_domain_image`).

### 5. 💻 Code Execution & UI Rendering
- **Agent Engine Sandbox Code Executor**: Safely executes Python code snippets for calculations, data processing, or SLA calculations in a sandbox environment (`AgentEngineSandboxCodeExecutor`).
- **A2UI (Agent to User Interface)**: Renders dynamic, structured rich cards (`Card`, `Column`, `Row`, `Text`, `Image`) with A2UI v0.8 schema management and callbacks (`A2uiSchemaManager`, `a2ui_callback`).

### 6. 🌐 External Integrations
- **GitHub Platform Status API**: Queries live operational status for GitHub Actions, Git, API, and Webhooks (`check_github_service_status`).
- **Google Maps Geocoding & Places (New) API**: Converts server data center addresses into geographic coordinates (`geocode_address`) and locates nearby facilities (`find_nearby_places`).

---

## 📋 Status of Planned Features

| Feature | Status | Notes |
| :--- | :---: | :--- |
| **Vertex AI Memory Bank** | ✅ Implemented | Wired in `app/agent.py` via `VertexAiMemoryBankService` |
| **Firestore Incident Catalog** | ✅ Implemented | Wired in `app/tools.py` via `google-cloud-firestore` |
| **Cloud Logging Querying** | ✅ Implemented | Wired in `app/tools.py` via `google-cloud-logging` |
| **Topology & Image Generation** | ✅ Implemented | Wired in `app/tools.py` via PIL, GCS & `gemini-3.1-flash-lite-image` |
| **A2UI Dynamic Cards** | ✅ Implemented | Wired in `app/agent.py` & `app/a2ui_utils.py` |
| **Agent Engine Code Sandbox** | ✅ Implemented | Wired in `app/agent.py` via `AgentEngineSandboxCodeExecutor` |
| **GitHub Status & Google Maps** | ✅ Implemented | Wired in `app/tools.py` |
| **Cloud Trace Integration** | 🚧 Planned | Stretch goal listed in project brief; not yet implemented |

---

## 🚀 Local Setup & Execution Instructions

### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`)
- Configured GCP Project with Vertex AI and Firestore APIs enabled

### 1. Install Dependencies
Navigate to the `frontend/` directory and install required Python packages:
```bash
cd frontend
pip install -r requirements.txt
```

### 2. Set Environment Variables
Export the required environment variables pointing to your Agent Engine resource and directory:
```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"
```

### 3. Start the Web Server
Launch the application backend & proxy server locally:
```bash
python main.py
```
The server will start on port `8080`. Open your web browser to `localhost` on port `8080` to interact with the OpsGuard AI agent interface.
