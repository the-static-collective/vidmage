"""Native Toaster L BRANCH -> native Blender Paper Director crossing tests.
Runs on public synthetic media only. Source repos are cloned at pinned exact commits.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bridge.blender_director_cross import propose, validate
from haunted_blender import paper_director

ROOT = Path(__file__).resolve().parents[1]
TOASTER = os.environ.get('VIDMAGE_TOASTER_ROOT')

class CrossTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not TOASTER:
            raise RuntimeError('VIDMAGE_TOASTER_ROOT must be a pinned Toaster checkout')
        cls.temp = tempfile.TemporaryDirectory(prefix='vidmage-lbranch-')
        cls.dir = Path(cls.temp.name)
        cls.audio = cls.dir/'synthetic.wav'
        # Sine tone with honest synthetic provenance, no real user media.
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y',
            '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=12',
            '-c:a','pcm_s16le',str(cls.audio)], check=True)
        cls.observation = cls.dir/'obs.json'
        subprocess.run(['node', str(ROOT/'bridge/toaster_lbranch_capture.cjs'),
            '--toaster-root',str(TOASTER), '--audio',str(cls.audio),
            '--out',str(cls.observation)],check=True,capture_output=True,text=True)
        cls.obs=json.loads(cls.observation.read_text())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_native_bank_and_no_made_up_vocal(self):
        bank, sections, duration = validate(self.obs)
        self.assertEqual(bank['schema'],'haunted-toaster/lane-bank/v1')
        self.assertIn('raw-energy-envelope', bank['laneIds'])
        self.assertNotIn('vocal-salience', bank['laneIds'])
        self.assertIn('vocal-salience',bank['absentLaneIds'])
        self.assertEqual(hashlib.sha256(self.audio.read_bytes()).hexdigest(),self.obs['sourceAudioSha256'])
        self.assertAlmostEqual(sections[-1]['end'],duration,places=2)

    def test_native_blender_proposals_are_repeatable_and_not_accepted(self):
        a=propose(self.obs,'breath-led',3)
        b=propose(self.obs,'breath-led',3)
        self.assertEqual(a,b)
        self.assertFalse(a['selectedForRender'])
        self.assertFalse(a['proposedAuthority']['render'])
        self.assertTrue(a['noAutomaticLyricTiming'])
        self.assertAlmostEqual(a['paperDirectorPlan']['coverageRatio'],1.0)
        self.assertEqual(a['paperDirectorPlan']['shotCount'],len(a['paperDirectorPlan']['shots']))
        self.assertEqual(a['paperDirectorPlan']['shots'][-1]['type'],'RETURN')

    def test_refuse_forged_admission_and_bad_sections(self):
        bad=json.loads(json.dumps(self.obs))
        bad['authority']['render']=True
        with self.assertRaises(ValueError):propose(bad)
        bad=json.loads(json.dumps(self.obs))
        bad['sections'][0]['end']+=0.6
        with self.assertRaises(ValueError):propose(bad)
        with self.assertRaises(ValueError):propose(self.obs,'voice-architecture')

    def test_real_blender_h264_render_and_receipt(self):
        proposal=propose(self.obs,'breath-led',4)
        # Render only from an intentionally synthetic base; paper_director itself
        # does not rewrite the underlying audio authority.
        movie=self.dir/'base.mp4'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y',
            '-f','lavfi','-i','color=c=blue:s=320x180:r=12:d=12',
            '-i',str(self.audio),'-shortest','-c:v','libx264','-pix_fmt','yuv420p',
            '-c:a','aac',str(movie)],check=True)
        dest=self.dir/'directed.mp4'
        receipt=paper_director.render(movie,proposal['paperDirectorPlan'],dest)
        self.assertTrue(dest.exists())
        self.assertEqual(receipt['shotCount'],proposal['paperDirectorPlan']['shotCount'])
        self.assertEqual(receipt['outputSha256'],hashlib.sha256(dest.read_bytes()).hexdigest())
        self.assertAlmostEqual(receipt['coverageRatio'],1.0)
        self.assertEqual(receipt['providerCredits'],0)
        with self.assertRaises(FileExistsError):
            paper_director.render(movie,proposal['paperDirectorPlan'],dest)

if __name__ == '__main__':
    unittest.main()
