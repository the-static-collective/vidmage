"""BAND-IQ 004: loopback-only human A/B video bench and durable chosen disposition.

Only a user-authored explicit decision can add review authority; source films,
original receipts, proposals and comparisons remain immutable. KEEP here means
'selected for further local work', not a final export, upstream merge or publication.
No cloud, arbitrary path browsing, paid provider, or media mutation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_playdeck_native as native

SCHEMA="vidmage/band-iq-human-review/v1"
DECISIONS={
    "KEEP_VIDMAGE":"selected-for-local-continuation",
    "KEEP_PLAYDECK":"selected-for-local-continuation",
    "SCRAPE_BOTH":"both-trials-declined",
    "ANOTHER_EXPERIMENT":"new-question-requested",
}
HEADERS={
    "Cache-Control":"no-store, no-cache, must-revalidate",
    "X-Content-Type-Options":"nosniff",
    "X-Frame-Options":"DENY",
    "Referrer-Policy":"no-referrer",
    "Cross-Origin-Resource-Policy":"same-origin",
    "Content-Security-Policy":"default-src 'none'; style-src 'self'; script-src 'self'; connect-src 'self'; media-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
}

def need(ok, message):
    iq.require(ok,message)

def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def validate_decision(body):
    need(isinstance(body,dict) and set(body)=={
        "decision","operatorAttestationId","rationale","nextQuestion","acknowledgedTrialOnly"},
        "explicit review form shape required")
    decision=body["decision"]
    need(decision in DECISIONS,"unknown review disposition")
    iq.bounded(body["operatorAttestationId"],"operator attestation required",256)
    need(body["acknowledgedTrialOnly"] is True,
         "review cannot imply export, publication or source overwrite")
    rationale=body["rationale"]
    need(isinstance(rationale,str) and len(rationale)<=2000,
         "review rationale must be bounded plain text")
    question=body["nextQuestion"]
    need(isinstance(question,str) and len(question)<=1200,
         "next experiment question must be bounded plain text")
    if decision=="ANOTHER_EXPERIMENT":
        iq.bounded(question,"another experiment needs an actual artist question",1200)
    else:
        need(not question.strip(),"future experiment question requires explicit experiment request")
    return body

class ReviewBench:
    """Local single-pair owner-selected interface, sealed once across restarts."""
    def __init__(self, *,cycle,selection,vidmage_record,vidmage_movie,
                 playdeck_receipt,playdeck_movie,record_dir):
        self.cycle=read(cycle)
        self.selection=read(selection)
        self.vidmage_record=read(vidmage_record)
        self.playdeck_receipt=read(playdeck_receipt)
        self.videos={
            "a":Path(vidmage_movie).expanduser().resolve(strict=True),
            "b":Path(playdeck_movie).expanduser().resolve(strict=True),
        }
        need(all(p.is_file() and p.suffix.lower()==".mp4" for p in self.videos.values()),
             "two existing local MP4s required")
        need(self.videos["a"] != self.videos["b"],"two independently rendered films required")
        self.root=Path(record_dir).expanduser().resolve()
        self.root.mkdir(parents=True,exist_ok=True)
        pair, path=native.compare_native_pair(
            cycle=self.cycle,
            selection=self.selection,
            vidmage_film_record=self.vidmage_record,vidmage_movie=self.videos["a"],
            playdeck_receipt=self.playdeck_receipt,playdeck_movie=self.videos["b"],
            output_dir=self.root/"pairs")
        self.pair=pair
        self.pair_path=path
        self.decision_path=self.root/("review-"+pair["comparisonSha256"]+".json")
        self._mutex=threading.Lock()
        self.token=secrets.token_urlsafe(32)
        self.fingerprints={
            side:self._fingerprint(path) for side,path in self.videos.items()
        }
        self.next_sources=None
        self.next_result=None
        self.next_blender_root=None
        self.last_observation=None
        self.get_decision()  # early refusal if a preexisting receipt is corrupted

    @staticmethod
    def _fingerprint(path):
        stat=path.stat()
        return (stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)

    def require_unchanged(self,side, *,cryptographic=False):
        path=self.videos[side]
        need(self._fingerprint(path)==self.fingerprints[side],
             "media source changed after review session began")
        if cryptographic:
            expected=self.pair["vidmageFilmSha256" if side=="a" else "playdeckFilmSha256"]
            need(donors.sha_file(path)==expected,
                 "real media bytes do not match verified pair")
        return path

    def get_decision(self):
        if not self.decision_path.exists():
            return None
        receipt=read(self.decision_path)
        need(isinstance(receipt,dict) and
             receipt.get("schema")==SCHEMA and
             receipt.get("comparisonSha256")==self.pair["comparisonSha256"] and
             iq.sha(receipt.get("reviewSha256")) and
             iq.digest({k:v for k,v in receipt.items() if k!="reviewSha256"})==receipt["reviewSha256"],
             "existing human review record failed independent readback")
        need(receipt.get("decision") in DECISIONS and
             receipt.get("outcome")==DECISIONS[receipt["decision"]] and
             receipt.get("automaticExecution") is False and
             receipt.get("publicationAuthorized") is False,
             "human review record claims unauthorized outcome")
        return receipt

    def enable_next_sources(self, *,plan,cards,observation,audio,asset_root):
        # An explicit local operator CLI action supplies the context. Viewing
        # an earlier review cannot infer permission or fetch media from elsewhere.
        self.next_sources=(read(plan),read(cards),read(observation),audio,asset_root)
        # Only validate executable source state once an actual next-question review exists.
        if (self.get_decision() or {}).get("decision")=="ANOTHER_EXPERIMENT":
            self.next_question_set()

    def next_question_set(self):
        need(self.next_sources is not None,
             "review room needs explicit local project inputs for next questions")
        from . import band_iq_next_question as nxt
        result=nxt.question_set(self,*self.next_sources)
        iq.write_once(self.root/"next-question-proposals",result,"questionSetSha256")
        return result

    def next_execute(self,selection):
        need(self.next_sources is not None,"next experiment sources are not configured")
        from . import band_iq_next_question as nxt
        with self._mutex:
            questions=self.next_question_set()
            # One local confirmed action produces at most one distinct output
            # in its own source-addressed destination, without touching either old film.
            prefix=questions["questionSetSha256"][:18]+"-"+iq.digest(selection)[:16]
            destination=self.root/"next-trials"/(prefix+".mp4")
            record,path=nxt.run_trial(self,questions,selection,*self.next_sources,destination)
            self.next_result={"revisionRecord":path,"film":str(destination),
                              "movieSha256":record["newMovieSha256"],
                              "revisionSha256":record["revisionSha256"]}
            return self.next_result

    def observe_next(self):
        # Explicit read-only in-room analysis is a separate human action;
        # only actual completed next trials may be analyzed.
        need(self.next_blender_root is not None and self.next_sources is not None and
             isinstance(self.next_result,dict),
             "native Doctor observation needs an existing performed local revision")
        from . import band_iq_question_lab as lab
        from . import band_iq_next_question as nxt
        revision=nxt.load(self.next_result["revisionRecord"])
        result,path=lab.observe(self,revision,*self.next_sources,
                                self.next_blender_root,self.root/"question-observations")
        self.last_observation={"observation":result,"receipt":path}
        return result

    def state(self):
        current=self.get_decision()
        proposal=next(p for p in self.cycle["imagine"]
                      if p["proposalSha256"]==self.selection["proposalSha256"])
        return {
            "schema":"vidmage/band-iq-review-ui/v1",
            "status":"recorded" if current else "awaiting-human-review",
            "reviewToken":self.token,
            "selection":{"lensId":proposal["lensId"],
                         "cameraMode":proposal["cameraMode"],
                         "targetStart":proposal["targetStart"],
                         "targetEnd":proposal["targetEnd"],
                         "operatorAttestationId":self.selection["operatorAttestationId"]},
            "source":{"audioSame":self.pair["sameSourceAudio"],
                      "imagesSame":self.pair["sameSourceImageSet"],
                      "questionSame":self.pair["sameOperatorSelectedQuestion"]},
            "renderers":{
                "a":{"title":"VidMage","description":"Local shot-and-camera director",
                     "url":"/media/a","sha256":self.pair["vidmageFilmSha256"]},
                "b":{"title":"Playdeck","description":"Native Remotion card-and-world director",
                     "url":"/media/b","sha256":self.pair["playdeckFilmSha256"]},
            },
            "comparisonSha256":self.pair["comparisonSha256"],
            "decision":current,
            "constraints":{"keepMeans":"chosen for further local continuation, NOT publication",
                           "publication":False,"export":False,"automaticEdit":False,
                           "creativeJudgmentByScore":False,
                           "nextQuestionToolsConfigured":self.next_sources is not None,
                           "nativeQuestionDoctorConfigured":self.next_blender_root is not None},
        }

    def commit(self,form):
        validate_decision(form)
        with self._mutex:
            need(self.get_decision() is None,
                 "human review already recorded; replay cannot change first choice")
            self.require_unchanged("a",cryptographic=True)
            self.require_unchanged("b",cryptographic=True)
            selected={
                "KEEP_VIDMAGE":"a",
                "KEEP_PLAYDECK":"b",
            }.get(form["decision"])
            body={
                "schema":SCHEMA,
                "comparisonSha256":self.pair["comparisonSha256"],
                "sourceCycleSha256":self.pair["sourceCycleSha256"],
                "sourceSelectionSha256":self.pair["selectionSha256"],
                "decision":form["decision"],
                "outcome":DECISIONS[form["decision"]],
                "operatorAttestationId":form["operatorAttestationId"].strip(),
                "rationale":form["rationale"],
                "nextQuestion":form["nextQuestion"].strip(),
                "chosenRenderer":selected,
                "chosenFilmSha256":(
                    self.pair["vidmageFilmSha256" if selected=="a" else "playdeckFilmSha256"]
                    if selected else None),
                "comparativeTechnicalScoreAsArtisticJudgment":False,
                "automaticExecution":False,
                "automaticKeep":False,
                "publicationAuthorized":False,
                "exportAuthorized":False,
                "sourceFilesModified":False,
                "nextExperimentPerformed":False,
                "laws":["VIEW != KEEP","HUMAN KEEP != PUBLICATION",
                        "SCRAPE != ERASURE","NEW QUESTION != EXECUTION",
                        "MEASUREMENT != TASTE","SAME CREATIVE QUESTION != SAME VIDEO"],
            }
            receipt={**body,"reviewSha256":iq.digest(body)}
            # A stable pair-addressed single decision file is created atomically.
            # Once written, another decision conflicts even if different hash.
            data=(json.dumps(receipt,sort_keys=True,indent=2,
                             ensure_ascii=False)+"\n").encode("utf8")
            try:
                with self.decision_path.open("xb") as dest:
                    dest.write(data)
                    dest.flush()
                    os.fsync(dest.fileno())
            except FileExistsError as exc:
                raise ValueError("BAND-IQ HOLD: human review already recorded") from exc
            need(self.get_decision()==receipt,"written review failed independent readback")
            return receipt

class Handler(BaseHTTPRequestHandler):
    bench: ReviewBench = None
    ui_dir = Path(__file__).resolve().parent.parent/"ui"
    def log_message(self,format,*args):
        # Never print private path names or posted operator attestations.
        return

    def _headers(self,code,content_type,length,extra=None):
        self.send_response(code)
        for k,v in HEADERS.items():
            self.send_header(k,v)
        self.send_header("Content-Type",content_type)
        self.send_header("Content-Length",str(length))
        for k,v in (extra or {}).items():
            self.send_header(k,v)
        self.end_headers()

    def _json(self,code,payload):
        body=iq.canonical(payload)
        self._headers(code,"application/json; charset=utf-8",len(body))
        if self.command!="HEAD":
            self.wfile.write(body)

    def _error(self,code,msg):
        self._json(code,{"ok":False,"status":"HOLD","message":msg})

    def _static(self,path):
        files={
            "/":"band_iq_review.html",
            "/review.js":"band_iq_review.js",
            "/review.css":"band_iq_review.css",
        }
        name=files.get(path)
        if not name:
            self._error(404,"unknown route")
            return
        source=self.ui_dir/name
        if not source.is_file():
            self._error(500,"static review surface unavailable")
            return
        blob=source.read_bytes()
        kind=("text/html" if name.endswith(".html") else
              "text/javascript" if name.endswith(".js") else "text/css")
        self._headers(200,kind+"; charset=utf-8",len(blob))
        if self.command!="HEAD":
            self.wfile.write(blob)

    def _video(self,side):
        try:
            if side=="next":
                trial=self.bench.next_result
                need(isinstance(trial,dict),"no independently performed next trial")
                path=Path(trial["film"]).resolve(strict=True)
                need(path.is_file() and donors.sha_file(path)==trial["movieSha256"],
                     "next trial file changed")
            else:
                path=self.bench.require_unchanged(side)
            length=path.stat().st_size
            need(length>0,"empty movie cannot be reviewed")
        except (OSError,ValueError):
            self._error(409,"media changed or unavailable")
            return
        try:
            rng=self.headers.get("Range")
            if rng:
                match=re.fullmatch(r"bytes=(\d*)-(\d*)",rng)
                if not match or (not match.group(1) and not match.group(2)):
                    self._error(416,"invalid media range")
                    return
                start_s,end_s=match.groups()
                if start_s:
                    start=int(start_s)
                    end=min(int(end_s),length-1) if end_s else length-1
                else:
                    suffix=int(end_s)
                    start=max(0,length-suffix)
                    end=length-1
                if start>=length or end<start:
                    self._error(416,"unsatisfiable media range")
                    return
                headers={"Accept-Ranges":"bytes",
                         "Content-Range":f"bytes {start}-{end}/{length}"}
                status=206
            else:
                start,end=0,length-1
                headers={"Accept-Ranges":"bytes"}
                status=200
            self._headers(status,"video/mp4",end-start+1,headers)
            if self.command=="HEAD":
                return
            with path.open("rb") as source:
                source.seek(start)
                remaining=end-start+1
                while remaining>0:
                    chunk=source.read(min(1024*1024,remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):
            pass
        except (OSError,ValueError):
            # Avoid attempting a second HTTP response after a partially sent body.
            if not self.wfile.closed:
                try: self.connection.close()
                except OSError: pass

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=="/api/context":
            self._json(200,self.bench.state())
        elif path=="/api/next/questions":
            try:
                question=self.bench.next_question_set()
                self._json(200,{"ok":True,"questions":question,
                                "trial":self.bench.next_result})
            except (ValueError,KeyError,OSError,TypeError):
                self._error(409,"next questions unavailable until human review and exact sources")
        elif path in ("/media/a","/media/b","/media/next"):
            self._video(path.rsplit("/",1)[-1])
        else:
            self._static(path)

    def do_POST(self):
        path=urlsplit(self.path).path
        if path not in ("/api/decision","/api/next/execute","/api/next/observe"):
            self._error(404,"unknown route")
            return
        # The loopback address alone does NOT establish CSRF or creator authorization.
        host=self.headers.get("Host","")
        origin=self.headers.get("Origin","")
        expected=f"http://127.0.0.1:{self.server.server_port}"
        if (self.headers.get("X-Review-Token")!=self.bench.token or
            origin!=expected or host!=expected.removeprefix("http://")):
            self._error(403,"review capability or same-origin boundary missing")
            return
        if self.headers.get("Content-Type","").split(";")[0].lower()!="application/json":
            self._error(415,"JSON form required")
            return
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=6000:
                self._error(413,"review form too large or empty")
                return
            data=json.loads(self.rfile.read(length))
            if path=="/api/decision":
                receipt=self.bench.commit(data)
                self._json(201,{"ok":True,"receipt":receipt})
            elif path=="/api/next/execute":
                need(isinstance(data,dict) and set(data)=={"authorization"},
                     "next execution needs one explicit authorization")
                result=self.bench.next_execute(data["authorization"])
                self._json(201,{"ok":True,"trial":result})
            else:
                need(data=={"inspectActualFilms":True},
                     "technical analysis requires a separate explicit user request")
                observation=self.bench.observe_next()
                self._json(200,{"ok":True,"observation":observation})
        except (ValueError,TypeError,KeyError,OSError,UnicodeError) as exc:
            self._error(409,"review refused; check explicit choice and source integrity")

def serve(bench,port=8764,open_browser=False):
    need(isinstance(port,int) and 0<=port<=65535,"invalid loopback port")
    class ThisReview(Handler):
        pass
    ThisReview.bench=bench
    server=ThreadingHTTPServer(("127.0.0.1",port),ThisReview)
    if open_browser:
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{server.server_port}/")
    print(json.dumps({"url":f"http://127.0.0.1:{server.server_port}/",
                      "status":"local-only-human-review",
                      "pairSha256":bench.pair["comparisonSha256"],
                      "existingReview":bench.get_decision() is not None}),flush=True)
    return server

def cli():
    p=argparse.ArgumentParser(description="BAND-IQ 004 local A/B human decision bench")
    for field in ("cycle","selection","vidmage-record","vidmage-movie",
                  "playdeck-receipt","playdeck-movie","record-dir"):
        p.add_argument("--"+field,required=True)
    for field in ("next-plan","next-cards","next-observation","next-audio","next-asset-root"):
        p.add_argument("--"+field)
    p.add_argument("--next-blender-root",help="explicit exact-pinned native Blender checkout for read-only 006 observation")
    p.add_argument("--port",type=int,default=8764)
    p.add_argument("--open-browser",action="store_true")
    args=p.parse_args()
    bench=ReviewBench(cycle=args.cycle,selection=args.selection,
        vidmage_record=args.vidmage_record,vidmage_movie=args.vidmage_movie,
        playdeck_receipt=args.playdeck_receipt,playdeck_movie=args.playdeck_movie,
        record_dir=args.record_dir)
    optional=[args.next_plan,args.next_cards,args.next_observation,
              args.next_audio,args.next_asset_root]
    need(all(v is None for v in optional) or all(v is not None for v in optional),
         "supply all five next-question project inputs or none")
    if all(v is not None for v in optional):
        bench.enable_next_sources(plan=args.next_plan,cards=args.next_cards,
                                  observation=args.next_observation,audio=args.next_audio,
                                  asset_root=args.next_asset_root)
    if args.next_blender_root is not None:
        need(bench.next_sources is not None,
             "native read-only question laboratory requires exact original project inputs")
        # Do not load arbitrary vendor code until actual user requests an inspection.
        bench.next_blender_root=args.next_blender_root
    http=serve(bench,args.port,open_browser=args.open_browser)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http.server_close()

if __name__=="__main__":
    cli()
