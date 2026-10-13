import copy
import unittest
from paula.receipt import verify, digest, ReceiptRefused, RECEIPT, EXPORT

PROJECT = "pocket-test"
def chain():
    payloads = [
        ("STORYBOARD_APPROVED", {"project": {"project_id": PROJECT, "story": "A kind encounter", "scenes": [{"id": "shot-1"}]}, "authority": "owner-approved-storyboard", "media_status": "not-rendered"}),
        ("FLOW_HANDOFF_PREPARED", {"project_id": PROJECT, "duration_seconds": 20, "prompt": "A kind encounter", "provider": "Google Flow Music", "media_status": "not-rendered"}),
        ("EXTERNAL_RENDER_REPORTED", {"project_id": PROJECT, "provider": "Google Flow Music", "link": "", "review_note": "Good", "evidence_status": "owner-report-not-verified", "claim": "Unverified report"}),
        ("CREATOR_REVIEW_RECORDED", {"project_id": PROJECT, "link": "", "note": "Good", "evidence_status": "owner-observation"}),
    ]
    previous = None
    items = []
    for event,payload in payloads:
        obj = {"format": RECEIPT, "event": event, "created_at": "2026-10-13T15:00:00.000Z", "previous_sha256": previous, "payload": payload}
        obj["sha256"] = digest(obj)
        previous = obj["sha256"]
        items.append(obj)
    return {"format": EXPORT, "project_id": PROJECT, "receipts": items}

class PocketTests(unittest.TestCase):
    def test_valid_receipts_remain_hold(self):
        w=verify(chain())
        self.assertEqual(w["intake_status"], "HOLD")
        self.assertFalse(w["external_video_verified"])
        self.assertFalse(w["publication_authorized"])
    def test_tampered_story_refused(self):
        obj=chain()
        obj["receipts"][0]["payload"]["project"]["story"]="Altered"
        with self.assertRaises(ReceiptRefused):verify(obj)
    def test_reordered_chain_refused(self):
        obj=chain();obj["receipts"].reverse()
        with self.assertRaises(ReceiptRefused):verify(obj)
    def test_rehashed_overclaim_refused(self):
        obj=chain();obj["receipts"]=obj["receipts"][:1]
        r=obj["receipts"][0];r["payload"]["media_status"]="rendered"
        r["sha256"]=digest({k:v for k,v in r.items() if k!="sha256"})
        with self.assertRaises(ReceiptRefused):verify(obj)
    def test_project_mismatch_refused(self):
        obj=chain();obj["project_id"]="unrelated"
        with self.assertRaises(ReceiptRefused):verify(obj)
    def test_added_authority_refused(self):
        obj=chain();obj["receipts"]=obj["receipts"][:1]
        r=obj["receipts"][0];r["payload"]["allow_publication"]=True
        r["sha256"]=digest({k:v for k,v in r.items() if k!="sha256"})
        with self.assertRaises(ReceiptRefused):verify(obj)

if __name__ == "__main__":
    unittest.main()
