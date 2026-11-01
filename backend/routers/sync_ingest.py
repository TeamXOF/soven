"""Optional cloud archive receiver; dedicated sync authentication is required."""
import hashlib
import json
from fastapi import APIRouter, HTTPException
from database.schema import get_db_connection

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


@router.post("/ingest")
def ingest(body: dict):
    if body.get("kind") not in {"classic", "checkpoint", "dynamic"} or not isinstance(body.get("payload"), dict):
        raise HTTPException(422, "Invalid sync snapshot")
    if not all(isinstance(body.get(k), str) and 0 < len(body[k]) <= 128 for k in ["source_id", "record_id", "digest"]):
        raise HTTPException(422, "Invalid snapshot identity")
    encoded = json.dumps(body["payload"], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    if digest != body["digest"] or body["payload"].get("id") != body["record_id"]:
        raise HTTPException(422, "Snapshot integrity check failed")
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO sync_received(source_id,kind,record_id,digest,payload_json) VALUES (?,?,?,?,?)", (body["source_id"], body["kind"], body["record_id"], digest, encoded))
        conn.commit()
    return {"record_id": body["record_id"], "digest": digest}
