# Copyright 2026 Google LLC
# Seed script for OpsGuard AI Firestore collection

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-0991ea70e49a"
COLLECTION_NAME = "incidents"

def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    incidents_ref = db.collection(COLLECTION_NAME)

    sample_incidents = [
        {
            "incident_id": "INC-101",
            "title": "ZeroDivisionError in SLA Metrics Calculator",
            "service": "analytics-service",
            "severity": "CRITICAL",
            "status": "OPEN",
            "stack_trace": "ZeroDivisionError: division by zero at app/metrics/calculator.py:42 in calculate_sla_percentage",
            "root_cause": "Missing zero-check guardrail when total_requests count is 0.",
            "suggested_patch": "if total_requests == 0:\n    return 100.0",
            "created_at": "2026-09-24T09:30:00Z",
        },
        {
            "incident_id": "INC-102",
            "title": "Database Connection Timeout during Spike Load",
            "service": "order-processor",
            "severity": "HIGH",
            "status": "INVESTIGATING",
            "stack_trace": "asyncio.exceptions.TimeoutError: Connection pool exhausted at db/pool.py:88",
            "root_cause": "Connection pool max_size set to 5, insufficient for 1000 concurrent checkout requests.",
            "suggested_patch": "max_connections = os.getenv('DB_POOL_MAX', 50)",
            "created_at": "2026-09-24T09:45:00Z",
        },
        {
            "incident_id": "INC-103",
            "title": "Unhandled KeyError in JWT Claims Parser",
            "service": "auth-gateway",
            "severity": "MEDIUM",
            "status": "RESOLVED",
            "stack_trace": "KeyError: 'tenant_id' at security/jwt.py:15 in extract_tenant_id",
            "root_cause": "Legacy guest tokens do not contain 'tenant_id' claim.",
            "suggested_patch": "tenant_id = claims.get('tenant_id', 'default_tenant')",
            "created_at": "2026-09-24T08:15:00Z",
        },
    ]

    for item in sample_incidents:
        doc_ref = incidents_ref.document(item["incident_id"])
        doc_ref.set(item)
        print(f"Seeded document: {item['incident_id']} -> {item['title']}")

    print("\nFirestore seeding complete!")

if __name__ == "__main__":
    seed_database()
