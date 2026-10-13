import copy
import hashlib
import json
import unittest
from paula.receipt import (
    validate, digest, ReceiptRefused, EXPORT_KIND, PROJECT_KIND, RECEIPT_KIND,
)

PROJECT='pocket-0123456789abcdef'

def envelope(events=('STORYBOARD_APPROVED', 'FLOW_HANDOFF_PREPARED', 'EXTERNAL_RENDER_REPORTED', 'CREATOR_REVIEW_RECORDED')):
    payloads={
        'STORYBOARD_APPROVED': {'project': {'project_id': PROJECT, 'title': 'An Imaginary Film', 'duration_seconds': 20, 'story': 'A lantern lights up.', 'scenes': [{'id': 'shot-1', 'time': '0-20', 'action': 'A lantern glows'}]}, 'authority': 'owner-approved-storyboard', 'media_status': 'not-rendered'},
        'FLOW_HANDOFF_PREPARED': {'project_id': PROJECT, 'duration_seconds': 20, 'prompt': 'A lantern glows', 'provider': 'Google Flow Music', 'media_status': 'not-rendered'},
        'EXTERNAL_RENDER_REPORTED': {'project_id': PROJECT, 'provider': 'Google Flow Music', 'link': '', 'review_note': 'A nice glow', 'evidence_status': 'owner-report-not-verified', 'claim': 'Owner reports attempting or generating an external video; content not verified by Vidmage.'},
        'CREATOR_REVIEW_RECORDED': {'project_id': PROJECT, 'link': '', 'note': 'I like it', 'evidence_status': 'owner-observation'},
    }
    result=[];prev=None
    for event in events:
        r={'format':RECEIPT_KIND,'event':event,'created_at':'2026-10-13T14:00:00.000Z','previous_sha256':prev,'payload':payloads[event]}
        r['sha256']=digest(r);prev=r['sha256'];result.append(r)
    return {'format': EXPORT_KIND, 'project_id':PROJECT, 'receipts':result}

class ReceiptTests(unittest.TestCase):
    def test_all_events_held_only(self):
        outcome=validate(envelope())
        self.assertEqual(outcome['intake_status'],'HOLD')
        self.assertEqual(outcome['receipt_count'],4)
        self.assertIn('provider-output',outcome['not_verified'])
        self.assertEqual(len(outcome['head_sha256']),64)
    def test_project_backup(self):
        x=envelope(); x['format']=PROJECT_KIND;x['projectId']=x.pop('project_id')
        self.assertEqual(validate(x)['source_kind'],PROJECT_KIND)
    def test_empty_receipts(self):
        x=envelope(); x['receipts']=[]
        self.assertEqual(validate(x)['receipt_count'],0)
    def test_content_tampered(self):
        x=envelope(); x['receipts'][0]['payload']['project']['story']='Different story'
        with self.assertRaises(ReceiptRefused):validate(x)
    def test_chain_reordered(self):
        x=envelope();x['receipts'].reverse()
        with self.assertRaises(ReceiptRefused):validate(x)
    def test_media_overclaim_even_with_rehash(self):
        x=envelope();x['receipts']=x['receipts'][:1];r=x['receipts'][0];r['payload']['media_status']='rendered';r['sha256']=digest({k:v for k,v in r.items() if k!='sha256'})
        with self.assertRaises(ReceiptRefused):validate(x)
    def test_event_extra_authority_refused(self):
        x=envelope();x['receipts']=x['receipts'][:1];r=x['receipts'][0];r['payload']['allow_publish']=True;r['sha256']=digest({k:v for k,v in r.items() if k!='sha256'})
        with self.assertRaises(ReceiptRefused):validate(x)
    def test_project_swap_refused(self):
        x=envelope();x['project_id']='other'
        with self.assertRaises(ReceiptRefused):validate(x)

if __name__=='__main__':unittest.main()
