"""Pinned Blender-native BAND-IQ donor door.

Only local, explicitly selected operations. No provider work, shell argument passing,
auto-KEEP, user-media uploads, or unpinned Blender imports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    from bridge.band_iq import digest, validate_report, write_once, require
except ModuleNotFoundError:
    from band_iq import digest, validate_report, write_once, require

BLENDER_SHA = "cf0256a49ac8aa879cf2a044847d248177fcfad9"
SCHEMA = "vidmage/band-iq-local-donor-receipt/v1"
OPS = {"scan-008f", "harvest-008h", "direct-008j", "material-008l"}


def pinned_blender(root):
    root = Path(root).expanduser().resolve(strict=True)
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True)
    require(proc.stdout.strip() == BLENDER_SHA, "untrusted or moved Blender donor checkout")
    require((root/"haunted_blender"/"weakest_window_doctor.py").is_file(),
            "pinned donor files missing")
    return root


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1_048_576), b""):
            h.update(chunk)
    return h.hexdigest()


def authorize(selection, operation):
    require(isinstance(selection, dict) and set(selection)==
            {"schema","operation","sourceRights","operatorAttestationId","allowLocalExecution",
             "allowPaidProviders","allowNetworkUpload"},
            "unsupported native authorization shape")
    require(selection["schema"]=="vidmage/band-iq-local-selection/v1" and
            selection["operation"]==operation and operation in OPS, "unknown or mismatched operation")
    require(selection["sourceRights"]=="creator-authorized", "material rights not attested")
    require(isinstance(selection["operatorAttestationId"],str) and
            0<len(selection["operatorAttestationId"].strip())<=512, "operator attestation required")
    require(selection["allowLocalExecution"] is True, "local execution needs explicit operator selection")
    require(selection["allowPaidProviders"] is False and
            selection["allowNetworkUpload"] is False, "external authority prohibited")
    return selection


def describe():
    return {
        "schema":"vidmage/band-iq-donor-capabilities/v1",
        "nativeBlenderPin":BLENDER_SHA,
        "operations":[
            {"id":"scan-008f","function":"weakest_window_doctor.scan",
             "outputs":["observed technical report"],"requiresHumanSelection":True},
            {"id":"harvest-008h","function":"parts_harvester.harvest",
             "outputs":["verified derivative parts"],"requiresHumanSelection":True},
            {"id":"direct-008j","function":"paper_director.render",
             "outputs":["new directed MP4 and native receipt"],"requiresHumanSelection":True},
            {"id":"material-008l","function":"material_surface.materialize_asset",
             "outputs":["treated PNG and native receipt"],"requiresHumanSelection":True},
        ],
        "compositionOnly":["playdeck-studio-011","vidmage-cross-001"],
        "optionalFutureNotInstalled":["sam3-object-tracking","depth-anything-3","pyscenedetect","vmaf"],
        "laws":["DONOR IMPORT != EXECUTION", "PROPOSED SHOT != PERFORMED SHOT",
                "NATIVE TECHNICAL SCORE != HUMAN AESTHETIC JUDGMENT",
                "LOCAL EXECUTION != PUBLICATION"]
    }


def run_selected(selection, *, blender_root, source, output, plan=None,
                 material=None, sample_fps=4):
    op = selection.get("operation")
    authorize(selection,op)
    pinned_blender(blender_root)
    # A caller must launch with PYTHONPATH containing the checked-out pinned
    # Blender root, not an unrelated installed copy.
    import haunted_blender
    imported = Path(haunted_blender.__file__).resolve() if getattr(haunted_blender,"__file__",None) \
        else Path(list(haunted_blender.__path__)[0]).resolve()
    require(imported.is_relative_to(Path(blender_root).resolve()),
            "Blender import is not from the independently pinned checkout")

    from haunted_blender import weakest_window_doctor, parts_harvester, paper_director, material_surface
    source = Path(source).expanduser().resolve(strict=True)
    output = Path(output).expanduser().resolve()
    require(source.is_file(), "source must be an actual local file")
    require(not output.exists(), "output path exists; create-only door")

    if op == "scan-008f":
        require(plan is not None, "native 008e source plan required")
        raw = json.loads(Path(plan).resolve(strict=True).read_text(encoding="utf8"))
        report = weakest_window_doctor.scan(source,raw,sample_fps=sample_fps)
        validate_report(report)
        observation = {"report":report,
                       "reportSha256":digest(report),
                       "sourceVideoSha256":sha_file(source)}
        # No user-media bytes are stored in the report; it holds local path and source hash.
        output.mkdir(parents=True,exist_ok=False)
        dest=output/"doctor.json"
        with dest.open("x",encoding="utf8") as f:json.dump(observation,f,indent=2,sort_keys=True)
        receipt = {"op":op,"resultPath":str(dest),"reportSha256":observation["reportSha256"]}
    elif op == "harvest-008h":
        result=parts_harvester.harvest(source,output,still_count=3)
        receipt = {"op":op,"harvestIdentity":result.get("id"),
                   "sourceSha256":sha_file(source),"resultSha256":digest(result)}
    elif op == "direct-008j":
        require(plan is not None, "native 008j plan required")
        native_plan=json.loads(Path(plan).resolve(strict=True).read_text(encoding="utf8"))
        require(native_plan.get("schema")==paper_director.PLAN_SCHEMA,"native 008j paper plan required")
        result=paper_director.render(source,native_plan,output)
        receipt = {"op":op,"sourceSha256":sha_file(source),
                   "outputSha256":sha_file(output),"nativeReceiptSha256":digest(result)}
    else:
        require(material in {"paper","cardboard","wood","clay","felt","plastic",
                             "foil","stone","wax","inked","ghost","junk-collage"},
                "unsupported material preset")
        result=material_surface.materialize_asset(source,output,material)
        receipt = {"op":op,"sourceSha256":sha_file(source),
                   "outputSha256":sha_file(output),"nativeReceiptSha256":digest(result),
                   "material":material}

    body={"schema":SCHEMA,"blenderPinnedSha":BLENDER_SHA,
          "sourceRights":"operator-attested",
          "attestationId":selection["operatorAttestationId"],
          "externalUpload":False,"paidProvider":False,"automaticKeep":False,
          "result":receipt,
          "laws":["EXECUTED != KEPT","RENDERED != PUBLISHED","MEASURED != JUDGED"]}
    sealed={**body,"receiptSha256":digest(body)}
    # Receipt separate from the produced media; no overwrite or implicit mutation.
    receipt_dir=output if op in {"scan-008f","harvest-008h"} else output.parent/"band-iq-receipts"
    witness=write_once(receipt_dir,sealed,"receiptSha256")
    return {"receipt":witness,"sha256":sealed["receiptSha256"],"result":receipt}


def cli():
    p=argparse.ArgumentParser(description="Explicit native Blender donor entry")
    sub=p.add_subparsers(dest="operation",required=True)
    sub.add_parser("capabilities")
    for op in sorted(OPS):
        s=sub.add_parser(op)
        s.add_argument("--selection",required=True)
        s.add_argument("--blender-root",required=True)
        s.add_argument("--source",required=True)
        s.add_argument("--output",required=True)
        s.add_argument("--plan")
        s.add_argument("--material")
        s.add_argument("--sample-fps",type=int,default=4)
    args=p.parse_args()
    if args.operation=="capabilities":
        print(json.dumps(describe(),indent=2));return
    sel=json.loads(Path(args.selection).read_text(encoding="utf8"))
    res=run_selected(sel,blender_root=args.blender_root,source=args.source,
                     output=args.output,plan=args.plan,material=args.material,
                     sample_fps=args.sample_fps)
    print(json.dumps(res,indent=2))


if __name__=="__main__":
    cli()
