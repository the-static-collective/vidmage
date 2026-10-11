"""BAND-IQ 010: author per-occurrence assignments and genuinely timed source witness."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from bridge import band_iq as iq
from bridge import band_iq_film_loop as loop
from bridge import band_iq_storytable as story
from bridge import band_iq_front_porch as porch

class StorytableSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        for i in range(2):
            im=Image.new("RGB",(640,360),
                         (120+i*70,40+i*80,100+i*60))
            im.save(self.root/("source-%03d.png"%(i+1)))
        self.plan={
            "schema":"haunted-blender/paper-director-plan/v1",
            "durationSeconds":4.0,
            "shots":[
                {"id":"shot-A","start":0.0,"end":2.0},
                {"id":"shot-B","start":2.0,"end":4.0},
            ],
        }
        self.cards={
            "schema":"vidmage/editorial-scene-cards/v1",
            "status":"proposal-only",
            "assets":{
                "p001":{"path":"source-001.png","mode":"subject","focus":[.5,.5]},
                "p002":{"path":"source-002.png","mode":"subject","focus":[.5,.5]},
            },
            "shots":[{"shotId":"shot-A","assetId":"p001","kineticSafe":False},
                     {"shotId":"shot-B","assetId":"p002","kineticSafe":False}],
        }
        self.prepared={
            "paperTraySha256":"d"*64,
            "paperPlanSha256":iq.digest(self.plan),
            "sceneCardsSha256":iq.digest(self.cards),
            "stillSha256":loop.exact_asset_bindings(self.cards,self.root),
        }
        self.form={
            "paperTraySha256":self.prepared["paperTraySha256"],
            "operatorAttestationId":"one-human-authored-story",
            "decision":"SEAL_STORYTABLE",
            "shots":[
                {"shotId":"shot-A","sourceAssetId":"p002",
                 "focus":[.2,.8],"protectText":True},
                {"shotId":"shot-B","sourceAssetId":"p002",
                 "focus":[.75,.3],"protectText":False},
            ],
            "preserveOriginals":True,"publish":False,
            "allowPaidProviders":False,"allowNetworkUpload":False,
        }
    def tearDown(self):
        self.tmp.cleanup()
    def make(self,form=None):
        return story.author(form or self.form,self.prepared,
                            self.plan,self.cards,self.root)

    def test_same_owned_picture_can_be_framed_differently_per_song_window(self):
        original_cards=copy.deepcopy(self.cards)
        receipt,authored=self.make()
        self.assertEqual(self.cards,original_cards)
        self.assertEqual([x["shotId"] for x in authored["shots"]],
                         ["shot-A","shot-B"])
        a,b=(authored["assets"][x["assetId"]] for x in authored["shots"])
        self.assertEqual(a["path"],b["path"])
        self.assertEqual(a["path"],"source-002.png")
        self.assertEqual(a["focus"],[.2,.8])
        self.assertEqual(b["focus"],[.75,.3])
        self.assertEqual(a["mode"],"protect-text")
        self.assertEqual(b["mode"],"subject")
        self.assertEqual([(x["start"],x["end"])
                          for x in receipt["shotAssignments"]],
                         [(0.0,2.0),(2.0,4.0)])
        self.assertFalse(receipt["renderAuthorized"])
        self.assertFalse(receipt["published"])
        self.assertFalse(receipt["humanKeep"])
        self.assertEqual(receipt["authoredCardsSha256"],iq.digest(authored))
        self.assertNotEqual(receipt["originalProvisionalCardsSha256"],
                            receipt["authoredCardsSha256"])

    def test_exact_receipt_reopens_and_refuses_tampered_frames(self):
        receipt,cards=self.make()
        seal=porch.write_exclusive(self.root/"seal.json",receipt)
        recorded=porch.write_exclusive(self.root/"authored.json",cards)
        self.assertEqual(story.verified(seal,recorded,self.prepared,
                                       self.plan,self.cards,self.root)[0],receipt)
        bad=copy.deepcopy(cards)
        bad["assets"]["shot-asset-0002"]["focus"]=[.2,.1]
        recorded.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError,"source-pinned human storytable or sealed snapshot changed"):
            story.verified(seal,recorded,self.prepared,self.plan,self.cards,self.root)
        recorded.write_text(json.dumps(cards))
        (self.root/"source-002.png").write_bytes(b"source was swapped")
        with self.assertRaisesRegex(ValueError,"source bytes changed"):
            story.verified(seal,recorded,self.prepared,self.plan,self.cards,self.root)

    def test_unapproved_images_invalid_frames_and_extra_keys_refuse(self):
        changes=[
            {"shots":[{**self.form["shots"][0],"sourceAssetId":"never-uploaded"},
                       self.form["shots"][1]]},
            {"shots":[{**self.form["shots"][0],"focus":[1.4,.2]},
                       self.form["shots"][1]]},
            {"shots":[{**self.form["shots"][0],"protectText":"yes"},
                       self.form["shots"][1]]},
            {"shots":self.form["shots"][:1]},
            {"shots":[{**self.form["shots"][0],"shotId":"shot-B"},
                       self.form["shots"][1]]},
            {"publish":True},
            {"allowPaidProviders":True},
            {"allowNetworkUpload":True},
            {"decision":"RENDER_EVERYTHING"},
            {"unexpected":"auto arrange"},
        ]
        for patch in changes:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                self.make({**self.form,**patch})

    def test_protect_text_does_not_claim_camera_or_publication_permission(self):
        result,cards=self.make()
        self.assertTrue(all(x["kineticSafe"] is False for x in cards["shots"]))
        self.assertNotIn("cinematicSelection",cards)
        self.assertNotIn("cameraMode",result)
        self.assertEqual(result["status"],"owner-authored-before-film")
        self.assertEqual(result["originalPaperPlanSha256"],iq.digest(self.plan))
        self.assertNotIn("human-selected-movie",result["laws"])

if __name__=="__main__":
    unittest.main()
