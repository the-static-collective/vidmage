"""BAND-IQ 011: evidence-exact real raster stills, sketch not movie."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import cv2
from PIL import Image

from bridge import band_iq as iq
from bridge import band_iq_donors as donors
from bridge import band_iq_living_filmstrip as strip
from bridge import band_iq_storytable as story
from bridge import band_iq_film_loop as loop
from bridge import scene_card_film as film

class RealFrameTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        for i in (1,2):
            src=Image.new("RGB",(640,360),(i*71,i*42+14,i*48))
            for y in range(0,360,17):
                for x in range(0,640,19):
                    src.putpixel((x,y),((x*i*7)%255,(y*i*11)%255,(i*39)%255))
            src.save(self.root/f"source-{i:03d}.png")
        self.plan={
            "schema":"haunted-blender/paper-director-plan/v1",
            "durationSeconds":4.0,
            "shots":[{"id":"shot-A","start":0.,"end":2.},
                     {"id":"shot-B","start":2.,"end":4.}],
        }
        self.provisional={
            "schema":"vidmage/editorial-scene-cards/v1",
            "status":"proposal-only",
            "assets":{
                "p001":{"path":"source-001.png","mode":"subject","focus":[.5,.5]},
                "p002":{"path":"source-002.png","mode":"subject","focus":[.5,.5]},
            },
            "shots":[{"shotId":"shot-A","assetId":"p001","kineticSafe":False},
                     {"shotId":"shot-B","assetId":"p002","kineticSafe":False}],
        }
        self.paper={
            "paperPlanSha256":iq.digest(self.plan),
            "sceneCardsSha256":iq.digest(self.provisional),
            "paperTraySha256":"a"*64,
            "stillSha256":loop.exact_asset_bindings(self.provisional,self.root),
        }
        form={
            "paperTraySha256":self.paper["paperTraySha256"],
            "operatorAttestationId":"human-source-director",
            "decision":"SEAL_STORYTABLE",
            "shots":[
                {"shotId":"shot-A","sourceAssetId":"p002",
                 "focus":[.15,.85],"protectText":True},
                {"shotId":"shot-B","sourceAssetId":"p002",
                 "focus":[.7,.25],"protectText":False},
            ],
            "preserveOriginals":True,"publish":False,
            "allowPaidProviders":False,"allowNetworkUpload":False,
        }
        self.seal,self.cards=story.author(
            form,self.paper,self.plan,self.provisional,self.root)
        self.song=self.root/"song.wav"
        self.song.write_bytes(b"synthetic wav ownership bytes only")
        self.obs={
            "schema":"vidmage/toaster-lbranch-observation/v1",
            "sourceAudioSha256":donors.sha_file(self.song),
            "laneBank":{
                "schema":"haunted-toaster/lane-bank/v1",
                "lanes":[{"id":"raw-energy-envelope","knots":[
                    {"atSeconds":0.,"value":.15},
                    {"atSeconds":4.,"value":.65}]}],
            },
        }
        self.destination=self.root/"filmstrip"

    def tearDown(self):
        self.tmp.cleanup()

    def consent(self,**replace):
        return {
            "storySha256":self.seal["storySha256"],
            "makeLocalSketch":True,"acknowledgeSketchNotFilm":True,
            "allowNetworkUpload":False,"allowPaidProviders":False,
            "allowPublication":False,**replace,
        }

    def make(self):
        return strip.build(self.seal,self.plan,self.cards,self.obs,
                           self.song,self.root,self.destination)

    def test_genuine_native_frame_function_and_separate_per_occurrence_authorship(self):
        self.assertEqual(strip.authorize(self.consent(),self.seal),self.consent())
        first=self.make()
        self.assertEqual(first["sampledWindowCount"],2)
        self.assertEqual(len(first["sampledActualRasterShots"]),2)
        self.assertEqual(first["totalNativeShotCount"],2)
        self.assertEqual(first["nativeFrameRate"],film.FPS)
        self.assertFalse(first["movieGenerated"])
        self.assertFalse(first["audioRemixed"])
        self.assertFalse(first["filmKeep"])
        self.assertFalse(first["published"])
        self.assertFalse(list(self.root.rglob("*.mp4")))
        self.assertTrue((self.destination/"filmstrip.json").is_file())
        a=first["sampledActualRasterShots"][0]
        b=first["sampledActualRasterShots"][1]
        self.assertEqual(a["sourceSha256"],b["sourceSha256"])
        self.assertNotEqual(a["focus"],b["focus"])
        self.assertTrue(a["protectText"])
        self.assertFalse(b["protectText"])
        self.assertEqual(a["frames"][0]["actualFrameIndex"],3)
        pic=strip.image_at(self.destination,first,0,1)
        raster=cv2.imread(str(pic))
        self.assertEqual(raster.shape[:2],(film.HEIGHT,film.WIDTH))
        self.assertEqual(donors.sha_file(pic),a["frames"][1]["sha256"])
        self.assertEqual(
            strip.verify(self.destination,self.seal,self.plan,self.cards,
                         self.obs,self.song,self.root),first)
        with self.assertRaisesRegex(ValueError,"create-only"):
            self.make()

    def test_source_tampering_is_hold_not_a_new_artistic_choice(self):
        record=self.make()
        preview=strip.image_at(self.destination,record,1,0)
        preview.write_bytes(preview.read_bytes()+b"forgery")
        with self.assertRaisesRegex(ValueError,"actual sampled frame bytes changed"):
            strip.verify(self.destination,self.seal,self.plan,self.cards,
                         self.obs,self.song,self.root)

    def test_rehashed_record_with_altered_sample_time_is_rejected(self):
        record=self.make()
        forged=copy.deepcopy(record)
        forged["sampledActualRasterShots"][1]["frames"][0]["actualFrameIndex"]+=1
        forged["filmstripSha256"]=iq.digest({
            k:v for k,v in forged.items() if k!="filmstripSha256"})
        (self.destination/"filmstrip.json").write_text(json.dumps(forged))
        with self.assertRaisesRegex(ValueError,"preview time index changed"):
            strip.verify(self.destination,self.seal,self.plan,self.cards,
                         self.obs,self.song,self.root)

    def test_new_photo_or_different_authored_source_is_rejected(self):
        self.make()
        (self.root/"source-002.png").write_bytes(b"changed user source")
        with self.assertRaisesRegex(ValueError,"Unreadable source|source image changed"):
            strip.verify(self.destination,self.seal,self.plan,self.cards,
                         self.obs,self.song,self.root)

    def test_sketch_permission_cannot_be_made_into_provider_or_movie_permission(self):
        for patch in ({"allowPublication":True},
                      {"allowNetworkUpload":True},
                      {"allowPaidProviders":True},
                      {"makeLocalSketch":False},
                      {"storySha256":"0"*64},
                      {"unknown":"render a movie"}):
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError):
                    strip.authorize(self.consent(**patch),self.seal)
        with self.assertRaises(ValueError):
            strip.image_at(self.destination,{"sampledActualRasterShots":[]},-1,0)

    def test_bounded_sampling_never_pretends_omitted_windows_are_bad(self):
        self.assertEqual(strip.selected_indices(2),[0,1])
        choices=strip.selected_indices(256)
        self.assertEqual(len(choices),strip.MAX_WINDOWS)
        self.assertEqual(choices[0],0)
        self.assertEqual(choices[-1],255)
        self.assertEqual(len(set(choices)),len(choices))
        self.assertTrue(all(a<b for a,b in zip(choices,choices[1:])))
        with self.assertRaises(ValueError):
            strip.selected_indices(257)
if __name__=="__main__":
    unittest.main()
