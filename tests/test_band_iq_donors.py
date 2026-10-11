"""Native and refusal proof for explicitly selected BAND-IQ donor doors."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge import band_iq as iq
from bridge import band_iq_donors as donors


def selection(op):
    return {"schema":"vidmage/band-iq-local-selection/v1",
            "operation":op,"sourceRights":"creator-authorized",
            "operatorAttestationId":"operator-selected-synthetic",
            "allowLocalExecution":True,"allowPaidProviders":False,
            "allowNetworkUpload":False}


class NativeDoorTest(unittest.TestCase):
    def test_unsafe_authority_refused(self):
        okay=selection("harvest-008h")
        donors.authorize(okay,"harvest-008h")
        for key in ("allowPaidProviders","allowNetworkUpload"):
            bad=dict(okay,**{key:True})
            with self.assertRaisesRegex(ValueError,"external authority"):
                donors.authorize(bad,"harvest-008h")
        bad=dict(okay,allowLocalExecution=False)
        with self.assertRaisesRegex(ValueError,"explicit"):
            donors.authorize(bad,"harvest-008h")
        bad=dict(okay,sourceRights="unknown")
        with self.assertRaisesRegex(ValueError,"rights"):
            donors.authorize(bad,"harvest-008h")
        with self.assertRaisesRegex(ValueError,"mismatched"):
            donors.authorize(okay,"direct-008j")

    def test_uninstalled_optional_workers_are_not_claimed(self):
        spec=donors.describe()
        self.assertEqual({v["id"] for v in spec["operations"]},
                         {"scan-008f","harvest-008h","direct-008j","material-008l"})
        self.assertEqual(len(spec["optionalFutureNotInstalled"]),4)

    @unittest.skipUnless(os.environ.get("VIDMAGE_BLENDER_ROOT") and shutil.which("ffmpeg"),
                         "requires pinned Blender checkout and FFmpeg")
    def test_real_native_ffmpeg_doctor_scan_enters_band_iq(self):
        root=os.environ["VIDMAGE_BLENDER_ROOT"]
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            video=tmp/"original.mp4"
            subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                            "-i","color=c=black:size=128x72:rate=4:duration=8",
                            "-an","-c:v","libx264","-pix_fmt","yuv420p",
                            str(video)],check=True)
            from haunted_blender import zero_dollar_mill
            plan={"schema":zero_dollar_mill.PLAN_SCHEMA,"id":"synthetic-plan-001",
                  "targetSeconds":8.0,
                  "slugs":[
                    {"id":"slug-1","sourceAssetId":"synthetic-a","durationSeconds":4,"sourceSha256":"f"*64,"recipe":"fit"},
                    {"id":"slug-2","sourceAssetId":"synthetic-b","durationSeconds":4,"sourceSha256":"e"*64,"recipe":"fit"},
                  ]}
            source_plan=tmp/"plan.json"
            source_plan.write_text(json.dumps(plan))
            reportdir=tmp/"scan"
            res=donors.run_selected(selection("scan-008f"),
                                    blender_root=root,source=video,output=reportdir,
                                    plan=source_plan,sample_fps=4)
            self.assertEqual(res["result"]["op"],"scan-008f")
            envelope=json.loads((reportdir/"doctor.json").read_text())
            report=envelope["report"]
            self.assertEqual(report["sourceVideoSha256"],donors.sha_file(video))
            self.assertEqual(len(report["windows"]),2)
            self.assertEqual(report["coverageRatio"],1.0)
            self.assertEqual(envelope["reportSha256"],iq.digest(report))
            context={"schema":iq.INPUT,"doctorReport":report,
                     "audioObservation":None,
                     "artistAnnotations":[{
                         "windowId":report["windows"][0]["id"],
                         "kind":"deliberate-stillness",
                         "operatorAttestationId":"human:stillness-selected",
                         "sourceVideoSha256":report["sourceVideoSha256"],
                     }]}
            cycle=iq.build_cycle(context)
            self.assertTrue(iq.verify_cycle(cycle))
            self.assertNotEqual(cycle["experiment"]["candidateWindowId"],
                                report["windows"][0]["id"])
            self.assertFalse(cycle["experiment"]["requiresOwnerSelection"] is False)
            self.assertFalse(cycle["imagine"][0]["execution"])
            self.assertTrue(Path(res["receipt"]).is_file())


if __name__=="__main__":
    unittest.main()
