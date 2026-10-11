"""BAND-IQ 009: actual media intake + separate verified first-film authorization."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from bridge import band_iq as iq
from bridge import band_iq_front_porch as porch
from bridge import band_iq_donors as donors


def song_bytes(root,duration=3):
    target=root/"sample.wav"
    subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                    "-i",f"sine=frequency=440:duration={duration}:sample_rate=22050",
                    "-ac","1",str(target)],check=True)
    return target.read_bytes()

def image_bytes(index):
    from PIL import Image,ImageDraw
    result=io.BytesIO()
    img=Image.new("RGB",(500,320),((index*81)%255,(index*31+60)%255,
                                    (index*63+91)%255))
    draw=ImageDraw.Draw(img)
    for j in range(11):
        draw.rectangle((j*43, j*18,j*43+35,j*18+83),
                       fill=((j*37+45)%255,(j*11+63)%255,(j*27+9)%255))
    draw.line((0,10,430,310),fill=(255,255,255),width=8)
    img.save(result,format="PNG")
    return result.getvalue()

def source_consent():
    return {"title":"An owned little song",
            "operatorAttestationId":"human-first-permission",
            "ownedOrLicensed":True,"allowLocalDerivatives":True,
            "noPublicRelease":True,
            "allowNetworkUpload":False,"allowPaidProviders":False}

def first_authorization(prepared):
    return {"paperTraySha256":prepared["paperTraySha256"],
            "lensId":"landscape",
            "operatorAttestationId":"human-second-chooses-landscape",
            "makeOneLocalABPair":True,
            "allowPaidProviders":False,"allowNetworkUpload":False,
            "allowPublicRelease":False,"acknowledgeUnselectedTrials":True}


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "requires real local audio probe")
class PorchPureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.porch=porch.FrontPorch(
            self.root/"workspace",
            blender_root=self.root/"missing-blender",
            toaster_root=self.root/"missing-toaster",
            playdeck_root=self.root/"missing-playdeck")

    def tearDown(self):
        self.tmp.cleanup()

    def stage(self):
        song=song_bytes(self.root,3)
        original_hash=donors.sha_file(song)
        audio=self.porch.upload("audio","source.wav",song.read_bytes())
        self.assertEqual(audio["sourceSha256"],original_hash)
        for index in (1,2):
            self.porch.upload("image",f"photo-{index}.png",image_bytes(index))
        return original_hash

    def test_no_film_until_creative_and_source_authorities_are_distinct(self):
        self.assertEqual(self.porch.state()["stage"],"bring")
        original=self.stage()
        self.assertEqual(len(self.porch.state()["images"]),2)
        self.assertEqual(self.porch.state()["song"]["sha256"],original)
        with self.assertRaisesRegex(ValueError,"owner must explicitly"):
            self.porch.intake({**source_consent(),"allowNetworkUpload":True})
        receipt=self.porch.intake(source_consent())
        self.assertTrue(iq.sha(receipt["intakeSha256"]))
        self.assertFalse(receipt["publicReleasePermission"])
        self.assertEqual(self.porch.state()["stage"],"consented")
        self.assertFalse(self.porch.profile_path.exists())
        self.assertFalse(self.porch.films.exists())
        with self.assertRaisesRegex(ValueError,"source intake is sealed"):
            self.porch.upload("image","late.png",image_bytes(3))
        with self.assertRaisesRegex(ValueError,"create-only"):
            self.porch.intake(source_consent())
        with self.assertRaises((FileNotFoundError,ValueError)):
            self.porch.prepare()
        self.assertFalse(self.porch.profile_path.exists())
        self.assertEqual(self.porch.verify_intake()[0],receipt)

    def test_audio_and_photo_are_real_decodable_local_data(self):
        data=song_bytes(self.root,2)
        with self.assertRaisesRegex(ValueError,"file name"):
            self.porch.upload("audio","../../hello.wav",data)
        with self.assertRaisesRegex(ValueError,"image"):
            self.porch.upload("image","broken.png",b"not an image"*30)
        with self.assertRaisesRegex(ValueError,"supported"):
            self.porch.upload("audio","blocked.exe",data)
        with self.assertRaisesRegex(ValueError,"song"):
            self.porch.intake(source_consent())
        self.assertEqual(self.porch.state()["images"],[])

    def test_original_media_change_is_refused_before_prepare(self):
        self.stage()
        self.porch.intake(source_consent())
        _,photos=self.porch._uploads()
        photos[0].write_bytes(photos[0].read_bytes()+b"forged")
        with self.assertRaisesRegex(ValueError,"owned original stills changed"):
            self.porch.verify_intake()

    def test_first_render_needs_new_named_explicit_authority(self):
        ready={"paperTraySha256":"a"*64}
        self.assertEqual(porch.authorize_first_movie(first_authorization(ready),ready)
                         ["lensId"],"landscape")
        for changes in [
            {"allowPaidProviders":True},
            {"allowNetworkUpload":True},
            {"allowPublicRelease":True},
            {"makeOneLocalABPair":False},
            {"acknowledgeUnselectedTrials":False},
            {"paperTraySha256":"b"*64},
        ]:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    porch.authorize_first_movie(
                        {**first_authorization(ready),**changes},ready)
        with self.assertRaisesRegex(ValueError,"new film authorization"):
            porch.authorize_first_movie(
                {**first_authorization(ready),"operatorAttestationId":""},ready)

    def test_local_browser_fixed_paths_and_uploads_reject_csrf(self):
        with contextlib.redirect_stdout(io.StringIO()):
            server=porch.serve(self.porch,port=0)
        runner=threading.Thread(target=server.serve_forever,daemon=True);runner.start()
        try:
            base=f"http://127.0.0.1:{server.server_port}"
            with urlopen(base+"/") as r:
                html=r.read().decode()
                self.assertIn("A song. Some pictures.",html)
                self.assertIn("default-src 'none'",r.headers["Content-Security-Policy"])
            for path in ("/porch.js","/porch.css"):
                with urlopen(base+path) as r:self.assertGreater(len(r.read()),500)
            with urlopen(base+"/api/porch/state") as r:
                status=json.load(r)
            self.assertEqual(status["stage"],"bring")
            song=song_bytes(self.root,2)
            body=song.read_bytes()
            forged=Request(base+"/api/porch/upload",data=body,headers={
                 "Origin":"https://attacker.invalid",
                 "X-Porch-Token":status["token"],
                 "X-Porch-Kind":"audio","X-Porch-Name":"song.wav",
                 "Content-Type":"application/octet-stream"})
            with self.assertRaises(HTTPError) as denied:urlopen(forged)
            self.assertEqual(denied.exception.code,403)
            self.assertIsNone(self.porch._uploads()[0])
            accepted=Request(base+"/api/porch/upload",data=body,headers={
                 "Origin":base,"X-Porch-Token":status["token"],
                 "X-Porch-Kind":"audio","X-Porch-Name":"song.wav",
                 "Content-Type":"application/octet-stream"})
            with urlopen(accepted) as r:self.assertEqual(r.status,201)
            for i in (1,2):
                accepted=Request(base+"/api/porch/upload",data=image_bytes(i),headers={
                     "Origin":base,"X-Porch-Token":status["token"],
                     "X-Porch-Kind":"image","X-Porch-Name":f"photo-{i}.png",
                     "Content-Type":"application/octet-stream"})
                with urlopen(accepted) as r:self.assertEqual(r.status,201)
            with urlopen(base+"/api/porch/photo/image-001") as r:
                self.assertEqual(r.headers["Content-Type"],"image/png")
                self.assertGreater(len(r.read()),500)
            with self.assertRaises(HTTPError) as blocked:
                urlopen(base+"/api/porch/photo/../../source.wav")
            self.assertEqual(blocked.exception.code,404)
            with self.assertRaises(HTTPError) as no_portal:
                urlopen(base+"/api/workbench/status")
            self.assertEqual(no_portal.exception.code,404)
            payload=json.dumps(source_consent()).encode()
            approved=Request(base+"/api/porch/consent",data=payload,headers={
                 "Origin":base,"X-Porch-Token":status["token"],
                 "Content-Type":"application/json"})
            with urlopen(approved) as r:
                self.assertEqual(json.load(r)["state"]["stage"],"consented")
            with self.assertRaises(HTTPError) as duplicate:urlopen(approved)
            self.assertEqual(duplicate.exception.code,409)
        finally:
            server.shutdown();server.server_close();runner.join(timeout=3)


@unittest.skipUnless(
    os.environ.get("VIDMAGE_BLENDER_ROOT") and
    os.environ.get("VIDMAGE_TOASTER_ROOT") and
    os.environ.get("VIDMAGE_PLAYDECK_ROOT") and
    shutil.which("ffmpeg") and shutil.which("node"),
    "requires installed exact native donors, ffmpeg and Node")
class PorchNativeTests(unittest.TestCase):
    def test_owned_song_to_actual_independent_two_film_workbench(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            project=porch.FrontPorch(
                root/"private-project",
                blender_root=os.environ["VIDMAGE_BLENDER_ROOT"],
                toaster_root=os.environ["VIDMAGE_TOASTER_ROOT"],
                playdeck_root=os.environ["VIDMAGE_PLAYDECK_ROOT"])
            source=song_bytes(root,4)
            old_sha=donors.sha_file(source)
            project.upload("audio","song.wav",source.read_bytes())
            for index in (1,2):
                project.upload("image",f"real-owned-photo-{index}.png",image_bytes(index))
            consent=project.intake(source_consent())
            prepared=project.prepare()
            self.assertTrue(prepared["preparedOnly"] if "preparedOnly" in prepared
                            else prepared["filmRendered"] is False)
            self.assertFalse(project.profile_path.exists())
            self.assertEqual(project.state()["stage"],"paper-tray")
            self.assertTrue((project.tray/"scene-cards.json").is_file())
            self.assertEqual(prepared["intakeSha256"],consent["intakeSha256"])
            for invalid in [
                {**first_authorization(prepared),"allowPublicRelease":True},
                {**first_authorization(prepared),"paperTraySha256":"0"*64},
            ]:
                with self.assertRaises(ValueError):
                    project.make(invalid)
            # Actual browser POST traverses the whole native rendering seam,
            # and the resulting route serves the genuine older workbench.
            with contextlib.redirect_stdout(io.StringIO()):
                server=porch.serve(project,port=0)
            runner=threading.Thread(target=server.serve_forever,daemon=True)
            runner.start()
            try:
                base=f"http://127.0.0.1:{server.server_port}"
                with urlopen(base+"/api/porch/state") as response:
                    state=json.load(response)
                decision=first_authorization(prepared)
                request=Request(base+"/api/porch/make",
                                data=json.dumps(decision).encode(),headers={
                      "Origin":base,"X-Porch-Token":state["token"],
                      "Content-Type":"application/json"})
                with urlopen(request,timeout=550) as response:
                    output=json.load(response)
                self.assertEqual(output["state"]["stage"],"films-ready")
                self.assertEqual(output["receipt"]["status"],
                                 "two-real-films-await-human-review")
                self.assertFalse(output["receipt"]["published"])
                self.assertFalse(output["receipt"]["selectedForKeep"])
                self.assertTrue(project.profile_path.is_file())
                self.assertEqual(project.profile_path.stat().st_mode & 0o777,0o600)
                self.assertEqual(donors.sha_file(project._uploads()[0]),old_sha)
                self.assertEqual(project.workbench.state()["steps"][3]["status"],
                                 "awaiting-human")
                with urlopen(base+"/") as response:
                    self.assertIn("Seven doors. One workbench.",response.read().decode())
                with urlopen(base+"/room") as response:
                    self.assertIn("Two films. One human decision.",response.read().decode())
                with urlopen(base+"/api/context") as response:
                    two=json.load(response)
                self.assertEqual(two["status"],"awaiting-human-review")
                for side in ("a","b"):
                    with urlopen(Request(base+"/media/"+side,
                                         headers={"Range":"bytes=0-63"})) as response:
                        self.assertEqual(response.status,206)
                        self.assertEqual(len(response.read()),64)
                # New independent explicit HUMAN choice, never inferred from
                # the presence of two completed movie outputs.
                review_body={
                    "decision":"KEEP_PLAYDECK",
                    "operatorAttestationId":"first-owner-actually-watches-and-chooses",
                    "rationale":"I prefer this version of my own materials.",
                    "nextQuestion":"",
                    "acknowledgedTrialOnly":True,
                }
                req=Request(base+"/api/decision",data=json.dumps(review_body).encode(),
                            headers={"Origin":base,
                              "X-Review-Token":two["reviewToken"],
                              "Content-Type":"application/json"})
                with urlopen(req) as response:
                    chosen=json.load(response)["receipt"]
                self.assertEqual(chosen["decision"],"KEEP_PLAYDECK")
                self.assertFalse(chosen["publicationAuthorized"])
                self.assertEqual(project.workbench.state()["firstReviewDecision"],
                                 "KEEP_PLAYDECK")
                self.assertEqual(donors.sha_file(project._uploads()[0]),old_sha)
                with self.assertRaises(HTTPError) as no_extra:urlopen(request)
                self.assertEqual(no_extra.exception.code,409)
                # Restart from the same PRIVATE folder: source proofs, actual
                # two original MP4s, and the real human review are intact.
                reopened=porch.FrontPorch(
                    project.root,
                    blender_root=os.environ["VIDMAGE_BLENDER_ROOT"],
                    toaster_root=os.environ["VIDMAGE_TOASTER_ROOT"],
                    playdeck_root=os.environ["VIDMAGE_PLAYDECK_ROOT"])
                self.assertEqual(reopened.state()["stage"],"films-ready")
                self.assertEqual(reopened.workbench.state()["firstReviewDecision"],
                                 "KEEP_PLAYDECK")
                self.assertEqual(reopened.verify_completed(),
                                 output["receipt"])
            finally:
                server.shutdown();server.server_close();runner.join(timeout=3)

if __name__=="__main__":unittest.main()
