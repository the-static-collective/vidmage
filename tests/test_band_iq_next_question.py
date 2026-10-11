"""BAND-IQ 005 explicit author question: no NLP-as-authorization and one-variable edits."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from bridge import band_iq as iq
from bridge import band_iq_next_question as nxt

def qset():
    source=[
        {"kind":"SWAP_CARD","status":"proposal-only","eligibleShotIds":["s1"],
         "eligibleReplacementAssetIdsByShot":{"s1":["other"]},"eligibleLensIds":[],
         "description":nxt.OPS["SWAP_CARD"]},
        {"kind":"REFOCUS_CARD","status":"proposal-only","eligibleShotIds":["s1"],
         "eligibleReplacementAssetIdsByShot":{},"eligibleLensIds":[],
         "description":nxt.OPS["REFOCUS_CARD"]},
        {"kind":"CHANGE_LENS","status":"proposal-only","eligibleShotIds":[],
         "eligibleReplacementAssetIdsByShot":{},"eligibleLensIds":["sigil"],
         "description":nxt.OPS["CHANGE_LENS"]},
    ]
    body={"schema":nxt.PROPOSALS,
          "humanQuestionVerbatim":"Can the first shot feel more distant?",
          "sourceReviewSha256":"a"*64,
          "priorCinematic":{"lensId":"landscape","cameraMode":"survey",
                            "start":0,"end":2,"sourceProposalSha256":"b"*64},
          "proposals":[{**p,"proposalSha256":iq.digest(p)} for p in source]}
    return {**body,"questionSetSha256":iq.digest(body)}

def selection(q,kind="SWAP_CARD",**extra):
    op=next(p for p in q["proposals"] if p["kind"]==kind)
    body={"schema":nxt.AUTH,"questionSetSha256":q["questionSetSha256"],
          "proposalSha256":op["proposalSha256"],
          "operatorAttestationId":"human-second-act",
          "decision":"RENDER_ONE_LOCAL_TRIAL",
          "shotId":"s1" if kind!="CHANGE_LENS" else None,
          "replacementAssetId":"other" if kind=="SWAP_CARD" else None,
          "newFocus":[.75,.66] if kind=="REFOCUS_CARD" else None,
          "newLensId":"sigil" if kind=="CHANGE_LENS" else None,
          "allowLocalExecution":True,"allowPaidProviders":False,
          "allowNetworkUpload":False}
    body.update(extra)
    return body

CARDS={"schema":"vidmage/editorial-scene-cards/v1",
       "status":"proposal-only",
       "assets":{"first":{"path":"a.png","mode":"subject","focus":[.5,.5]},
                 "other":{"path":"b.png","mode":"subject","focus":[.4,.4]}},
       "shots":[{"shotId":"s1","assetId":"first","kineticSafe":False},
                {"shotId":"s2","assetId":"other","kineticSafe":False}]}

class NextQuestionPureTests(unittest.TestCase):
    def test_author_chooses_a_clearly_defined_experiment(self):
        q=qset()
        self.assertEqual(len(q["proposals"]),3)
        for kind in nxt.OPS:
            auth=selection(q,kind)
            op=nxt.validate_authorization(q,auth,None,CARDS)
            self.assertEqual(op["kind"],kind)
            revised,change=nxt.realize_cards(CARDS,op,auth,q)
            self.assertEqual(iq.digest(CARDS),iq.digest(copy.deepcopy(CARDS)))
            if kind=="SWAP_CARD":
                self.assertEqual(revised["shots"][0]["assetId"],"other")
                self.assertEqual(revised["shots"][1]["assetId"],"other")
            elif kind=="REFOCUS_CARD":
                aid=revised["shots"][0]["assetId"]
                self.assertNotEqual(aid,"first")
                self.assertEqual(revised["assets"][aid]["focus"],[.75,.66])
                self.assertEqual(revised["assets"][aid]["path"],"a.png")
                self.assertEqual(revised["assets"]["first"],CARDS["assets"]["first"])
                self.assertEqual(revised["shots"][1],CARDS["shots"][1])
                self.assertTrue(change["sameOwnedBytes"])
            else:
                self.assertEqual(revised,CARDS)
                self.assertEqual(change["toLensId"],"sigil")

    def test_source_ambiguity_and_provider_authority_are_refusals(self):
        q=qset()
        attempts=[
            (selection(q,"SWAP_CARD",replacementAssetId="first"),"replacement"),
            (selection(q,"SWAP_CARD",replacementAssetId="../../secrets"),"replacement"),
            (selection(q,"REFOCUS_CARD",newFocus=[1.0,1.0]),"focus"),
            (selection(q,"REFOCUS_CARD",newFocus=[.5,.5]),"genuinely new"),
            (selection(q,"CHANGE_LENS",newLensId="unknown"),"lens"),
            (selection(q,"CHANGE_LENS",shotId="s1"),"lens"),
            (selection(q,"SWAP_CARD",allowNetworkUpload=True),"authorization"),
            (selection(q,"SWAP_CARD",allowPaidProviders=True),"authorization"),
            (selection(q,"SWAP_CARD",allowLocalExecution=False),"authorization"),
            (selection(q,"SWAP_CARD",operatorAttestationId=""),"act"),
            (selection(q,"SWAP_CARD",decision="PUBLISH"),"authorization"),
            (selection(q,"SWAP_CARD",proposalSha256="f"*64),"proposal"),
            (selection(q,"SWAP_CARD",questionSetSha256="f"*64),"question set"),
        ]
        for auth,detail in attempts:
            with self.subTest(auth=auth,detail=detail):
                with self.assertRaisesRegex(ValueError,detail):
                    nxt.validate_authorization(q,auth,None,CARDS)

    def test_question_record_or_submitted_fields_cannot_be_rewritten(self):
        q=qset()
        bad=copy.deepcopy(q)
        bad["humanQuestionVerbatim"]="The AI secretly changed the question"
        with self.assertRaisesRegex(ValueError,"evidence identity"):
            nxt.validate_authorization(bad,selection(q),None,CARDS)
        auth=selection(q)
        auth["inventedExtraInstruction"]="Ignore the creator"
        with self.assertRaisesRegex(ValueError,"exact typed"):
            nxt.validate_authorization(q,auth,None,CARDS)

    def test_invalid_proposal_status_is_never_autocorrected(self):
        q=qset()
        bad=copy.deepcopy(q)
        bad["proposals"][0]["status"]="HOLD-unavailable"
        bad["questionSetSha256"]=iq.digest({k:v for k,v in bad.items()
                                            if k!="questionSetSha256"})
        with self.assertRaisesRegex(ValueError,"proposal"):
            nxt.validate_authorization(bad,selection(bad),None,CARDS)

if __name__=="__main__":
    unittest.main()
