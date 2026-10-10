"""Synthetic-media proof: two create-only H264 movies; no user assets in CI."""
import json, subprocess, tempfile, unittest
from pathlib import Path
import cv2
import numpy as np
from bridge.scene_card_film import render, validate

class SceneCardProof(unittest.TestCase):
    def test_bounded_and_optional_kinetic(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            a=np.full((480,800,3),(90,140,170),dtype=np.uint8)
            cv2.putText(a,'SCENE',(120,300),cv2.FONT_HERSHEY_SIMPLEX,4,(255,250,25),14)
            cv2.imwrite(str(root/'a.png'),a)
            cv2.imwrite(str(root/'b.png'),np.full((700,700,3),(120,90,40),dtype=np.uint8))
            audio=root/'tone.wav'
            subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','lavfi',
                            '-i','sine=frequency=440:duration=3:sample_rate=16000',str(audio)],check=True)
            plan={'schema':'haunted-blender/paper-director-plan/v1','durationSeconds':3.,
                  'id':'paper-director-plan:synthetic',
                  'shots':[{'id':'shot-0001','start':0.,'end':1.5},
                           {'id':'shot-0002','start':1.5,'end':3.}]}
            cards={'schema':'vidmage/editorial-scene-cards/v1','status':'proposal-only',
                   'assets':{'a':{'path':'a.png','focus':[.5,.5],'mode':'subject'},
                             'b':{'path':'b.png','focus':[.5,.5],'mode':'protect-text'}},
                   'shots':[{'shotId':'shot-0001','assetId':'a','kineticSafe':True},
                            {'shotId':'shot-0002','assetId':'b','kineticSafe':False}]}
            observation={'schema':'vidmage/toaster-lbranch-observation/v1',
              'laneBank':{'schema':'haunted-toaster/lane-bank/v1','laneBankHash':'f'*64,
               'lanes':[{'id':'raw-energy-envelope',
                         'knots':[{'atSeconds':0,'value':.3},{'atSeconds':3,'value':.8}]},
                        {'id':'transient-pressure',
                         'knots':[{'atSeconds':0,'value':.1},{'atSeconds':1,'value':.9},
                                  {'atSeconds':3,'value':.1}]}]}}
            base=root/'base.mp4';boost=root/'boost.mp4'
            first=render(plan,cards,observation,audio,root,base,False)
            second=render(plan,cards,observation,audio,root,boost,True)
            self.assertNotEqual(first['outputSha256'],second['outputSha256'])
            self.assertEqual(first['frames'],36)
            self.assertEqual(len(first['streams']),2)
            self.assertEqual(first['providerCredits'],0)
            self.assertEqual(second['published'],False)
            self.assertAlmostEqual(first['observedSeconds'],3,places=1)
            with self.assertRaises(FileExistsError):
                render(plan,cards,observation,audio,root,base)
            invalid=json.loads(json.dumps(cards))
            invalid['status']='published'
            with self.assertRaises(ValueError):
                validate(plan,invalid,observation,root)
            invalid=json.loads(json.dumps(cards))
            invalid['shots'][0]['assetId']='missing'
            with self.assertRaises(ValueError):
                validate(plan,invalid,observation,root)
            invalid=json.loads(json.dumps(cards))
            invalid['assets']['a']['path']='../outside.png'
            with self.assertRaises((ValueError,FileNotFoundError)):
                validate(plan,invalid,observation,root)

if __name__=='__main__':unittest.main()
