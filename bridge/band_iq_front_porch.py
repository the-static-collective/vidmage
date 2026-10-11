"""BAND-IQ 009: one song + owned pictures -> explicit first native A/B film door.

Owner-local, loopback-only and create-only. Browser supplies bytes but NO disk path,
shell args, provider permission, output path, arbitrary camera code, publication
permission or authority to execute without a second named human action.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_film_loop as film_loop
from . import band_iq_playdeck_native as native
from . import band_iq_workbench as workbench
from . import scene_card_film as film
from . import band_iq_storytable as story

PORCH="vidmage/band-iq-009-owned-intake/v1"
PREPARED="vidmage/band-iq-009-paper-tray/v1"
PERFORMANCE="vidmage/band-iq-009-first-double-film/v1"
IMAGE_LIMIT=12
MIN_IMAGES=2
IMAGE_BYTES=12*1024*1024
AUDIO_BYTES=36*1024*1024
MAX_SECONDS=360.0
AUDIO_SUFFIXES={".wav",".mp3",".m4a",".flac",".ogg"}
IMAGE_SUFFIXES={".jpg",".jpeg",".png",".webp"}
HELD_LENSES=tuple(native.GRAMMAR)
NAME_LIMIT=160

def need(ok,reason):iq.require(ok,reason)
def read(path):return json.loads(Path(path).read_text(encoding="utf8"))
def write_exclusive(path,data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with path.open("x",encoding="utf8") as stream:
        json.dump(data,stream,sort_keys=True,indent=2,ensure_ascii=False)
        stream.write("\n")
    return path

def pinned_toaster(root):
    root=Path(root).expanduser().resolve(strict=True)
    sha=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
                       check=True,capture_output=True,text=True).stdout.strip()
    need(sha=="3652c2a96b6b287cda316d1c92daadf7c7417eaf",
         "Toaster source checkout changed")
    need((root/"src/full-measure/src/render/analyze.cjs").is_file(),
         "actual Toaster audio engine missing")
    return root

def duration_probe(path):
    out=subprocess.check_output([
        "ffprobe","-v","error","-select_streams","a:0",
        "-show_entries","stream=codec_name:format=duration",
        "-of","json",str(path)],text=True,timeout=30)
    data=json.loads(out)
    duration=float(data["format"]["duration"])
    need(iq.finite(duration,.8,MAX_SECONDS),"song must last 0.8–360 seconds")
    need(data["streams"],"actual decodable audio stream required")
    return duration

def verify_photo(raw):
    from PIL import Image
    from PIL import UnidentifiedImageError
    try:
        with Image.open(io.BytesIO(raw)) as image:
            need(image.format in ("PNG","JPEG","WEBP"),"unsupported image format")
            need(16<=image.width<=12000 and 16<=image.height<=12000 and
                 image.width*image.height<=24_000_000,
                 "image size outside bounded, safe local limits")
            image.verify()
    except (UnidentifiedImageError,OSError,ValueError) as e:
        raise ValueError("image must decode correctly") from e

def store_bytes(path,data):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,"wb") as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())

def native_blender(root):
    root=donors.pinned_blender(root)
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    from haunted_blender import paper_director,scene_growth,weakest_window_doctor
    for module in (paper_director,scene_growth,weakest_window_doctor):
        need(Path(module.__file__).resolve().is_relative_to(root),
             "imported Blender module not from source-pinned native checkout")
    return paper_director,scene_growth,weakest_window_doctor

def approve_intake(body):
    need(isinstance(body,dict) and set(body)=={
         "title","operatorAttestationId","ownedOrLicensed","allowLocalDerivatives",
         "noPublicRelease","allowNetworkUpload","allowPaidProviders"},
         "front porch requires exact plain-language creator consent")
    need(isinstance(body["title"],str) and 0<len(body["title"].strip())<=120,
         "song/project title required")
    iq.bounded(body["operatorAttestationId"],"creator identity/attestation required",256)
    need(body["ownedOrLicensed"] is True and
         body["allowLocalDerivatives"] is True and
         body["noPublicRelease"] is True and
         body["allowNetworkUpload"] is False and
         body["allowPaidProviders"] is False,
         "owner must explicitly authorize local source transformations only")
    return body

def authorize_first_movie(body,prepared):
    need(isinstance(body,dict) and set(body)=={
         "paperTraySha256","lensId","operatorAttestationId",
         "makeOneLocalABPair","allowPaidProviders","allowNetworkUpload",
         "allowPublicRelease","acknowledgeUnselectedTrials"},
         "first film request requires a new separate exact author action")
    need(body["paperTraySha256"]==prepared["paperTraySha256"] and
         body["lensId"] in HELD_LENSES and
         body["makeOneLocalABPair"] is True and
         body["acknowledgeUnselectedTrials"] is True and
         body["allowPaidProviders"] is False and
         body["allowNetworkUpload"] is False and
         body["allowPublicRelease"] is False,
         "one explicit private unselected A/B experiment required")
    iq.bounded(body["operatorAttestationId"],
               "new film authorization needs second creator attestation",256)
    return body

class FrontPorch:
    def __init__(self,workspace,*,blender_root,toaster_root,playdeck_root):
        self.root=Path(workspace).expanduser().resolve()
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        need(self.root.is_dir() and not self.root.is_symlink(),
             "private workspace must be a real local directory")
        self.original=self.root/"original"
        self.stills=self.root/"owned-stills"
        self.audio=self.root/"working-audio"
        self.tray=self.root/"paper-tray"
        self.films=self.root/"first-films"
        self.records=self.root/"human-reviews"
        self.token=secrets.token_urlsafe(32)
        self.lock=threading.RLock()
        self.blender_root=Path(blender_root).expanduser().resolve()
        self.toaster_root=Path(toaster_root).expanduser().resolve()
        self.playdeck_root=Path(playdeck_root).expanduser().resolve()
        self.intake_path=self.root/"consent.json"
        self.tray_path=self.tray/"proposal.json"
        self.story_dir=self.root/"storytable"
        self.story_path=self.story_dir/"story-seal.json"
        self.story_cards_path=self.story_dir/"authored-scene-cards.json"
        self.profile_path=self.root/"private-workbench.json"
        self.performance_path=self.root/"first-performance.json"
        self.workbench=None
        if self.profile_path.is_file():
            profile=workbench.validate_profile(read(self.profile_path))
            self.workbench=workbench.Workbench(profile)
            self.verify_completed()

    def _uploads(self):
        image_dir=self.original/"images"
        photos=sorted(image_dir.glob("image-*")) if image_dir.exists() else []
        photos=[p for p in photos if p.is_file() and
                re.fullmatch(r"image-\d\d\d\.(?:png|jpg|jpeg|webp)",p.name)]
        song=[p for p in self.original.glob("song.*") if p.is_file() and
              p.suffix.lower() in AUDIO_SUFFIXES] if self.original.exists() else []
        need(len(song)<=1 and len(photos)<=IMAGE_LIMIT,"ambiguous source staging")
        return song[0] if song else None,photos

    def upload(self,kind,filename,raw):
        with self.lock:
            need(not self.intake_path.exists() and
                 not self.tray_path.exists() and not self.profile_path.exists(),
                 "source intake is sealed; open a fresh workspace for another project")
            need(type(raw)==bytes,"actual file bytes required")
            name=Path(filename).name
            need(len(filename)<=NAME_LIMIT and name==filename and
                 not any(ord(c)<32 for c in name),"file name must be a short basename")
            suffix=Path(name).suffix.lower()
            song,photos=self._uploads()
            if kind=="audio":
                need(song is None and suffix in AUDIO_SUFFIXES and
                     80<=len(raw)<=AUDIO_BYTES,"one supported 36MB-or-smaller song required")
                target=self.original/("song"+suffix)
                store_bytes(target,raw)
                try:duration_probe(target)
                except Exception:
                    target.unlink(missing_ok=True)
                    raise
            elif kind=="image":
                need(suffix in IMAGE_SUFFIXES and len(photos)<IMAGE_LIMIT and
                     100<=len(raw)<=IMAGE_BYTES,
                     "up to twelve supported 12MB-or-smaller owned images")
                verify_photo(raw)
                index=len(photos)+1
                target=self.original/"images"/("image-%03d"%index+suffix)
                store_bytes(target,raw)
            else:
                raise ValueError("only a song or an owned still image may be brought")
            return {"kind":kind,"sourceSha256":donors.sha_file(target),
                    "sourceCount":len(self._uploads()[1]),
                    "audioPresent":self._uploads()[0] is not None}

    def intake(self,form):
        with self.lock:
            need(not self.intake_path.exists(),"consent receipt is create-only")
            approve_intake(form)
            song,photos=self._uploads()
            need(song is not None and MIN_IMAGES<=len(photos)<=IMAGE_LIMIT,
                 "bring one song and at least two actual images before authorizing")
            duration=duration_probe(song)
            refs=[{"id":"image-%03d"%(i+1),
                   "sourceSha256":donors.sha_file(path),
                   "originalNameOnDisk":path.name}
                  for i,path in enumerate(photos)]
            body={
                "schema":PORCH,
                "title":form["title"].strip(),
                "operatorAttestationId":form["operatorAttestationId"].strip(),
                "rightsAttested":True,"localDerivativesAuthorized":True,
                "providerPermission":False,"externalUploadPermission":False,
                "publicReleasePermission":False,
                "originalAudioSha256":donors.sha_file(song),
                "originalAudioNameOnDisk":song.name,
                "observedAudioSeconds":round(duration,6),
                "originalImages":refs,
                "imageAssignmentRule":"source order by uploaded image number; artist may revise after films",
                "status":"owned-input-authorized-no-film-permission",
                "laws":["UPLOADED != OWNED WITHOUT ATTESTATION",
                        "SOURCE != DERIVATIVE","PREPARE != RENDER",
                        "RIGHTS FOR LOCAL DERIVATIVES != PUBLIC RELEASE"],
            }
            receipt={**body,"intakeSha256":iq.digest(body)}
            write_exclusive(self.intake_path,receipt)
            return receipt

    def verify_intake(self):
        from . import band_iq_next_question as nextq
        receipt=nextq.ensure_record(read(self.intake_path),PORCH,"intakeSha256")
        song,photos=self._uploads()
        need(song is not None and donors.sha_file(song)==receipt["originalAudioSha256"],
             "original song changed after permission")
        need(len(photos)==len(receipt["originalImages"]) and
             all(p.name==r["originalNameOnDisk"] and
                 donors.sha_file(p)==r["sourceSha256"]
                 for p,r in zip(photos,receipt["originalImages"])),
             "owned original stills changed after permission")
        return receipt,song,photos

    def prepare(self):
        with self.lock:
            if self.tray_path.exists():
                return self.verify_tray()
            consent,song,photos=self.verify_intake()
            need(not self.profile_path.exists(),"the initial films already exist")
            # The user separately approved creating local audio/image derivatives
            # when attesting the first song, not any motion/publish operation.
            pinned_toaster(self.toaster_root)
            native.check_playdeck_checkout(self.playdeck_root)
            paper_director,scene_growth,_=native_blender(self.blender_root)
            from PIL import Image,ImageOps
            work=self.root/"preparing"
            need(not work.exists(),"prior incomplete local preparation must be inspected")
            work.mkdir(mode=0o700)
            try:
                samples=work/"song.wav"
                subprocess.run(["ffmpeg","-y","-nostdin","-v","error",
                    "-i",str(song),"-vn","-ac","1","-ar","22050","-c:a","pcm_s16le",
                    str(samples)],check=True,timeout=100)
                normalized_duration=duration_probe(samples)
                need(abs(normalized_duration-consent["observedAudioSeconds"])<.12,
                     "working song would materially alter original duration")
                authored_stills={}
                for i,p in enumerate(photos):
                    name="source-%03d.png"%(i+1)
                    dest=work/name
                    with Image.open(p) as source:
                        image=ImageOps.exif_transpose(source).convert("RGB")
                        target=ImageOps.contain(image,(640,360))
                        frame=Image.new("RGB",(640,360),(22,32,28))
                        frame.paste(target,((640-target.width)//2,(360-target.height)//2))
                        frame.save(dest,format="PNG")
                    authored_stills["p%03d"%(i+1)]={
                        "path":name,"mode":"subject","focus":[.5,.5],
                    }
                obs_file=work/"toaster-observation.json"
                subprocess.run(["node","bridge/toaster_lbranch_capture.cjs",
                                "--toaster-root",str(self.toaster_root),
                                "--audio",str(samples),"--out",str(obs_file)],
                               check=True,capture_output=True,text=True,timeout=120)
                observation=read(obs_file)
                iq.validate_audio(observation)
                timing=scene_growth.normalize_timing({
                    "schemaVersion":"0.1",
                    "id":"porch-song-"+consent["originalAudioSha256"][:18],
                    "duration":float(normalized_duration),
                    "gates":[{"id":"song-start","at":0,"kind":"verse",
                              "label":"Start of owned track; no lyric inference"}],
                })
                plan=paper_director.plan(timing)
                keys=sorted(authored_stills)
                cards={
                    "schema":"vidmage/editorial-scene-cards/v1",
                    "status":"proposal-only",
                    "assets":authored_stills,
                    "shots":[{"shotId":s["id"],
                             "assetId":keys[i%len(keys)],
                             "kineticSafe":False}
                             for i,s in enumerate(plan["shots"])],
                }
                film.validate(plan,cards,observation,work)
                body={
                    "schema":PREPARED,"intakeSha256":consent["intakeSha256"],
                    "sourceOriginalAudioSha256":consent["originalAudioSha256"],
                    "audioSha256":donors.sha_file(samples),
                    "normalizedDurationSeconds":round(normalized_duration,6),
                    "stillSha256":film_loop.exact_asset_bindings(cards,work),
                    "paperPlanSha256":iq.digest(plan),
                    "sceneCardsSha256":iq.digest(cards),
                    "toasterObservationSha256":iq.digest(observation),
                    "blenderCommitSha256":donors.BLENDER_SHA,
                    "toasterCommitSha256":"3652c2a96b6b287cda316d1c92daadf7c7417eaf",
                    "playdeckCommitSha256":native.PLAYDECK_SHA,
                    "selectedLens":None,"filmRendered":False,
                    "status":"prepared-without-render-permission",
                    "laws":["PREVIEW != PERFORMANCE","ONE IMAGE ASSIGNMENT != ARTISTIC FINAL",
                            "PAPER PLAN != MANUAL EDITOR APPROVAL",
                            "READY != PUBLICATION"],
                }
                proposal={**body,"paperTraySha256":iq.digest(body)}
                # Keep the working source material and its proof in one
                # owner-local folder. Never mutate originals.
                self.tray.mkdir(parents=True,exist_ok=True,mode=0o700)
                for p in work.iterdir():
                    p.rename(self.tray/p.name)
                write_exclusive(self.tray/"paper-plan.json",plan)
                write_exclusive(self.tray/"scene-cards.json",cards)
                write_exclusive(self.tray_path,proposal)
                return proposal
            finally:
                if work.exists():shutil.rmtree(work)

    def verify_tray(self):
        from . import band_iq_next_question as nextq
        consent,song,photos=self.verify_intake()
        p=nextq.ensure_record(read(self.tray_path),PREPARED,"paperTraySha256")
        plan=read(self.tray/"paper-plan.json")
        cards=read(self.tray/"scene-cards.json")
        observation=read(self.tray/"toaster-observation.json")
        audio=self.tray/"song.wav"
        need(p["intakeSha256"]==consent["intakeSha256"] and
             p["sourceOriginalAudioSha256"]==donors.sha_file(song) and
             p["audioSha256"]==donors.sha_file(audio) and
             p["paperPlanSha256"]==iq.digest(plan) and
             p["sceneCardsSha256"]==iq.digest(cards) and
             p["toasterObservationSha256"]==iq.digest(observation) and
             p["stillSha256"]==film_loop.exact_asset_bindings(cards,self.tray),
             "prepared song/images/shot proposal changed")
        film.validate(plan,cards,observation,self.tray)
        return p

    def seal_story(self,form):
        with self.lock:
            need(not self.story_path.exists() and not self.profile_path.exists(),
                 "storytable is already sealed; do not rewrite a human choice")
            paper=self.verify_tray()
            plan=read(self.tray/"paper-plan.json")
            original=read(self.tray/"scene-cards.json")
            receipt,cards=story.author(form,paper,plan,original,self.tray)
            self.story_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
            write_exclusive(self.story_cards_path,cards)
            write_exclusive(self.story_path,receipt)
            need(self.verify_story()[0]==receipt,
                 "source-authored shot table failed to reopen")
            return receipt

    def verify_story(self):
        paper=self.verify_tray()
        need(self.story_path.is_file() and self.story_cards_path.is_file(),
             "artist must seal the complete storytable BEFORE either film")
        return story.verified(self.story_path,self.story_cards_path,paper,
            read(self.tray/"paper-plan.json"),
            read(self.tray/"scene-cards.json"),self.tray)

    def make(self,choice):
        with self.lock:
            need(not self.profile_path.exists(),"initial A/B pair already completed")
            proposal=self.verify_tray()
            # 010 makes story authorship a hard prerequisite. One cannot
            # bypass the human's shot arrangement via the older render door.
            need(isinstance(choice,dict) and "storySha256" in choice,
                 "render needs the separate sealed human Storytable receipt")
            story_receipt,cards=self.verify_story()
            need(choice["storySha256"]==story_receipt["storySha256"],
                 "film authorization references the wrong owner-arranged shots")
            authorize_first_movie({k:v for k,v in choice.items()
                                   if k!="storySha256"},proposal)
            _,_,doctor=native_blender(self.blender_root)
            native.check_playdeck_checkout(self.playdeck_root)
            pinned_toaster(self.toaster_root)
            plan=read(self.tray/"paper-plan.json")
            # Cards are the actual author-sealed shot occurrences,
            # never the machine's original provisional assignments.
            observation=read(self.tray/"toaster-observation.json")
            audio=self.tray/"song.wav"
            self.films.mkdir(parents=True,exist_ok=True,mode=0o700)
            # Every separately approved attempt is a distinct folder.
            attempt=len(list(self.films.glob("attempt-*")))+1
            attempt_dir=self.films/("attempt-%03d"%attempt)
            attempt_dir.mkdir(mode=0o700)
            baseline=attempt_dir/"baseline.mp4"
            film.render(plan,cards,observation,audio,self.tray,baseline)
            attrib=film_loop.doctor_scene_attribution_plan(plan,cards,self.tray)
            before=doctor.scan(baseline,attrib,window_seconds=2.0)
            iq.validate_report(before)
            # Nothing may infer that stillness is wrong. The artist's second
            # act explicitly authorizes motion REVIEW in the first window.
            first=before["windows"][0]
            annotation=[{
                "windowId":first["id"],
                "kind":"motion-review-authorized",
                "operatorAttestationId":choice["operatorAttestationId"],
                "sourceVideoSha256":before["sourceVideoSha256"],
            }]
            cycle=iq.build_cycle({
                "schema":iq.INPUT,"doctorReport":before,
                "audioObservation":observation,"artistAnnotations":annotation})
            iq.verify_cycle(cycle)
            matching=[p for p in cycle["imagine"]
                      if p["lensId"]==choice["lensId"] and p["status"]=="proposal-only"]
            need(len(matching)==1,
                 "native movie proposal unavailable; no arbitrary fallback")
            chosen=matching[0]
            selection={
                "schema":film_loop.SELECTION,
                "cycleSha256":cycle["cycleSha256"],
                "proposalSha256":chosen["proposalSha256"],
                "operatorAttestationId":choice["operatorAttestationId"],
                "decision":"RENDER_TRIAL",
                "allowLocalExecution":True,
                "allowPaidProviders":False,
                "allowNetworkUpload":False,
                "sourceVideoSha256":before["sourceVideoSha256"],
                "paperPlanSha256":iq.digest(plan),
                "sceneCardsSha256":iq.digest(cards),
                "audioObservationSha256":iq.digest(observation),
                "audioSha256":donors.sha_file(audio),
                "assetBindings":film_loop.exact_asset_bindings(cards,self.tray),
            }
            a=attempt_dir/"vidmage-a.mp4"
            record,record_path=film_loop.render_selected(
                cycle,before,selection,plan,cards,observation,
                audio,self.tray,baseline,a)
            b=attempt_dir/"native-playdeck-b.mp4"
            receipt,receipt_path=native.render_native(
                cycle=cycle,before=before,selection=selection,
                plan=plan,cards=cards,observation=observation,
                audio=audio,asset_root=self.tray,
                baseline_movie=baseline,playdeck_root=self.playdeck_root,
                output=b)
            native.compare_native_pair(
                cycle=cycle,selection=selection,vidmage_film_record=record,
                vidmage_movie=a,playdeck_receipt=receipt,playdeck_movie=b,
                output_dir=attempt_dir/"comparison")
            cycle_file=write_exclusive(attempt_dir/"cycle.json",cycle)
            sel_file=write_exclusive(attempt_dir/"selection.json",selection)
            profile=workbench.make_profile(
                {"cycle":cycle_file,"selection":sel_file,
                 "vidmage_record":record_path,"vidmage_movie":a,
                 "playdeck_receipt":receipt_path,"playdeck_movie":b,
                 "record_dir":self.records},
                {"plan":self.tray/"paper-plan.json",
                 "cards":self.story_cards_path,
                 "observation":self.tray/"toaster-observation.json",
                 "audio":audio,"asset_root":self.tray},
                blender_root=self.blender_root)
            wb=workbench.Workbench(profile)
            completed={
                "schema":PERFORMANCE,
                "sourceIntakeSha256":read(self.intake_path)["intakeSha256"],
                "sourcePaperTraySha256":proposal["paperTraySha256"],
                "sourceStorySha256":story_receipt["storySha256"],
                "authoredCardsSha256":story_receipt["authoredCardsSha256"],
                "humanRenderAttestation":choice["operatorAttestationId"],
                "selectedLens":choice["lensId"],
                "cycleSha256":cycle["cycleSha256"],
                "selectedProposalSha256":chosen["proposalSha256"],
                "vidmageFilmSha256":donors.sha_file(a),
                "playdeckFilmSha256":donors.sha_file(b),
                "sourceProfileSha256":profile["projectSha256"],
                "status":"two-real-films-await-human-review",
                "selectedForKeep":False,"published":False,
                "allowProviderSpend":False,"networkUploaded":False,
                "laws":["FIRST RENDER != KEEP","TWO FILMS != TWO RELEASES",
                        "ARTIST'S LENS CHOICE != ARTIST'S FINAL CUT"],
            }
            performed={**completed,"performanceSha256":iq.digest(completed)}
            write_exclusive(self.performance_path,performed)
            # Owner-readable local path map; no private bytes in GitHub.
            fd=os.open(self.profile_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,"w",encoding="utf8") as out:
                json.dump(profile,out,indent=2,sort_keys=True)
                out.write("\n")
            self.workbench=wb
            return performed

    def verify_completed(self):
        from . import band_iq_next_question as nextq
        p=nextq.ensure_record(read(self.performance_path),PERFORMANCE,"performanceSha256")
        tray=self.verify_tray()
        chosen_cards,source_cards=self.verify_story()
        consent,_,_=self.verify_intake()
        wb=self.workbench
        need(p["sourceStorySha256"]==chosen_cards["storySha256"] and
             p["authoredCardsSha256"]==chosen_cards["authoredCardsSha256"] and
             wb.profile["nextSources"]["cards"]==str(self.story_cards_path.resolve()) and
             p["sourceIntakeSha256"]==consent["intakeSha256"] and
             p["sourcePaperTraySha256"]==tray["paperTraySha256"] and
             p["vidmageFilmSha256"]==wb.first.pair["vidmageFilmSha256"] and
             p["playdeckFilmSha256"]==wb.first.pair["playdeckFilmSha256"] and
             p["sourceProfileSha256"]==wb.profile["projectSha256"] and
             p["selectedForKeep"] is False and p["published"] is False,
             "front porch completed session contradicts actual film evidence")
        return p

    def state(self):
        with self.lock:
            song,photos=self._uploads()
            consent=read(self.intake_path) if self.intake_path.is_file() else None
            prepared=read(self.tray_path) if self.tray_path.is_file() else None
            sealed=self.verify_story()[0] if self.story_path.is_file() else None
            performed=self.verify_completed() if self.workbench else None
            stage=("films-ready" if performed else
                   "paper-tray" if prepared else
                   "consented" if consent else "bring")
            return {
                "schema":"vidmage/band-iq-009-front-porch-ui/v1",
                "stage":stage,"token":self.token,
                "song":None if not song else {
                    "storedName":song.name,"sha256":donors.sha_file(song),
                    "durationSeconds":round(duration_probe(song),3)},
                "images":[{
                    "id":"image-%03d"%(i+1),"name":p.name,
                    "sha256":donors.sha_file(p),
                    "url":"/api/porch/photo/"+("image-%03d"%(i+1))}
                    for i,p in enumerate(photos)],
                "consent":None if not consent else {
                    "title":consent["title"],"sha256":consent["intakeSha256"]},
                "paper":None if not prepared else {
                    "paperTraySha256":prepared["paperTraySha256"],
                    "durationSeconds":prepared["normalizedDurationSeconds"],
                    "sourceCount":len(photos),
                    "lensIds":list(HELD_LENSES),
                    "preparedOnly":True},
                "storytable":None if not prepared else {
                    "paperTraySha256":prepared["paperTraySha256"],
                    "sealed":sealed is not None,
                    "storySha256":sealed["storySha256"] if sealed else None,
                    "shots":[{
                        "shotId":row["id"],
                        "start":row["start"],"end":row["end"],
                        "sourceAssetId":(
                            sealed["shotAssignments"][i]["sourceAssetId"]
                            if sealed else read(self.tray/"scene-cards.json")["shots"][i]["assetId"]),
                        "focus":sealed["shotAssignments"][i]["focus"]
                                if sealed else [.5,.5],
                        "protectText":sealed["shotAssignments"][i]["protectText"]
                                      if sealed else False,
                    } for i,row in enumerate(read(self.tray/"paper-plan.json")["shots"])],
                    "images":[{
                        "assetId":aid,
                        "url":"/api/porch/photo/image-%03d"%(i+1),
                        "sha256":prepared["stillSha256"][aid],
                    } for i,aid in enumerate(sorted(
                        read(self.tray/"scene-cards.json")["assets"]))],
                    "timingIsNativeBlenderPaperPlan":True,
                    "noFilmRenderedBySealing":True,
                },
                "films":None if not performed else {
                    "originalVidmageSha256":performed["vidmageFilmSha256"],
                    "nativePlaydeckSha256":performed["playdeckFilmSha256"],
                    "selectedLens":performed["selectedLens"],
                    "reviewUrl":"/room"},
                "limits":{"maxAudioMB":36,"maxImageMB":12,"maxImages":IMAGE_LIMIT,
                          "minImages":MIN_IMAGES,"maxSongSeconds":MAX_SECONDS},
                "constraints":{"ownerLocal":True,"noAutomaticRender":True,
                               "noExternalUpload":True,"noPublication":True,
                               "noAutomaticKeep":True},
            }

class PorchHandler(workbench.WorkbenchHandler):
    porch:FrontPorch=None
    ui_dir=Path(__file__).resolve().parent.parent/"ui"

    def _files(self,path):
        mapping={"/porch":"band_iq_front_porch.html",
                 "/porch.js":"band_iq_front_porch.js",
                 "/porch.css":"band_iq_front_porch.css"}
        name=mapping.get(path)
        if name is None:return self._error(404,"unknown porch resource")
        file=self.ui_dir/name
        if not file.is_file():return self._error(500,"front porch visual missing")
        data=file.read_bytes()
        mime=("text/html" if name.endswith(".html") else
              "text/javascript" if name.endswith(".js") else "text/css")
        self._headers(200,mime+"; charset=utf-8",len(data))
        if self.command!="HEAD":self.wfile.write(data)

    def do_GET(self):
        route=urlsplit(self.path).path
        if route=="/" and self.porch.workbench is None:
            return self._files("/porch")
        if route in ("/porch","/porch.js","/porch.css"):
            return self._files(route)
        if route=="/api/porch/story/audio":
            try:
                prepared=self.porch.verify_tray()
                file=self.porch.tray/"song.wav"
                need(donors.sha_file(file)==prepared["audioSha256"],
                     "song bytes changed since the native paper arrangement")
                length=file.stat().st_size
                need(0<length<=AUDIO_BYTES,"bounded working audio unavailable")
                header=self.headers.get("Range")
                if header:
                    found=re.fullmatch(r"bytes=(\\d*)-(\\d*)",header)
                    need(found and (found.group(1) or found.group(2)),
                         "invalid audio range")
                    left,right=found.groups()
                    if left:
                        start=int(left)
                        end=min(int(right),length-1) if right else length-1
                    else:
                        start=max(0,length-int(right))
                        end=length-1
                    need(start<length and end>=start,"unsatisfiable audio range")
                    extras={"Accept-Ranges":"bytes",
                            "Content-Range":f"bytes {start}-{end}/{length}"}
                    code=206
                else:
                    start,end=0,length-1
                    extras={"Accept-Ranges":"bytes"};code=200
                self._headers(code,"audio/wav",end-start+1,extras)
                if self.command=="HEAD":return
                with file.open("rb") as src:
                    src.seek(start)
                    remaining=end-start+1
                    while remaining:
                        part=src.read(min(1024*1024,remaining))
                        if not part:break
                        self.wfile.write(part)
                        remaining-=len(part)
            except (OSError,ValueError,KeyError,TypeError):
                if not self.wfile.closed:
                    try:self.connection.close()
                    except OSError:pass
            except (BrokenPipeError,ConnectionResetError):
                pass
            return
        if route=="/api/porch/state":
            try:return self._json(200,self.porch.state())
            except (OSError,ValueError,KeyError,TypeError):
                return self._error(409,"private source file or receipt has changed")
        if route.startswith("/api/porch/photo/"):
            try:
                token=route.removeprefix("/api/porch/photo/")
                need(re.fullmatch(r"image-\d\d\d",token),
                     "only explicitly uploaded numbered local stills can be previewed")
                _,photos=self.porch._uploads()
                number=int(token.split("-")[-1])
                need(1<=number<=len(photos),"image not present")
                path=photos[number-1]
                # Fixed bounded source files only, no browser-selected path.
                original=path.read_bytes()
                need(len(original)<=IMAGE_BYTES,"photo changed size")
                mime="image/png" if path.suffix==".png" else (
                    "image/webp" if path.suffix==".webp" else "image/jpeg")
                self._headers(200,mime,len(original))
                if self.command!="HEAD":self.wfile.write(original)
            except (OSError,ValueError,KeyError):
                self._error(404,"no such authorized private still")
            return
        if self.porch.workbench is None:
            return self._error(404,"no film rooms exist until the creator authorizes A/B")
        self.workbench=self.porch.workbench
        return workbench.WorkbenchHandler.do_GET(self)

    def do_HEAD(self):self.do_GET()

    def do_POST(self):
        route=urlsplit(self.path).path
        if route not in ("/api/porch/upload","/api/porch/consent",
                         "/api/porch/prepare","/api/porch/story/seal",
                         "/api/porch/make"):
            if self.porch.workbench is None:
                return self._error(404,"no other action before the first films")
            self.workbench=self.porch.workbench
            return workbench.WorkbenchHandler.do_POST(self)
        host=self.headers.get("Host","")
        expected="http://127.0.0.1:"+str(self.server.server_port)
        if (self.headers.get("Origin")!=expected or
            host!=expected.removeprefix("http://") or
            self.headers.get("X-Porch-Token")!=self.porch.token):
            return self._error(403,"front porch owner-local capability missing")
        try:
            length=int(self.headers.get("Content-Length","0"))
            cap=(AUDIO_BYTES if self.headers.get("X-Porch-Kind")=="audio"
                 else IMAGE_BYTES if self.headers.get("X-Porch-Kind")=="image"
                 else 75000 if route=="/api/porch/story/seal"
                 else 3000)
            need(0<length<=cap,"local file or approval exceeds bounded size")
            content_type=self.headers.get("Content-Type","").split(";")[0].lower()
            if route=="/api/porch/upload":
                need(content_type=="application/octet-stream",
                     "raw browser file bytes required")
                outcome=self.porch.upload(
                    self.headers.get("X-Porch-Kind",""),
                    unquote(self.headers.get("X-Porch-Name","")),
                    self.rfile.read(length))
            else:
                need(content_type=="application/json",
                     "creator consent must be an exact JSON form")
                form=json.loads(self.rfile.read(length))
                if route=="/api/porch/consent":outcome=self.porch.intake(form)
                elif route=="/api/porch/prepare":
                    need(form=={"prepareLocalPaper":True},
                         "paper preparation needs a separate explicit action")
                    outcome=self.porch.prepare()
                elif route=="/api/porch/story/seal":
                    outcome=self.porch.seal_story(form)
                else:outcome=self.porch.make(form)
            return self._json(201,{"ok":True,"receipt":outcome,"state":self.porch.state()})
        except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError,
                subprocess.TimeoutExpired,ImportError,RuntimeError) as exc:
            return self._error(409,"local request refused: "+str(exc)[:220])

def serve(porch,port=8767,open_browser=False):
    need(type(port)==int and 0<=port<=65535,"invalid loopback-only port")
    class ThisPorch(PorchHandler):pass
    ThisPorch.porch=porch
    server=ThreadingHTTPServer(("127.0.0.1",port),ThisPorch)
    if open_browser:
        import webbrowser
        webbrowser.open("http://127.0.0.1:"+str(server.server_port)+"/")
    print(json.dumps({"url":"http://127.0.0.1:"+str(server.server_port)+"/",
                      "status":"private-first-song-porch",
                      "alreadyMade":porch.workbench is not None}),flush=True)
    return server

def main():
    p=argparse.ArgumentParser(description="BAND-IQ 009 owned song/image Front Porch")
    p.add_argument("--workspace",required=True)
    p.add_argument("--blender-root",required=True)
    p.add_argument("--toaster-root",required=True)
    p.add_argument("--playdeck-root",required=True)
    p.add_argument("--port",type=int,default=8767)
    p.add_argument("--open-browser",action="store_true")
    args=p.parse_args()
    porch=FrontPorch(args.workspace,blender_root=args.blender_root,
                     toaster_root=args.toaster_root,playdeck_root=args.playdeck_root)
    server=serve(porch,args.port,args.open_browser)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=="__main__":main()
