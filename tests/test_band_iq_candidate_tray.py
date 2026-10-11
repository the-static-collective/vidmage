"""BAND-IQ 013: real pixel fragments, many candidate shots and signed film lineage."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import cv2

from bridge import band_iq as iq
from bridge import band_iq_candidate_tray as cross
from bridge import band_iq_contact_sheet as contact
from bridge import band_iq_storytable as story
from bridge import band_iq_donors as donors
from tests.test_band_iq_living_filmstrip import RealFrameTests

class SourceFragmentTests(unittest.TestCase):
    def setUp(self):
        self.demo=RealFrameTests("test_bounded_sampling_never_pretends_omitted_windows_are_bad")
        self.demo.setUp()
        self.root=self.demo.root
        self.original=self.demo.provisional
        self.paper={
            **self.demo.paper,
            "audioSha256":donors.sha_file(self.demo.song),
            "toasterObservationSha256":iq.digest(self.demo.obs)}
        self.bit={
            "sourceAssetId":"p002",
            "crop":[.20,.25,.30,.30],
            "place":[.45,.40,.35,.35],
            "opacity":.85,
        }
        self.shots=[
            {"shotId":"shot-A","sourceAssetId":"p001","focus":[.25,.75],
             "protectText":False,"crossBit":self.bit},
            {"shotId":"shot-B","sourceAssetId":"p002","focus":[.75,.20],
             "protectText":True},
        ]
        self.form={
            "paperTraySha256":self.paper["paperTraySha256"],
            "operatorAttestationId":"human-maker-of-a-small-crossed-picture",
            "decision":"SEAL_STORYTABLE","shots":self.shots,
            "preserveOriginals":True,"publish":False,
            "allowPaidProviders":False,"allowNetworkUpload":False}

    def tearDown(self):
        self.demo.tearDown()

    def test_grab_cross_deterministic_source_pixels_and_create_only_seal(self):
        originals={p.name:donors.sha_file(p)
                   for p in self.root.glob("source-*.png")}
        receipt,png=cross.compose("p001",self.bit,self.original["assets"],self.root)
        self.assertEqual(receipt["schema"],cross.SCHEMA)
        self.assertEqual(receipt["baseSourceSha256"],originals["source-001.png"])
        self.assertEqual(receipt["grabbedSourceSha256"],originals["source-002.png"])
        self.assertEqual(receipt["composedImageSha256"],hashlib.sha256(png).hexdigest())
        self.assertNotEqual(receipt["composedImageSha256"],originals["source-001.png"])
        self.assertEqual((cv2.imdecode(__import__("numpy").frombuffer(
            png,dtype=__import__("numpy").uint8),cv2.IMREAD_COLOR)).shape[:2],(360,640))
        self.assertFalse(list(self.root.glob("cross-bits/*")))
        # Actual author seal creates one owner-local DERIVATIVE, and its
        # source ID survives into the genuine 010 scene cards.
        record,cards=story.author(self.form,self.paper,self.demo.plan,
            self.original,self.root,materialize_bits=True)
        chosen=record["shotAssignments"][0]
        self.assertEqual(chosen["crossBit"],receipt)
        self.assertEqual(chosen["sourceSha256"],receipt["composedImageSha256"])
        self.assertEqual(cards["assets"]["shot-asset-0001"]["path"],
                         cross.derived_path(receipt))
        self.assertTrue((self.root/cross.derived_path(receipt)).is_file())
        self.assertEqual(donors.sha_file(self.root/cross.derived_path(receipt)),
                         receipt["composedImageSha256"])
        self.assertEqual(
            {p.name:donors.sha_file(p) for p in self.root.glob("source-*.png")},
            originals)
        same,cards2=story.author(self.form,self.paper,self.demo.plan,self.original,self.root)
        self.assertEqual(record,same)
        self.assertEqual(cards,cards2)
        self.assertEqual(cross.verify_derived(receipt,self.original["assets"],self.root),
                         self.root/cross.derived_path(receipt))
        # The original source cards remain exactly the original machine proposal.
        self.assertEqual(self.demo.provisional,self.original)

    def test_real_contact_sheet_sees_grabbed_pixels_without_sealing(self):
        base={
            "sourceAssetId":"p001","focus":[.5,.5],"protectText":False}
        right={**base,"crossBit":self.bit}
        form={
            "paperTraySha256":self.paper["paperTraySha256"],
            "shotId":"shot-A","left":base,"right":right,
            "compareOnly":True,"allowStorySeal":False,
            "allowMovieRender":False,"allowNetworkUpload":False,
            "allowPaidProviders":False,"allowPublication":False}
        record,pixels=contact.comparison(form,self.paper,self.demo.plan,
            self.original,self.demo.obs,self.demo.song,self.root)
        self.assertEqual(len(pixels),6)
        self.assertEqual(record["right"]["crossBitReceipt"]["schema"],cross.SCHEMA)
        self.assertNotEqual(record["left"]["frames"][1]["imageSha256"],
                            record["right"]["frames"][1]["imageSha256"])
        self.assertFalse(list(self.root.glob("cross-bits/*")))
        self.assertFalse(list(self.root.glob("*.mp4")))

    def test_changed_cross_source_or_derived_png_refuses_reopen(self):
        receipt,png=cross.compose("p001",self.bit,self.original["assets"],self.root)
        cross.materialize(receipt,png,self.root)
        composite=self.root/cross.derived_path(receipt)
        composite.write_bytes(composite.read_bytes()+b"forged-pixels")
        with self.assertRaisesRegex(ValueError,"missing or changed"):
            cross.verify_derived(receipt,self.original["assets"],self.root)
        with self.assertRaisesRegex(ValueError,"existing composed owner image changed"):
            cross.materialize(receipt,png,self.root)

    def test_bounded_fragments_cannot_request_unowned_paths_or_execution(self):
        candidates=[
            {"sourceAssetId":"a-secret-file"},
            {"crop":[.94,.1,.25,.3]},
            {"crop":[0,0,0,0]},
            {"place":[.1,.2,1.,1.]},
            {"opacity":0},
            {"opacity":float("nan")},
            {"unexpectedFilesystemPath":"../../private"},
        ]
        for patch in candidates:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                cross.checked_bit({**self.bit,**patch},self.original["assets"])
        with self.assertRaisesRegex(ValueError,"human local arrangement"):
            # The sealed author still requires the normal explicit seal contract.
            story.author({**self.form,"decision":"RENDER_NOW"},
                         self.paper,self.demo.plan,self.original,self.root)

    def test_multi_shot_candidate_snapshots_do_not_change_paper(self):
        original=copy.deepcopy(self.original)
        shots=cross.validate_draft_shots(self.shots,self.original["assets"])
        self.assertEqual(len(shots),2)
        self.assertIn("crossBit",shots[0])
        self.assertNotIn("crossBit",shots[1])
        self.assertEqual(self.original,original)
        with self.assertRaises(ValueError):
            cross.validate_draft_shots([{**shots[0],"publish":True}],
                                       self.original["assets"])
        with self.assertRaises(ValueError):
            cross.validate_draft_shots([{"shotId":"A","focus":[.5,.5]}],
                                       self.original["assets"])

if __name__=="__main__":
    unittest.main()
