"""BAND-IQ 001: bounded evidence -> six cinematic questions -> human trial -> feedback.

Requires no native Blender/Playdeck import for its pure planning core. Actual media
observations enter through the separately pinned band_iq_donors.py adapter.
This module does not render, alter sources, admit edits, or judge artistic value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SCHEMA = "vidmage/band-iq-cycle/v1"
INPUT = "vidmage/band-iq-input/v1"
TRIAL = "vidmage/band-iq-trial-evidence/v1"
DOCTOR = "haunted-blender/weakest-window-report/v1"
LENSES = {
    # Playdeck Studio 011 director vocabulary, not direct Playdeck execution.
    "landscape": ("survey", "terrain-bands", "long-breath", "parallel-drift", "erosion"),
    "architecture": ("hinge-orbit", "corridor", "measured-cuts", "axial-lock", "room-trace"),
    "organism": ("pulse-dolly", "cellular-cluster", "elastic-pulse", "attraction-repulsion", "scar-recall"),
    "sigil": ("snap-frame", "glyph-grid", "syncopated-cuts", "stroke-link", "overwrite-ghost"),
    "weather": ("wind-eye", "particle-field", "gust-bursts", "swarm", "wake"),
    "dimensional-space": ("parallax-orbit", "nested-planes", "folded-time", "orbit-crossing", "nested-afterimage"),
}
DONORS = {
    "blender-008f": {"sha": "363e1ddcb22570b82e3df5b07008c0a2a79f1c1c", "verb": "observe-and-trial"},
    "blender-008h": {"sha": "9bdd378b98001770af1191c01ae93e7938265bf3", "verb": "harvest-proposal"},
    "blender-008j": {"sha": "070d8034e11052f7e84588e19e36f452c862a772", "verb": "director-proposal"},
    "blender-008l": {"sha": "a39d6c3be8197b38b06c2f45fb323e4ef8b4f279", "verb": "material-proposal"},
    "blender-composite": {"sha": "cf0256a49ac8aa879cf2a044847d248177fcfad9", "verb": "pinned-tested-native-implementation"},
    "playdeck-studio-011": {"sha": "012186fd67f4c4ef1c6591fc5e29cb559b5a80d0", "verb": "cinematic-vocabulary-only"},
    "vidmage-cross-001": {"sha": "223190e7294197532cdfebb598ae8d85f8273c7e", "verb": "native-audio-cross"},
}
CANDIDATES = ("kinetic-push", "pull", "misregister", "owned-bit", "paper-director", "material-surface")
SHA = "0123456789abcdef"


def require(ok, message):
    if not ok:
        raise ValueError("BAND-IQ HOLD: " + message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in SHA for c in value)


def finite(value, low=None, high=None):
    ok = type(value) in (int, float) and math.isfinite(value)
    return ok and (low is None or value >= low) and (high is None or value <= high)


def bounded(text, label, maximum=512):
    require(isinstance(text, str) and 0 < len(text.strip()) <= maximum, label)
    return text


def validate_report(report):
    require(isinstance(report, dict) and report.get("schema") == DOCTOR, "native 008f report required")
    require(sha(report.get("sourceVideoSha256")), "source video SHA256 missing")
    require(isinstance(report.get("planId"), str) and report["planId"], "Doctor plan identity missing")
    require(finite(report.get("targetSeconds"), .001, 36000), "invalid target duration")
    require(finite(report.get("observedVideoSeconds"), .001), "invalid observed duration")
    require(finite(report.get("coverageRatio"), 0, 1), "invalid coverage ratio")
    require(report["observedVideoSeconds"] + .08 >= report["targetSeconds"], "full song coverage lost")
    require(isinstance(report.get("windows"), list) and 1 <= len(report["windows"]) <= 10000,
            "bounded observed windows required")
    seen, cursor = set(), 0.0
    for row in report["windows"]:
        require(isinstance(row, dict), "invalid window")
        wid = bounded(row.get("id"), "window ID missing")
        require(wid not in seen, "duplicate window ID")
        seen.add(wid)
        start, end = row.get("start"), row.get("end")
        require(finite(start, 0) and finite(end, 0) and
                abs(start-cursor) <= .03 and end > start and
                end <= report["targetSeconds"] + .03, "noncontiguous window observations")
        cursor = end
        require(finite(row.get("weaknessScore"), 0, 1), "invalid Doctor measurement")
        require(row.get("dominantWeakness") in
                ("stasis", "sourceOveruse", "recentRepetition", "noveltyDeficit", "transitionJolt"),
                "unexpected Doctor weakness dimension")
        require(isinstance(row.get("components"), dict) and all(
            finite(row["components"].get(k), 0, 1) for k in
            ("stasis", "sourceOveruse", "recentRepetition", "noveltyDeficit", "transitionJolt")),
            "missing independent weakness components")
    require(abs(cursor-report["targetSeconds"]) <= .03, "window list does not cover whole song")
    return report


def validate_audio(obs):
    if obs is None:
        return None
    require(isinstance(obs, dict) and
            obs.get("schema") == "vidmage/toaster-lbranch-observation/v1" and
            obs.get("status") == "observation-only", "native Toaster observation required")
    require(sha(obs.get("sourceAudioSha256")), "audio SHA missing")
    bank = obs.get("laneBank") or {}
    require(bank.get("schema") == "haunted-toaster/lane-bank/v1" and
            sha(bank.get("laneBankHash")), "exact L BRANCH bank required")
    require(isinstance(obs.get("authority"), dict) and
            not any(obs["authority"].values()), "audio observation attempts authority escalation")
    return obs


def validate_annotations(entries, report):
    require(isinstance(entries, list) and len(entries) <= 10000, "bounded annotations required")
    windows = {row["id"] for row in report["windows"]}
    kinds = {"deliberate-stillness", "protected-scene", "motion-review-authorized"}
    selected = {}
    for entry in entries:
        require(isinstance(entry, dict) and set(entry) ==
                {"windowId", "kind", "operatorAttestationId", "sourceVideoSha256"},
                "invalid explicit annotation shape")
        wid = entry["windowId"]
        require(wid in windows and wid not in selected, "unrecognized or repeated annotation target")
        require(entry["kind"] in kinds, "unsupported artistic intent annotation")
        bounded(entry["operatorAttestationId"], "operator attestation is required")
        require(entry["sourceVideoSha256"] == report["sourceVideoSha256"],
                "annotation source changed")
        selected[wid] = dict(entry)
    return selected


def build_cycle(data, previous=None):
    require(isinstance(data, dict) and data.get("schema") == INPUT, "input schema invalid")
    require(set(data) == {"schema", "doctorReport", "audioObservation", "artistAnnotations"},
            "unknown or missing input fields")
    report = validate_report(data["doctorReport"])
    audio = validate_audio(data["audioObservation"])
    authored = validate_annotations(data["artistAnnotations"], report)
    if previous is not None:
        verify_cycle(previous)
        require(previous["sourceVideoSha256"] == report["sourceVideoSha256"],
                "cross-source memory requires a separately authorized transition")

    # Native Doctor includes stasis in its technical index, but BAND-IQ must not
    # infer that a quiet shot is unwanted. Rank solely by *non-stasis* observations.
    def nonstillness(row):
        c = row["components"]
        return round(.25*c["sourceOveruse"] + .20*c["recentRepetition"] +
                     .15*c["noveltyDeficit"] + .10*c["transitionJolt"], 6)

    candidates = sorted(report["windows"], key=lambda w:(-nonstillness(w), w["start"], w["id"]))
    protected = sorted(k for k in authored if authored[k]["kind"] != "motion-review-authorized")
    review_authorized = sorted(k for k in authored if authored[k]["kind"] == "motion-review-authorized")
    targets = [w for w in candidates if w["id"] not in protected and
               (nonstillness(w) > 0.05 or w["id"] in review_authorized)]
    perception = {
        "doctorReportId": report.get("id"),
        "doctorReportSha256": digest(report),
        "videoSha256": report["sourceVideoSha256"],
        "audioSha256": audio["sourceAudioSha256"] if audio else None,
        "laneBankHash": (audio["laneBank"]["laneBankHash"] if audio else None),
        "targetSeconds": report["targetSeconds"],
        "coverageRatio": report["coverageRatio"],
        "windowCount": len(report["windows"]),
        "measuredWeaknessDimensions": list(("stasis","sourceOveruse","recentRepetition",
                                            "noveltyDeficit","transitionJolt")),
        "semanticObjectTracking": "not observed",
        "depth": "not observed",
        "lyricTiming": "not inferred",
    }
    relationships = {
        "materialUse": "read the observed 008f source rows only; do not infer objects",
        "artistProtectedWindowIds": protected,
        "artistAuthorizedMotionReviewIds": review_authorized,
        "unprotectedObservedWindowIds": [w["id"] for w in targets],
        "nonStillnessMetric": "0.25 overuse + 0.20 repetition + 0.15 novelty deficit + 0.10 jolt; stasis excluded",
        "sourceAuthority": "read-only observed locally",
    }
    next_window = targets[0] if targets else None
    questions = []
    for lens, (camera, topology, rhythm, relation, memory) in LENSES.items():
        w = next_window
        proposal = {
            "lensId": lens,
            "cameraMode": camera,
            "topology": topology,
            "cutRhythm": rhythm,
            "relationMode": relation,
            "memoryMode": memory,
            "targetWindowId": w["id"] if w else None,
            "targetStart": w["start"] if w else None,
            "targetEnd": w["end"] if w else None,
            "measuredDominantWeakness": w["dominantWeakness"] if w else None,
            "experimentQuestion": (
                f"What happens to verified non-stillness measurements under {camera} in {w['id']}?"
                if w else "No author-permitted, non-stillness target; ask the author first."),
            "status": "proposal-only" if w else "HOLD-protected",
            "execution": False,
            "keep": False,
            "publish": False,
        }
        questions.append({**proposal, "proposalSha256": digest(proposal)})
    trial = {
        "status": "proposal-only" if next_window else "HOLD-no-unprotected-windows",
        "candidateWindowId": next_window["id"] if next_window else None,
        "recipeOptions": list(CANDIDATES) if next_window else [],
        "firstTreatmentLevel": 1 if next_window else None,
        "automaticAction": None,
        "preserveOriginal": True,
        "requiresOwnerSelection": True,
        "paidProviderPermission": False,
        "externalUploadPermission": False,
    }
    body = {
        "schema": SCHEMA, "name": "BAND-IQ 001", "status": "observation-and-proposals",
        "sourceVideoSha256": report["sourceVideoSha256"],
        "sourceDoctorReportSha256": digest(report),
        "sourceAudioObservationSha256": digest(audio) if audio else None,
        "predecessorCycleSha256": previous["cycleSha256"] if previous else None,
        "pins": DONORS,
        "perceive": perception, "relate": relationships,
        "imagine": questions, "experiment": trial,
        "compare": {"status":"awaits separately rendered trial and independent 008f rescan",
                    "numericImprovementIsNotAestheticApproval":True},
        "remember": {"mode":"create-only-content-addressed", "previousCycleLinked":bool(previous)},
        "laws": ["STILLNESS != WEAKNESS", "MEASUREMENT != TASTE",
                 "SOURCE != PROPOSAL", "TRIAL != KEEP", "VIEW != WORLD",
                 "SOURCE SHA != AUTHORIZATION", "PROPOSAL != EXECUTION",
                 "HUMAN SELECTION != INFERRED FROM SCORE", "COMPARED != PUBLISHED"],
    }
    return {**body, "cycleSha256": digest(body)}


def verify_cycle(cycle):
    require(isinstance(cycle, dict) and cycle.get("schema") == SCHEMA, "invalid cycle schema")
    presented = cycle.get("cycleSha256")
    require(sha(presented), "cycle identity must be SHA256")
    require(digest({k:v for k,v in cycle.items() if k!="cycleSha256"}) == presented,
            "cycle was modified")
    require(cycle.get("status") == "observation-and-proposals" and
            cycle.get("pins") == DONORS and
            len(cycle.get("imagine", [])) == 6 and
            all(p.get("execution") is False and p.get("keep") is False and p.get("publish") is False
                for p in cycle["imagine"]), "cycle claims unsafe authority")
    return True


def compare_trial(cycle, before, after, human_review=None):
    verify_cycle(cycle)
    validate_report(before)
    validate_report(after)
    require(cycle["sourceDoctorReportSha256"] == digest(before),
            "before report does not match observed source")
    require(abs(before["targetSeconds"]-after["targetSeconds"]) <= .03 and
            len(before["windows"]) == len(after["windows"]) and
            all(abs(a["start"]-b["start"]) <= .03 and
                    abs(a["end"]-b["end"]) <= .03
                    for a,b in zip(before["windows"], after["windows"])),
            "trial comparison lost matched times")
    require(after["coverageRatio"] + 1e-8 >= before["coverageRatio"] and
            after["observedVideoSeconds"] + .08 >= before["targetSeconds"],
            "trial lost coverage")
    require(after["sourceVideoSha256"] != before["sourceVideoSha256"],
            "same video bytes do not establish a new experimental trial")
    protected = set(cycle["relate"]["artistProtectedWindowIds"])
    before_map = {w["id"]:w for w in before["windows"]}
    after_map = {w["id"]:w for w in after["windows"]}
    require(before_map.keys() == after_map.keys(), "trial changed window identities")
    # A protected window is *not* eligible as proof of an improvement objective.
    def nonstillness(row):
        c=row["components"]
        return .25*c["sourceOveruse"]+.20*c["recentRepetition"]+\
               .15*c["noveltyDeficit"]+.10*c["transitionJolt"]
    rows = [{"id":k, "protected":k in protected,
             "before":before_map[k]["weaknessScore"],
             "after":after_map[k]["weaknessScore"],
             "delta":round(after_map[k]["weaknessScore"]-before_map[k]["weaknessScore"],6),
             "nonStillnessDelta":round(nonstillness(after_map[k])-nonstillness(before_map[k]),6)}
            for k in before_map]
    review = None
    if human_review is not None:
        require(isinstance(human_review, dict) and
                set(human_review) == {"decision","operatorAttestationId"} and
                human_review["decision"] in ("KEEP","SCRAPE","HOLD"), "invalid human decision")
        bounded(human_review["operatorAttestationId"], "human attestation required")
        review = human_review
    measurable = [x for x in rows if not x["protected"]]
    aggregate = round(sum(x["nonStillnessDelta"] for x in measurable)/len(measurable),6) if measurable else None
    body = {"schema":TRIAL,"cycleSha256":cycle["cycleSha256"],
            "beforeReportSha256":digest(before),"afterReportSha256":digest(after),
            "beforeVideoSha256":before["sourceVideoSha256"],
            "afterVideoSha256":after["sourceVideoSha256"],
            "sameSongCoverage":True,"comparisonWindows":rows,
            "unprotectedMeanWeaknessDelta":aggregate,
            "technicalDeltaImproved":aggregate is not None and aggregate < 0,
            "automaticAcceptance":False,
            "humanReview":review,
            "authority":"measurement-and-declared-human-review-only",
            "laws":["NUMERIC DELTA != ARTISTIC IMPROVEMENT",
                    "STILLNESS != WEAKNESS",
                    "TRIAL != PUBLISHED",
                    "HUMAN REVIEW REQUIRES AN EXPLICIT ACT"]}
    return {**body, "trialSha256":digest(body)}


def write_once(directory, record, identity_field):
    require(sha(record.get(identity_field)), "write needs a SHA-256 identity")
    require(digest({k:v for k,v in record.items() if k != identity_field}) == record[identity_field],
            "write refuses tampered record")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    dest = root / (record[identity_field]+".json")
    blob = json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False,
                      allow_nan=False).encode("utf-8") + b"\n"
    # Content-addressed and create-only. An existing differing blob is refusal.
    try:
        with dest.open("xb") as out: out.write(blob)
    except FileExistsError:
        require(dest.read_bytes() == blob, "existing evidence differs; overwrite refused")
    return str(dest)


def cli():
    p = argparse.ArgumentParser(description="BAND-IQ evidence-only compositor")
    s = p.add_subparsers(dest="command", required=True)
    a=s.add_parser("propose")
    a.add_argument("input");a.add_argument("output_dir");a.add_argument("--previous")
    b=s.add_parser("compare")
    b.add_argument("cycle");b.add_argument("before");b.add_argument("after")
    b.add_argument("output_dir");b.add_argument("--human-review")
    args=p.parse_args()
    read=lambda name:json.loads(Path(name).read_text(encoding="utf-8"))
    if args.command=="propose":
        result=build_cycle(read(args.input),read(args.previous) if args.previous else None)
        out=write_once(args.output_dir,result,"cycleSha256")
        print(json.dumps({"cycle":out,"sha256":result["cycleSha256"],"proposals":6}))
    else:
        result=compare_trial(read(args.cycle),read(args.before),read(args.after),
                             read(args.human_review) if args.human_review else None)
        out=write_once(args.output_dir,result,"trialSha256")
        print(json.dumps({"trial":out,"sha256":result["trialSha256"],
                          "technicalDeltaImproved":result["technicalDeltaImproved"],
                          "automaticAcceptance":False}))


if __name__=="__main__":
    cli()
