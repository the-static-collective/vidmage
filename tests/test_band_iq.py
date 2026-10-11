"""BAND-IQ synthetic evidence and anti-automatic-artistic-judgment regression."""
import json
import tempfile
import unittest
from pathlib import Path

from bridge import band_iq as iq

VIDEO_A="a"*64
VIDEO_B="b"*64
AUDIO="c"*64
LANE="d"*64
COMPONENTS={"stasis":1.0,"sourceOveruse":0.0,"recentRepetition":0.0,
            "noveltyDeficit":0.0,"transitionJolt":0.0}


def make_report(video=VIDEO_A,components=None,plan="plan-001",duration=8):
    c=components or COMPONENTS
    rows=[]
    for i in range(2):
        components=dict(c)
        score=round(sum(components[k]*weight for k,weight in
                        [("stasis",.3),("sourceOveruse",.25),("recentRepetition",.2),
                         ("noveltyDeficit",.15),("transitionJolt",.1)]),6)
        rows.append({"id":f"window-{i+1:04}","start":4.0*i,"end":4.0*(i+1),
                     "weaknessScore":score,
                     "components":components,
                     "dominantWeakness":max(components,key=components.get)})
    return {"schema":iq.DOCTOR,"id":"weak-report:sample","sourceVideoSha256":video,
            "planId":plan,"targetSeconds":duration,"observedVideoSeconds":duration,
            "coverageRatio":1.0,"windows":rows}


def audio():
    return {"schema":"vidmage/toaster-lbranch-observation/v1",
            "status":"observation-only","sourceAudioSha256":AUDIO,
            "laneBank":{"schema":"haunted-toaster/lane-bank/v1","laneBankHash":LANE},
            "authority":{"keep":False,"render":False,"publication":False}}


def context(report=None,artist=None,audio_obs=None):
    return {"schema":iq.INPUT,
            "doctorReport":report if report is not None else make_report(),
            "audioObservation":audio_obs,
            "artistAnnotations":artist if artist is not None else []}


def annotation(kind,window="window-0001"):
    return {"kind":kind,"windowId":window,
            "sourceVideoSha256":VIDEO_A,
            "operatorAttestationId":"human:explicit"}


class BandIQTest(unittest.TestCase):
    def test_stillness_alone_is_never_a_weakness_target(self):
        cycle=iq.build_cycle(context())
        self.assertTrue(iq.verify_cycle(cycle))
        self.assertIsNone(cycle["experiment"]["candidateWindowId"])
        self.assertEqual(cycle["experiment"]["status"],"HOLD-no-unprotected-windows")
        self.assertTrue(all(p["status"]=="HOLD-protected" for p in cycle["imagine"]))
        self.assertEqual(len({p["proposalSha256"] for p in cycle["imagine"]}),6)
        self.assertEqual(len({p["cameraMode"] for p in cycle["imagine"]}),6)

    def test_nonmotion_weakness_can_be_proposed_without_execution(self):
        c=dict(COMPONENTS,sourceOveruse=.8,recentRepetition=.7)
        x=iq.build_cycle(context(make_report(components=c),audio_obs=audio()))
        self.assertEqual(x["experiment"]["candidateWindowId"],"window-0001")
        self.assertEqual(x["perceive"]["audioSha256"],AUDIO)
        self.assertEqual(len(x["imagine"]),6)
        self.assertTrue(all(p["execution"] is False and p["keep"] is False
                            for p in x["imagine"]))
        self.assertIsNone(x["experiment"]["automaticAction"])
        self.assertFalse(x["experiment"]["externalUploadPermission"])

    def test_explicit_stillness_attestation_protects_observed_section(self):
        c=dict(COMPONENTS,sourceOveruse=.8)
        x=iq.build_cycle(context(make_report(components=c),[annotation("deliberate-stillness")]))
        self.assertEqual(x["experiment"]["candidateWindowId"],"window-0002")
        self.assertEqual(x["relate"]["artistProtectedWindowIds"],["window-0001"])
        self.assertNotIn("window-0001",x["relate"]["unprotectedObservedWindowIds"])

    def test_artistic_motion_review_requires_author_attestation(self):
        x=iq.build_cycle(context(artist=[annotation("motion-review-authorized")]))
        self.assertEqual(x["experiment"]["candidateWindowId"],"window-0001")
        self.assertIn("window-0001",x["relate"]["artistAuthorizedMotionReviewIds"])
        self.assertFalse(x["imagine"][0]["execution"])

    def test_unauthorized_annotations_or_audio_authority_refused(self):
        invalid=annotation("deliberate-stillness")
        invalid["sourceVideoSha256"]=VIDEO_B
        with self.assertRaisesRegex(ValueError,"annotation source changed"):
            iq.build_cycle(context(artist=[invalid]))
        forged=audio();forged["authority"]["keep"]=True
        with self.assertRaisesRegex(ValueError,"authority escalation"):
            iq.build_cycle(context(audio_obs=forged))

    def test_tampering_cycle_or_changed_source_cannot_pass_memory(self):
        x=iq.build_cycle(context())
        x2=json.loads(json.dumps(x))
        x2["imagine"][0]["execution"]=True
        with self.assertRaisesRegex(ValueError,"modified"):
            iq.verify_cycle(x2)
        y=iq.build_cycle(context(),previous=x)
        self.assertEqual(y["predecessorCycleSha256"],x["cycleSha256"])
        with self.assertRaisesRegex(ValueError,"cross-source"):
            iq.build_cycle(context(make_report(video=VIDEO_B)),previous=x)

    def test_rendered_trial_must_preserve_coverage_and_media_difference(self):
        c=dict(COMPONENTS,sourceOveruse=.9)
        before=make_report(components=c)
        cycle=iq.build_cycle(context(before))
        after=make_report(video=VIDEO_B,components=dict(c,sourceOveruse=.3))
        result=iq.compare_trial(cycle,before,after)
        self.assertTrue(result["technicalDeltaImproved"])
        self.assertIsNone(result["humanReview"])
        self.assertFalse(result["automaticAcceptance"])
        self.assertTrue(result["unprotectedMeanWeaknessDelta"] < 0)
        bad=dict(after,coverageRatio=.9)
        with self.assertRaisesRegex(ValueError,"coverage"):
            iq.compare_trial(cycle,before,bad)
        with self.assertRaisesRegex(ValueError,"same video"):
            iq.compare_trial(cycle,before,before)

    def test_stasis_change_is_not_claimed_as_quality_improvement(self):
        before=make_report(components=dict(COMPONENTS,sourceOveruse=.4))
        cycle=iq.build_cycle(context(before))
        after=make_report(video=VIDEO_B,components=dict(COMPONENTS,stasis=0.0,sourceOveruse=.4))
        result=iq.compare_trial(cycle,before,after)
        self.assertEqual(result["unprotectedMeanWeaknessDelta"],0)
        self.assertFalse(result["technicalDeltaImproved"])
        self.assertLess(result["comparisonWindows"][0]["delta"],0)

    def test_protected_window_excluded_from_comparison_summary(self):
        before=make_report(components=dict(COMPONENTS,sourceOveruse=.8))
        cycle=iq.build_cycle(context(before,[annotation("protected-scene")]))
        after=make_report(video=VIDEO_B,components=dict(COMPONENTS,sourceOveruse=.2))
        out=iq.compare_trial(cycle,before,after,{"decision":"SCRAPE","operatorAttestationId":"human:review"})
        self.assertTrue(out["comparisonWindows"][0]["protected"])
        self.assertEqual(out["humanReview"]["decision"],"SCRAPE")
        self.assertFalse(out["automaticAcceptance"])

    def test_exact_idempotent_create_only_writes(self):
        cycle=iq.build_cycle(context())
        with tempfile.TemporaryDirectory() as root:
            name=iq.write_once(root,cycle,"cycleSha256")
            self.assertTrue(Path(name).is_file())
            self.assertEqual(iq.write_once(root,cycle,"cycleSha256"),name)
            Path(name).write_text('{"tampered":true}')
            with self.assertRaisesRegex(ValueError,"overwrite refused"):
                iq.write_once(root,cycle,"cycleSha256")

    def test_native_doctor_envelope_can_be_assembled_without_forging_observations(self):
        report=make_report()
        envelope={"report":report,"reportSha256":iq.digest(report),
                  "sourceVideoSha256":report["sourceVideoSha256"]}
        assembled=iq.assemble_input(envelope,artist_annotations=[annotation("deliberate-stillness")])
        self.assertEqual(assembled["schema"],iq.INPUT)
        self.assertTrue(iq.verify_cycle(iq.build_cycle(assembled)))
        envelope["reportSha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"envelope changed"):
            iq.assemble_input(envelope)

    def test_missing_or_malformed_windows_refuse(self):
        r=make_report()
        r["windows"][1]["start"]=6
        with self.assertRaisesRegex(ValueError,"noncontiguous"):
            iq.build_cycle(context(r))
        r=make_report()
        r["windows"][0]["components"]["stasis"]=float("nan")
        with self.assertRaisesRegex(ValueError,"components"):
            iq.build_cycle(context(r))


if __name__=="__main__":
    unittest.main()
