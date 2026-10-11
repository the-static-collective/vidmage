"""BAND-IQ 006 refuses semantic projection and measures only real picture bytes."""
import copy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from bridge import band_iq_question_lab as lab
from bridge import band_iq as iq

ORIGINAL={"schema":"vidmage/editorial-scene-cards/v1","status":"proposal-only",
          "assets":{
              "one":{"path":"a.png","focus":[.5,.5],"mode":"subject"},
              "two":{"path":"b.png","focus":[.3,.5],"mode":"subject"},
          },
          "shots":[{"shotId":"shot-1","assetId":"one","kineticSafe":False},
                   {"shotId":"shot-2","assetId":"two","kineticSafe":False}]}

class QuestionLabPureTest(unittest.TestCase):
    def test_one_shot_delta_is_evidence_not_model_interpretation(self):
        altered=copy.deepcopy(ORIGINAL)
        altered["shots"][0]["assetId"]="two"
        change={"shotId":"shot-1","fromAssetId":"one","toAssetId":"two"}
        self.assertEqual(lab.unchanged_shots(ORIGINAL,altered,"SWAP_CARD",change),["shot-1"])
        altered["shots"][1]["assetId"]="one"
        with self.assertRaisesRegex(ValueError,"only changed occurrence"):
            lab.unchanged_shots(ORIGINAL,altered,"SWAP_CARD",change)

    def test_reframe_does_not_rewrite_every_occurrence(self):
        edited=copy.deepcopy(ORIGINAL)
        edited["assets"]["focus-alias"]=dict(edited["assets"]["one"],focus=[.71,.48])
        edited["shots"][0]["assetId"]="focus-alias"
        change={"shotId":"shot-1","fromAssetId":"one","toAssetId":"focus-alias"}
        self.assertEqual(lab.unchanged_shots(ORIGINAL,edited,"REFOCUS_CARD",change),
                         ["shot-1"])
        with self.assertRaisesRegex(ValueError,"lens-only"):
            lab.unchanged_shots(ORIGINAL,edited,"CHANGE_LENS",{"fromLensId":"sigil"})

    def test_three_questions_are_proposals_not_executions(self):
        rows=lab.make_questions("SWAP_CARD",["window-0001"],[])
        self.assertEqual(len(rows),3)
        self.assertTrue(all(x["requiresHumanChoice"] and x["execution"] is False and
                            x["keep"] is False and x["publication"] is False
                            for x in rows))
        self.assertEqual(len(set(x["proposalSha256"] for x in rows)),3)

    def test_nonstillness_excludes_stasis_and_refuses_bad_scores(self):
        a={"stasis":0,"sourceOveruse":.5,"recentRepetition":.2,
           "noveltyDeficit":.1,"transitionJolt":.1}
        b=dict(a,stasis=1)
        self.assertEqual(lab.nonstillness(a),lab.nonstillness(b))
        self.assertEqual(lab.NONSTILLNESS,("sourceOveruse","recentRepetition",
                                           "noveltyDeficit","transitionJolt"))

    @unittest.skipUnless(shutil.which("ffmpeg"),"requires real local ffmpeg")
    def test_actual_frames_differ_but_same_bytes_do_not(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            a=root/"red.mp4";b=root/"blue.mp4"
            for color,path in (("red",a),("blue",b)):
                subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                                "-i",f"color=c={color}:s=96x54:r=4:d=2",
                                "-c:v","libx264","-pix_fmt","yuv420p",str(path)],
                                check=True)
            report={"windows":[{"id":"window-0001","start":0.0,"end":2.0}]}
            same=lab.compare_frames(a,a,report)
            diff=lab.compare_frames(a,b,report)
            self.assertEqual(same[0]["pixelMeanAbsoluteDifference"],0)
            self.assertGreater(diff[0]["pixelMeanAbsoluteDifference"],.02)
            self.assertEqual(diff[0]["changedFrameFractionAt2PctMAE"],1.0)

if __name__=="__main__":
    unittest.main()
