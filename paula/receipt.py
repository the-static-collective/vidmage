"""Read-only adapter from Paula Pocket mobile receipts into Vidmage HOLD witnesses."""
import argparse
import hashlib
import json
from pathlib import Path

RECEIPT = "vidmage/paula-pocket-receipt/v1"
PROJECT = "vidmage/paula-pocket-project/v1"
EXPORT = "vidmage/paula-pocket-export/v1"
KINDS = {PROJECT, EXPORT}
FIELDS = {
    "STORYBOARD_APPROVED": {"project", "authority", "media_status"},
    "FLOW_HANDOFF_PREPARED": {"project_id", "duration_seconds", "prompt", "provider", "media_status"},
    "EXTERNAL_RENDER_REPORTED": {"project_id", "provider", "link", "review_note", "evidence_status", "claim"},
    "CREATOR_REVIEW_RECORDED": {"project_id", "link", "note", "evidence_status"},
}

class ReceiptRefused(ValueError):
    """Invalid or overclaimed input; do not grant any authority."""

def digest(value):
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def verify(obj):
    if not isinstance(obj, dict) or obj.get("format") not in KINDS:
        raise ReceiptRefused("Unknown export format")
    kind = obj["format"]
    project = obj.get("projectId" if kind == PROJECT else "project_id")
    if not isinstance(project, str) or not 1 <= len(project) <= 120:
        raise ReceiptRefused("Missing project identity")
    items = obj.get("receipts")
    if not isinstance(items, list) or len(items) > 200:
        raise ReceiptRefused("Receipt list missing or too large")
    previous = None
    events = []
    for i, receipt in enumerate(items):
        if not isinstance(receipt, dict) or set(receipt) != {"format", "event", "created_at", "previous_sha256", "payload", "sha256"}:
            raise ReceiptRefused(f"Unexpected fields in receipt {i}")
        event = receipt["event"]
        if receipt["format"] != RECEIPT or event not in FIELDS:
            raise ReceiptRefused(f"Unexpected format/event {i}")
        payload = receipt["payload"]
        if not isinstance(payload, dict) or set(payload) != FIELDS[event]:
            raise ReceiptRefused(f"Unexpected event payload {i}")
        sha = receipt["sha256"]
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise ReceiptRefused(f"Invalid content hash {i}")
        if receipt["previous_sha256"] != previous:
            raise ReceiptRefused(f"Broken receipt chain {i}")
        base = {k: receipt[k] for k in ("format", "event", "created_at", "previous_sha256", "payload")}
        if digest(base) != sha:
            raise ReceiptRefused(f"Tampered content {i}")
        actual_project = payload["project"].get("project_id") if event == "STORYBOARD_APPROVED" else payload["project_id"]
        if actual_project != project:
            raise ReceiptRefused(f"Project mismatch {i}")
        if event == "STORYBOARD_APPROVED":
            if payload["authority"] != "owner-approved-storyboard" or payload["media_status"] != "not-rendered":
                raise ReceiptRefused("Storyboarding cannot claim a film render")
            if not isinstance(payload["project"].get("story"), str) or not isinstance(payload["project"].get("scenes"), list):
                raise ReceiptRefused("Invalid storyboard content")
        if event == "FLOW_HANDOFF_PREPARED":
            if payload["provider"] != "Google Flow Music" or payload["media_status"] != "not-rendered":
                raise ReceiptRefused("Handoff cannot claim a render")
        if event == "EXTERNAL_RENDER_REPORTED" and payload["evidence_status"] != "owner-report-not-verified":
            raise ReceiptRefused("External output is an unverified owner report")
        if event == "CREATOR_REVIEW_RECORDED" and payload["evidence_status"] != "owner-observation":
            raise ReceiptRefused("Creator review remains an observation")
        previous = sha
        events.append({"event": event, "sha256": sha})
    return {
        "format": "vidmage/paula-import-witness/v1",
        "project_id": project,
        "intake_status": "HOLD",
        "source_format": kind,
        "receipts": events,
        "head_sha256": previous,
        "hash_scope": "content-and-chain-only",
        "external_video_verified": False,
        "creator_identity_verified": False,
        "render_authorized": False,
        "publication_authorized": False,
    }

def main():
    parser = argparse.ArgumentParser(description="Read-only Vidmage intake of Paula Pocket receipts")
    parser.add_argument("source")
    parser.add_argument("--witness", help="Create a local HOLD witness; existing file is never overwritten")
    args = parser.parse_args()
    data = Path(args.source).read_bytes()
    if len(data) > 3000000:
        parser.error("Too large")
    try:
        result = verify(json.loads(data))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        parser.error(f"REFUSED: {exc}")
    result["source_file_sha256"] = hashlib.sha256(data).hexdigest()
    if args.witness:
        target = Path(args.witness)
        with target.open("x", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
