"""Verify owner-exported Paula Pocket receipts before any Vidmage admission.

No media is fetched and no local render, provider operation, or creative decision
is authorized by these data. SHA-256 provides integrity, NOT an owner signature.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RECEIPT_KIND = 'vidmage/paula-pocket-receipt/v1'
PROJECT_KIND = 'vidmage/paula-pocket-project/v1'
EXPORT_KIND = 'vidmage/paula-pocket-export/v1'
WITNESS_KIND = 'vidmage/paula-import-witness/v1'
EVENTS = {
    'STORYBOARD_APPROVED', 'FLOW_HANDOFF_PREPARED',
    'EXTERNAL_RENDER_REPORTED', 'CREATOR_REVIEW_RECORDED',
}
EVENT_FIELDS = {
    'STORYBOARD_APPROVED': {'project', 'authority', 'media_status'},
    'FLOW_HANDOFF_PREPARED': {'project_id', 'duration_seconds', 'prompt', 'provider', 'media_status'},
    'EXTERNAL_RENDER_REPORTED': {'project_id', 'provider', 'link', 'review_note', 'evidence_status', 'claim'},
    'CREATOR_REVIEW_RECORDED': {'project_id', 'link', 'note', 'evidence_status'},
}
MAX_BYTES = 3_000_000
MAX_RECEIPTS = 200

class ReceiptRefused(ValueError):
    """Payload is not a recognized, intact Paula receipt chain."""


def canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(data: Any) -> str:
    return hashlib.sha256(canonical(data)).hexdigest()


def _str(value: Any, field: str, limit: int = 200_000) -> str:
    if not isinstance(value, str) or len(value) > limit:
        raise ReceiptRefused(f'Invalid {field}')
    return value


def read_file(path: str | Path) -> tuple[dict[str, Any], bytes]:
    source = Path(path)
    if not source.is_file() or source.stat().st_size > MAX_BYTES:
        raise ReceiptRefused('File not found or too large')
    data = source.read_bytes()
    try:
        envelope = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReceiptRefused('Not a valid UTF-8 JSON export') from exc
    if not isinstance(envelope, dict):
        raise ReceiptRefused('Top level must be an object')
    return envelope, data


def validate(envelope: dict[str, Any]) -> dict[str, Any]:
    kind = envelope.get('format')
    if kind not in {PROJECT_KIND, EXPORT_KIND}:
        raise ReceiptRefused('Unrecognized source format')
    project_id = _str(envelope.get('projectId' if kind == PROJECT_KIND else 'project_id'), 'project id', 120)
    receipts = envelope.get('receipts')
    if not isinstance(receipts, list) or len(receipts) > MAX_RECEIPTS:
        raise ReceiptRefused('Receipts absent or over limit')
    last = None
    imported = []
    for index, item in enumerate(receipts):
        if not isinstance(item, dict) or set(item) != {
            'format', 'event', 'created_at', 'previous_sha256', 'payload', 'sha256'
        }:
            raise ReceiptRefused(f'Invalid receipt fields at {index}')
        if item['format'] != RECEIPT_KIND or item['event'] not in EVENTS:
            raise ReceiptRefused(f'Invalid event at {index}')
        if not isinstance(item['payload'], dict) or set(item['payload']) != EVENT_FIELDS[item['event']]:
            raise ReceiptRefused(f'Invalid event payload at {index}')
        _str(item['created_at'], 'timestamp', 40)
        sha = _str(item['sha256'], 'digest', 64)
        if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ReceiptRefused(f'Invalid digest syntax at {index}')
        if item['previous_sha256'] != last:
            raise ReceiptRefused(f'Broken ancestry at {index}')
        check = {field: item[field] for field in ('format', 'event', 'created_at', 'previous_sha256', 'payload')}
        if sha != digest(check):
            raise ReceiptRefused(f'Content mismatch at {index}')
        payload = item['payload']
        actual_id = payload['project'].get('project_id') if item['event'] == 'STORYBOARD_APPROVED' else payload['project_id']
        if actual_id != project_id:
            raise ReceiptRefused(f'Different project at {index}')
        if item['event'] == 'STORYBOARD_APPROVED':
            if payload['media_status'] != 'not-rendered' or payload['authority'] != 'owner-approved-storyboard':
                raise ReceiptRefused('Story approval cannot claim actual rendering')
            project = payload['project']
            if not isinstance(project.get('story'), str) or not isinstance(project.get('scenes'), list):
                raise ReceiptRefused('Incomplete storyboard')
        elif item['event'] == 'FLOW_HANDOFF_PREPARED':
            if payload['media_status'] != 'not-rendered' or payload['provider'] != 'Google Flow Music':
                raise ReceiptRefused('Handoff overstates provider or media status')
        elif item['event'] == 'EXTERNAL_RENDER_REPORTED':
            if payload['evidence_status'] != 'owner-report-not-verified':
                raise ReceiptRefused('Owner report cannot claim independently verified output')
        elif item['event'] == 'CREATOR_REVIEW_RECORDED':
            if payload['evidence_status'] != 'owner-observation':
                raise ReceiptRefused('Owner review must stay owner observation')
        last = sha
        imported.append({'event': item['event'], 'sha256': sha, 'created_at': item['created_at']})
    return {
        'format': WITNESS_KIND,
        'project_id': project_id,
        'intake_status': 'HOLD',
        'receipt_count': len(imported),
        'head_sha256': last,
        'source_kind': kind,
        'events': imported,
        'verified': 'local-content-digest-and-chain-only',
        'not_verified': ['provider-output', 'media-bytes', 'creator-identity', 'copyright-rights'],
        'authority': 'no-render-no-publication-no-owner-decision',
    }


def main() -> int:
    p = argparse.ArgumentParser(description='Read-only verification of an exported Paula Pocket receipt chain')
    p.add_argument('path', help='A user-exported Paula .json project or receipt trail')
    p.add_argument('--write-witness', type=Path, help='Optionally save a bounded local HOLD witness JSON')
    args = p.parse_args()
    try:
        obj, raw = read_file(args.path)
        result = validate(obj)
    except (OSError, ReceiptRefused) as exc:
        p.exit(2, f'REFUSED: {exc}\n')
    result['export_bytes_sha256'] = hashlib.sha256(raw).hexdigest()
    if args.write_witness:
        if args.write_witness.exists():
            p.exit(2, 'REFUSED: Witness already exists; no overwrite\n')
        args.write_witness.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
