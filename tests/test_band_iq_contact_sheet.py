"""BAND-IQ 012: six authentic temporary raster frames, zero changed film artifacts."""
import copy
import hashlib
import unittest
from pathlib import Path

from bridge import band_iq as iq
from bridge import band_iq_contact_sheet as contact
from bridge import band_iq_donors as donors
from tests.test_band_iq_living_filmstrip import RealFrameTests


class ContactSheetTests(unittest.TestCase):
    def setUp(self):
        # Reuse an actual decoded, differently patterned owned-picture fixture.
        self.fixture=RealFrameTests("test_bounded_sampling_never_pretends_omitted_windows_are_bad")
        self.fixture.setUp()
        source=self.fixture
        self.plan=source.plan
        self.cards=source.provisional
        self.paper={
            **source.paper,
            "audioSha256":donors.sha_file(source.song),
            "toasterObservationSha256":iq.digest(source.obs),
        }
        self.observation=source.obs
        self.audio=source.song
        self.root=source.root
        self.form={
            "paperTraySha256":self.paper["paperTraySha256"],
            "shotId":"shot-A",
            "left":{"sourceAssetId":"p001","focus":[.5,.5],"protectText":False},
            "right":{"sourceAssetId":"p002","focus":[.25,.85],"protectText":True},
            "compareOnly":True,"allowStorySeal":False,
            "allowMovieRender":False,"allowNetworkUpload":False,
            "allowPaidProviders":False,"allowPublication":False,
        }

    def tearDown(self):
        self.fixture.tearDown()

    def look(self,form=None):
        return contact.comparison(form or self.form,self.paper,self.plan,
                                  self.cards,self.observation,self.audio,self.root)

    def test_actual_three_frame_a_b_comparison_never_changes_originals(self):
        original=copy.deepcopy(self.cards)
        photo_hashes={p.name:donors.sha_file(p)
                      for p in self.root.glob("source-*.png")}
        receipt,photos=self.look()
        self.assertEqual(receipt["schema"],contact.SCHEMA)
        self.assertEqual(receipt["shotId"],"shot-A")
        self.assertEqual(receipt["shotIndex"],0)
        self.assertEqual(receipt["shotStart"],0.)
        self.assertEqual(receipt["shotEnd"],2.)
        self.assertEqual(len(photos),6)
        self.assertEqual(set(photos),
                         {("left",0),("left",1),("left",2),
                          ("right",0),("right",1),("right",2)})
        self.assertNotEqual(
            receipt["left"]["frames"][1]["imageSha256"],
            receipt["right"]["frames"][1]["imageSha256"])
        self.assertEqual(
            contact.verified_image(receipt,photos,receipt["comparisonSha256"],
                                   "right",2),
            photos[("right",2)])
        self.assertEqual(
            hashlib.sha256(photos[("left",0)]).hexdigest(),
            receipt["left"]["frames"][0]["imageSha256"])
        self.assertEqual(
            [x["nativeFrameIndex"] for x in receipt["left"]["frames"]],
            [3,11,20])
        self.assertEqual(receipt["left"]["sourceSha256"],
                         self.paper["stillSha256"]["p001"])
        self.assertEqual(receipt["right"]["sourceSha256"],
                         self.paper["stillSha256"]["p002"])
        self.assertEqual(self.cards,original)
        self.assertEqual(
            {p.name:donors.sha_file(p) for p in self.root.glob("source-*.png")},
            photo_hashes)
        self.assertFalse(receipt["sourceDraftModified"])
        self.assertFalse(receipt["humanStorySealed"])
        self.assertFalse(receipt["movieGenerated"])
        self.assertFalse(receipt["published"])
        self.assertIsNone(receipt["artisticJudgment"])
        self.assertFalse(list(self.root.rglob("*.mp4")))
        self.assertFalse(list(self.root.rglob("*contact*")))
        self.assertEqual(
            iq.digest({k:v for k,v in receipt.items() if k!="comparisonSha256"}),
            receipt["comparisonSha256"])

    def test_two_independent_focal_points_one_owned_photo(self):
        two=copy.deepcopy(self.form)
        two["right"]={
            "sourceAssetId":"p001","focus":[.0,1.0],"protectText":False}
        receipt,photos=self.look(two)
        self.assertEqual(receipt["left"]["sourceSha256"],
                         receipt["right"]["sourceSha256"])
        self.assertNotEqual(
            receipt["left"]["frames"][1]["imageSha256"],
            receipt["right"]["frames"][1]["imageSha256"])
        self.assertEqual(receipt["right"]["focus"],[0.,1.])
        self.assertFalse(receipt["movieGenerated"])

    def test_missing_owned_picture_or_shot_and_escalated_permission_refused(self):
        variants=[
            {"allowStorySeal":True},
            {"allowMovieRender":True},
            {"allowPublication":True},
            {"allowPaidProviders":True},
            {"allowNetworkUpload":True},
            {"compareOnly":False},
            {"paperTraySha256":"0"*64},
            {"shotId":"an unowned shot"},
            {"left":{**self.form["left"],"sourceAssetId":"unowned-photo"}},
            {"right":{**self.form["right"],"focus":[float("nan"),.8]}},
            {"right":{**self.form["right"],"focus":[1.2,.8]}},
            {"right":{**self.form["right"],"protectText":"sure"}},
            {"invented":"publish while comparing"},
        ]
        for patch in variants:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                self.look({**self.form,**patch})

    def test_rehashed_pixel_or_wrong_comparison_identity_refused(self):
        record,frames=self.look()
        with self.assertRaisesRegex(ValueError,"no active matching"):
            contact.verified_image(record,frames,"0"*64,"right",1)
        with self.assertRaises(ValueError):
            contact.verified_image(record,frames,record["comparisonSha256"],"right",3)
        forged=dict(frames)
        forged[("right",0)]=frames[("right",0)]+b"tampered"
        with self.assertRaisesRegex(ValueError,"frame changed"):
            contact.verified_image(record,forged,record["comparisonSha256"],"right",0)

    def test_original_sources_moved_means_hold(self):
        (self.root/"source-001.png").write_bytes(b"corrupt original")
        with self.assertRaises((ValueError,RuntimeError)):
            self.look()

    def test_same_local_draft_can_preview_again_without_creating_authority(self):
        first,pixels=self.look()
        again,more=self.look()
        self.assertEqual(first,again)
        self.assertEqual(pixels,more)
        self.assertEqual(first["left"]["sourceAssetId"],"p001")
        self.assertEqual(first["right"]["sourceAssetId"],"p002")
        self.assertFalse(first["humanStorySealed"])
        self.assertFalse(first["movieGenerated"])
        self.assertFalse(list(self.root.rglob("*.json")))

if __name__=="__main__":
    unittest.main()
