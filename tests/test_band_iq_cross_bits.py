"""BAND-IQ 013: image pieces really cross source custody into actual film cards."""
from __future__ import annotations
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import cv2

from bridge import band_iq as iq
from bridge import band_iq_cross_bits as cross
from bridge import band_iq_storytable as story
from bridge import band_iq_living_filmstrip as strip
from bridge import band_iq_donors as donors
from bridge import band_iq_film_loop as loop
from tests.test_band_iq_living_filmstrip import RealFrameTests

class GrabCrossTests(unittest.TestCase):
    def setUp(self):
        self.fixture=RealFrameTests(
            "test_bounded_sampling_never_pretends_omitted_windows_are_bad")
        self.fixture.setUp()
        f=self.fixture
        self.root=f.root
        self.paper={**f.paper,"audioSha256":donors.sha_file(f.song),
                    "toasterObservationSha256":iq.digest(f.obs)}
        self.plan=f.plan
        self.original=f.provisional
        self.obs=f.obs
        self.audio=f.song
        self.bit={
            "sourceAssetId":"p002",
            "grab":[0.1,0.1,0.45,0.45],
            "place":[0.35,0.25,0.4,0.4],
            "opacity":0.8,
        }
        self.form={
            "paperTraySha256":self.paper["paperTraySha256"],
            "operatorAttestationId":"explicit-human-bit-director",
            "decision":"SEAL_STORYTABLE",
            "shots":[
                {"shotId":"shot-A","sourceAssetId":"p001",
                 "focus":[.5,.5],"protectText":False,
                 "crosses":[self.bit]},
                {"shotId":"shot-B","sourceAssetId":"p002",
                 "focus":[.25,.75],"protectText":True},
            ],
            "preserveOriginals":True,"publish":False,
            "allowPaidProviders":False,"allowNetworkUpload":False,
        }
        self.preview_form={
            "paperTraySha256":self.paper["paperTraySha256"],
            "shotId":"shot-A",
            "left":{"sourceAssetId":"p001","focus":[.5,.5],
                    "protectText":False,"crosses":[]},
            "right":{"sourceAssetId":"p001","focus":[.5,.5],
                     "protectText":False,"crosses":[self.bit]},
            "compareOnly":True,
            "allowStorySeal":False,"allowMovieRender":False,
            "allowNetworkUpload":False,"allowPaidProviders":False,
            "allowPublication":False,
        }
    def tearDown(self):self.fixture.tearDown()

    def test_real_source_pixels_cross_without_replacing_either_owned_image(self):
        original_hashes=loop.exact_asset_bindings(self.original,self.root)
        receipt,frames=cross.preview(
            self.preview_form,self.paper,self.plan,self.original,
            self.obs,self.audio,self.root)
        self.assertEqual(receipt["schema"],cross.SCHEMA)
        self.assertEqual(len(frames),6)
        self.assertEqual(receipt["right"]["crosses"][0]["sourceAssetId"],"p002")
        self.assertNotEqual(receipt["left"]["frames"][1]["imageSha256"],
                            receipt["right"]["frames"][1]["imageSha256"])
        self.assertTrue(receipt["sourceDraftModified"] is False)
        self.assertFalse(receipt["humanStorySealed"])
        self.assertFalse(receipt["movieGenerated"])
        self.assertFalse(list(self.root.glob("crossed-bits/*")))
        self.assertEqual(loop.exact_asset_bindings(self.original,self.root),
                         original_hashes)
        image=cross.verified_image if hasattr(cross,"verified_image") else None
        self.assertEqual(hashlib.sha256(frames[("right",1)]).hexdigest(),
                         receipt["right"]["frames"][1]["imageSha256"])

    def test_explicit_story_seal_materializes_provenance_bound_image_and_reopens(self):
        with self.assertRaisesRegex(ValueError,"cross-bit"):
            story.author(self.form,self.paper,self.plan,self.original,self.root)
        cross.materialize_for_form(
            self.form,self.original["assets"],self.root,self.paper["stillSha256"])
        saved,cards=story.author(
            self.form,self.paper,self.plan,self.original,self.root)
        self.assertTrue(saved["shotAssignments"][0]["crosses"])
        self.assertEqual(saved["shotAssignments"][0]["borrowedSources"][0]["sourceSha256"],
                         self.paper["stillSha256"]["p002"])
        self.assertEqual(saved["shotAssignments"][0]["sourceSha256"],
                         self.paper["stillSha256"]["p001"])
        derived=self.root/"crossed-bits"/"shot-asset-0001.png"
        self.assertEqual(saved["shotAssignments"][0]["crossedImageSha256"],
                         donors.sha_file(derived))
        self.assertEqual(cards["assets"]["shot-asset-0001"]["path"],
                         "crossed-bits/shot-asset-0001.png")
        self.assertEqual(cv2.imread(str(derived)).shape[:2],(360,640))
        self.assertFalse(saved["renderAuthorized"])
        self.assertFalse(saved["published"])
        # Sealed derivative really is part of the existing VidMage renderer
        # and a source-pinned 011 filmstrip, not just a fake UI overlay.
        rendered=strip.build(saved,self.plan,cards,self.obs,self.audio,
                             self.root,self.root/"real-filmstrip")
        self.assertTrue(rendered["sampledActualRasterShots"][0]["frames"])
        with tempfile.TemporaryDirectory() as _:
            receipt_file=self.root/"sealed-story.json"
            cards_file=self.root/"sealed-cards.json"
            receipt_file.write_text(json.dumps(saved))
            cards_file.write_text(json.dumps(cards))
            reopened,unchanged=story.verified(
                receipt_file,cards_file,self.paper,self.plan,self.original,self.root)
            self.assertEqual(reopened,saved)
            self.assertEqual(unchanged,cards)
        self.assertFalse(list(self.root.glob("*.mp4")))

    def test_source_changed_or_rehashed_derived_composite_holds(self):
        cross.materialize_for_form(
            self.form,self.original["assets"],self.root,self.paper["stillSha256"])
        saved,cards=story.author(
            self.form,self.paper,self.plan,self.original,self.root)
        derived=self.root/"crossed-bits"/"shot-asset-0001.png"
        derived.write_bytes(derived.read_bytes()+b"forged")
        with self.assertRaisesRegex(ValueError,"cross-bit composition"):
            story.author(self.form,self.paper,self.plan,self.original,self.root)
        with self.assertRaisesRegex(ValueError,"existing sealed cross-bit pixels differ"):
            cross.materialize_for_form(
                self.form,self.original["assets"],self.root,self.paper["stillSha256"])

    def test_unowned_source_and_out_of_bounds_rectangles_refuse(self):
        patches=[
            {"sourceAssetId":"someone-elses-photo"},
            {"grab":[.85,.2,.3,.4]},
            {"place":[.6,.6,.7,.7]},
            {"grab":[0,0,0.01,.4]},
            {"opacity":1.5},
            {"opacity":"fully"},
            {"grab":[float("nan"),.1,.4,.4]},
            {"other":"inject"},
        ]
        for change in patches:
            bad={**self.bit,**change}
            form=copy.deepcopy(self.preview_form)
            form["right"]["crosses"]=[bad]
            with self.subTest(change=change),self.assertRaises(ValueError):
                cross.preview(form,self.paper,self.plan,self.original,self.obs,
                              self.audio,self.root)

    def test_no_autoseal_paid_provider_network_or_movie_authorization(self):
        for escalation in [
            {"allowStorySeal":True},{"allowMovieRender":True},
            {"allowNetworkUpload":True},{"allowPaidProviders":True},
            {"allowPublication":True},{"extra":"write disk from preview"},
        ]:
            form={**self.preview_form,**escalation}
            with self.subTest(escalation=escalation),self.assertRaises(ValueError):
                cross.preview(form,self.paper,self.plan,self.original,
                              self.obs,self.audio,self.root)
        too_many=copy.deepcopy(self.form)
        too_many["shots"][0]["crosses"]=[self.bit]*4
        with self.assertRaises(ValueError):
            cross.materialize_for_form(
                too_many,self.original["assets"],self.root,self.paper["stillSha256"])

if __name__=="__main__":unittest.main()
