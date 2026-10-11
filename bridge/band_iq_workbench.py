"""BAND-IQ 008: one local front door to the REAL source-pinned filmmaking rooms.

A single explicit private project map connects 004's A/B review and its 005/006
local question/experiment flows to a separately selected 007 A/C review.
This shell never reads an artistic judgment from numerical measurements, never
auto-chooses the latest experiment, and never renders on page open or navigation.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from . import band_iq as iq
from . import band_iq_ac_review as ac
from . import band_iq_next_question as nextq
from . import band_iq_question_lab as lab
from . import band_iq_review as review

PROFILE="vidmage/band-iq-008-private-workbench/v1"
CORE=("cycle","selection","vidmage_record","vidmage_movie",
      "playdeck_receipt","playdeck_movie","record_dir")
NEXT=("plan","cards","observation","audio","asset_root")
OPTIONAL=("blender_root","ac_record_dir")
IDENTITY="projectSha256"
MAX_CANDIDATES=160

def need(ok,message):
    iq.require(ok,message)

def pathstr(p):
    return str(Path(p).expanduser().resolve())

def load(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def make_profile(core, next_sources=None, blender_root=None, ac_record_dir=None):
    need(set(core)==set(CORE),"one exact old-film project seed required")
    source={k:pathstr(core[k]) for k in CORE}
    optional={}
    if next_sources is not None:
        need(set(next_sources)==set(NEXT),
             "next-question source map needs all five original inputs")
        optional={k:pathstr(next_sources[k]) for k in NEXT}
    if blender_root is not None:
        need(optional,"Blender observation needs native original project inputs")
    body={
        "schema":PROFILE,
        "original":source,
        "nextSources":optional,
        "nativeBlenderRoot":pathstr(blender_root) if blender_root is not None else None,
        "acRecordDir":pathstr(ac_record_dir) if ac_record_dir else
                       pathstr(Path(core["record_dir"])/"ac-reviews"),
        "purpose":"single owner-local movie workshop; source files stay in place",
        "publication":False,
        "automaticExecution":False,
    }
    return {**body,IDENTITY:iq.digest(body)}

def validate_profile(profile):
    need(isinstance(profile,dict) and profile.get("schema")==PROFILE and
         set(profile)=={"schema","original","nextSources","nativeBlenderRoot",
                        "acRecordDir","purpose","publication","automaticExecution",IDENTITY} and
         iq.sha(profile.get(IDENTITY)) and
         iq.digest({k:v for k,v in profile.items() if k!=IDENTITY})==profile[IDENTITY] and
         profile["publication"] is False and
         profile["automaticExecution"] is False and
         set(profile["original"])==set(CORE) and
         (profile["nextSources"]=={} or set(profile["nextSources"])==set(NEXT)) and
         (profile["nativeBlenderRoot"] is None or bool(profile["nextSources"])),
         "refuse incomplete, changed, or execution-authorizing project map")
    need(all(isinstance(x,str) and x and Path(x).is_absolute()
             for x in (list(profile["original"].values())+
                       list(profile["nextSources"].values())+
                       [profile["acRecordDir"]]+
                       ([profile["nativeBlenderRoot"]] if profile["nativeBlenderRoot"] else []))),
         "private project map requires explicit absolute local paths")
    return profile

class Workbench:
    def __init__(self,profile):
        self.profile=validate_profile(profile)
        self.first=review.ReviewBench(**profile["original"])
        self.ac_bench=None
        self.selected_pair=None
        self.token=secrets.token_urlsafe(32)
        self._lock=threading.Lock()
        opts=profile["nextSources"]
        if opts:
            self.first.enable_next_sources(**opts)
        if profile["nativeBlenderRoot"]:
            self.first.next_blender_root=profile["nativeBlenderRoot"]
        self.root=Path(profile["original"]["record_dir"])
        self.ac_dir=Path(profile["acRecordDir"])

    def _roots(self):
        # Fixed, owner-approved 005/006 destination directories.
        return (self.root/"next-trials"/"band-iq-005-revisions",
                self.root/"question-observations")

    def discover(self):
        revisions,observations=self._roots()
        bad=0
        rev={}
        obs={}
        # Scanning only two fixed locations avoids crawling unrelated files.
        for directory,schema,field,target in (
            (revisions,nextq.REVISION,"revisionSha256",rev),
            (observations,lab.SCHEMA,"observationSha256",obs),
        ):
            if not directory.exists():continue
            paths=sorted(directory.glob("*.json"))
            need(len(paths)<=MAX_CANDIDATES,
                 "too many workshop receipts; explicit project scoping required")
            for source in paths:
                try:
                    doc=nextq.ensure_record(load(source),schema,field)
                    need(source.name==doc[field]+".json",
                         "source receipt filename must equal its complete SHA")
                    target[doc[field]]=(source,doc)
                except (OSError,KeyError,TypeError,ValueError,UnicodeError):
                    bad+=1
        return rev,obs,bad

    def entries(self):
        revisions,observations,bad=self.discover()
        original=self.first.get_decision()
        result=[]
        for rid,(revision_path,revision) in revisions.items():
            if original is None or revision.get("sourceReviewSha256")!=original["reviewSha256"]:
                continue
            compatible=[
                (oid,path,obs) for oid,(path,obs) in observations.items()
                if obs.get("sourceRevisionSha256")==rid and
                   obs.get("sourceReviewSha256")==original["reviewSha256"]
            ]
            if compatible:
                for oid,path,ob in compatible:
                    result.append({
                        "key":rid+":"+oid,
                        "revisionSha256":rid,"observationSha256":oid,
                        "experiment":revision.get("experimentKind","UNKNOWN"),
                        "question":revision.get("humanQuestionVerbatim",""),
                        "sourceFilmSha256":revision.get("newMovieSha256"),
                        "evidence":"measured","selectionRequired":True,
                    })
            else:
                result.append({
                    "key":rid,"revisionSha256":rid,"observationSha256":None,
                    "experiment":revision.get("experimentKind","UNKNOWN"),
                    "question":revision.get("humanQuestionVerbatim",""),
                    "sourceFilmSha256":revision.get("newMovieSha256"),
                    "evidence":"rendered-not-measured","selectionRequired":True,
                })
        result.sort(key=lambda item:(item["revisionSha256"],
                                      item["observationSha256"] or ""))
        return result,bad

    def restore_revision(self,revision_sha):
        need(iq.sha(revision_sha),"exact prior revision receipt identity required")
        revisions,observations,bad=self.discover()
        need(revision_sha in revisions,
             "prior revision receipt is not a known private project artifact")
        path,record=revisions[revision_sha]
        source=self.first.get_decision()
        need(source is not None and source["decision"]=="ANOTHER_EXPERIMENT" and
             record["sourceReviewSha256"]==source["reviewSha256"] and
             record["humanQuestionVerbatim"]==source["nextQuestion"] and
             record["originalVidmageMovieSha256"]==self.first.pair["vidmageFilmSha256"] and
             record["originalPlaydeckMovieSha256"]==self.first.pair["playdeckFilmSha256"] and
             record["humanKeep"] is False and record["publish"] is False,
             "restored revision must belong to this original human question")
        proof=nextq.reopen_revision(path)
        need(proof["revisionSha256"]==record["revisionSha256"] and
             proof["movieSha256"]==record["newMovieSha256"],
             "reopened source bytes do not identify this third film")
        if self.first.next_sources is not None:
            questions=nextq.question_set(self.first,*self.first.next_sources)
            need(questions["questionSetSha256"]==record["questionSetSha256"],
                 "original question or previously authorized source selection moved")
        self.first.next_result={
            "revisionRecord":str(path),
            "film":record["outputLocalPath"],
            "movieSha256":record["newMovieSha256"],
            "revisionSha256":record["revisionSha256"],
        }
        return self.first.next_result

    def select(self,revision_sha,observation_sha):
        need(iq.sha(revision_sha) and iq.sha(observation_sha),
             "select an exact revision and measured observation receipt")
        with self._lock:
            revisions,observations,bad=self.discover()
            need(revision_sha in revisions and observation_sha in observations,
                 "chosen local A/C evidence was not found")
            candidate=observations[observation_sha][1]
            need(candidate.get("sourceRevisionSha256")==revision_sha,
                 "revision and observation are unrelated")
            opts=self.profile["original"]
            bench=ac.ACReviewBench(**opts,
                revision=revisions[revision_sha][0],
                observation=observations[observation_sha][0],
                ac_record_dir=self.ac_dir)
            self.restore_revision(revision_sha)
            self.ac_bench=bench
            self.selected_pair=(revision_sha,observation_sha)
            return bench.state()

    def state(self):
        first_choice=self.first.get_decision()
        candidates,bad=self.entries()
        active=self.ac_bench
        second=active.get_decision() if active else None
        question=first_choice.get("nextQuestion") if first_choice else None
        steps=[
            {"id":"bring","name":"Bring","verb":"The source has a home",
             "status":"verified","detail":"Original source-pinned project and paired MP4s"},
            {"id":"listen","name":"Listen","verb":"Hear what exists",
             "status":"ready" if self.first.next_sources else "not-configured",
             "detail":"Verified song, Paper Director plan and authored scene cards"},
            {"id":"make","name":"Make","verb":"Two performances",
             "status":"verified","detail":"Actual VidMage A and native Playdeck B"},
            {"id":"wonder","name":"Wonder","verb":"The first human choice",
             "status":"recorded" if first_choice else "awaiting-human",
             "detail":"Watch A/B, choose, or write the next question"},
            {"id":"revise","name":"Revise","verb":"One chosen experiment",
             "status":"recorded" if candidates else
                      "ready" if question else "not-yet",
             "detail":"One authorized local image, focus or camera revision"},
            {"id":"notice","name":"Notice","verb":"Look at what changed",
             "status":"observed" if any(e["observationSha256"] for e in candidates) else
                      "not-yet",
             "detail":"Actual native scans and measured picture windows"},
            {"id":"choose","name":"Choose","verb":"Original, or revised?",
             "status":"recorded" if second else "ready" if active else
                      "available" if any(e["observationSha256"] for e in candidates) else
                      "not-yet",
             "detail":"Another independent human A/C choice"},
        ]
        return {
            "schema":"vidmage/band-iq-008-workbench-status/v1",
            "projectSha256":self.profile[IDENTITY],
            "token":self.token,
            "title":"One song, many possible films",
            "questionVerbatim":question or None,
            "firstReviewDecision":first_choice["decision"] if first_choice else None,
            "firstReviewSha256":first_choice["reviewSha256"] if first_choice else None,
            "originalFilmSha256":self.first.pair["vidmageFilmSha256"],
            "alternateFilmSha256":self.first.pair["playdeckFilmSha256"],
            "steps":steps,
            "candidates":candidates,
            "ignoredInvalidReceipts":bad,
            "activeRevision":self.first.next_result["revisionSha256"]
                              if self.first.next_result else None,
            "activePair":None if not active else {
                 "revisionSha256":self.selected_pair[0],
                 "observationSha256":self.selected_pair[1],
                 "comparisonSha256":active.pair["comparisonSha256"],
                 "reviewed":second is not None,
                 "decision":second["decision"] if second else None,
            },
            "doors":{
                "originalReview":"/room",
                "revisedReview":"/ac/" if active else None,
            },
            "constraints":{
                "localOnly":True,"noImplicitRender":True,
                "noAutomaticKeep":True,"noRelease":True,
                "storedProjectMapIsPrivate":True,
                "twoRealFilmRenderers":True,
            },
        }

class WorkbenchHandler(ac.ACHandler):
    workbench:Workbench=None
    ui_dir=Path(__file__).resolve().parent.parent/"ui"

    def _static(self,path):
        if getattr(self,"_ac_route",False):
            return ac.ACHandler._static(self,path)
        return review.Handler._static(self,path)

    def _own(self,name):
        names={
            "/":"band_iq_workbench.html",
            "/workbench.js":"band_iq_workbench.js",
            "/workbench.css":"band_iq_workbench.css",
        }
        source=names.get(name)
        if not source:
            self._error(404,"unknown workbench route");return
        file=self.ui_dir/source
        if not file.is_file():
            self._error(500,"workbench visual missing");return
        blob=file.read_bytes()
        typ=("text/html" if source.endswith(".html") else
             "text/javascript" if source.endswith(".js") else "text/css")
        self._headers(200,typ+"; charset=utf-8",len(blob))
        if self.command!="HEAD":self.wfile.write(blob)

    def _delegate(self,kind,method,route):
        # Only internal, known routes; the original A/B and revised A/C
        # handlers still enforce their own source and permission rules.
        old_path=self.path
        self.path=route
        self.bench=self.workbench.ac_bench if kind=="ac" else self.workbench.first
        self._ac_route=(kind=="ac")
        try:
            if kind=="ac":
                getattr(ac.ACHandler,method)(self)
            else:
                getattr(review.Handler,method)(self)
        finally:
            self.path=old_path
            self._ac_route=False
            self.bench=None

    def do_GET(self):
        route=urlsplit(self.path).path
        if route in ("/","/workbench.js","/workbench.css"):
            return self._own(route)
        if route=="/api/workbench/status":
            return self._json(200,self.workbench.state())
        if route=="/room":
            return self._delegate("first","do_GET","/")
        if route in ("/review.js","/review.css","/api/context","/api/next/questions",
                     "/media/a","/media/b","/media/next"):
            return self._delegate("first","do_GET",self.path)
        if route.startswith("/ac/"):
            if self.workbench.ac_bench is None:
                return self._error(409,"select actual measured A/C source pair first")
            return self._delegate("ac","do_GET",self.path[3:])
        return self._error(404,"fixed local workshop routes only")

    def do_HEAD(self):self.do_GET()

    def do_POST(self):
        route=urlsplit(self.path).path
        if route in ("/api/workbench/select","/api/workbench/restore"):
            expected="http://127.0.0.1:"+str(self.server.server_port)
            if (self.headers.get("Host")!=expected.removeprefix("http://") or
                self.headers.get("Origin")!=expected or
                self.headers.get("X-Workbench-Token")!=self.workbench.token):
                return self._error(403,"workbench select needs same-origin owner capability")
            if self.headers.get("Content-Type","").split(";")[0]!="application/json":
                return self._error(415,"JSON choice required")
            try:
                length=int(self.headers.get("Content-Length","0"))
                need(0<length<=1000,"choice form too large")
                body=json.loads(self.rfile.read(length))
                if route=="/api/workbench/select":
                    need(isinstance(body,dict) and set(body)=={
                         "revisionSha256","observationSha256"},
                         "choose exact observation pair, never arbitrary local paths")
                    chosen=self.workbench.select(body["revisionSha256"],body["observationSha256"])
                    return self._json(200,{"ok":True,"ac":chosen})
                need(isinstance(body,dict) and set(body)=={"revisionSha256"},
                     "only a known prior revision can be resumed")
                resumed=self.workbench.restore_revision(body["revisionSha256"])
                return self._json(200,{"ok":True,"trial":resumed})
            except (OSError,ValueError,KeyError,TypeError):
                return self._error(409,"A/C source choice refused; verify local evidence")
        if route in ("/api/decision","/api/next/execute","/api/next/observe"):
            return self._delegate("first","do_POST",self.path)
        if route.startswith("/ac/"):
            if self.workbench.ac_bench is None:
                return self._error(409,"explicit A/C pair selection required")
            return self._delegate("ac","do_POST",self.path[3:])
        return self._error(404,"no such workshop action")

def serve(workbench,port=8766,open_browser=False):
    need(type(port)==int and 0<=port<=65535,"invalid loopback port")
    class LocalWorkbench(WorkbenchHandler):pass
    LocalWorkbench.workbench=workbench
    http=ThreadingHTTPServer(("127.0.0.1",port),LocalWorkbench)
    if open_browser:
        import webbrowser
        webbrowser.open("http://127.0.0.1:"+str(http.server_port)+"/")
    print(json.dumps({"url":"http://127.0.0.1:"+str(http.server_port)+"/",
                      "status":"source-pinned-one-door-local-workbench",
                      "projectSha256":workbench.profile[IDENTITY]}),flush=True)
    return http

def cli():
    parser=argparse.ArgumentParser(
        description="BAND-IQ 008: private source-pinned filmmaker's living workbench")
    sub=parser.add_subparsers(dest="action",required=True)
    init=sub.add_parser("init",help="once: seal a local profile of your EXISTING source files")
    init.add_argument("--output",required=True)
    for name in CORE:
        init.add_argument("--"+name.replace("_","-"),required=True)
    for name in NEXT:
        init.add_argument("--next-"+name.replace("_","-"))
    init.add_argument("--blender-root")
    init.add_argument("--ac-record-dir")
    launch=sub.add_parser("open",help="later: open the same real source project with ONE map")
    launch.add_argument("--project",required=True)
    launch.add_argument("--port",type=int,default=8766)
    launch.add_argument("--open-browser",action="store_true")
    args=parser.parse_args()
    if args.action=="init":
        core={k:getattr(args,k) for k in CORE}
        candidates=[getattr(args,"next_"+k) for k in NEXT]
        need(all(x is not None for x in candidates) or all(x is None for x in candidates),
             "supply all five optional next source paths or none")
        originals={k:getattr(args,"next_"+k) for k in NEXT} if all(
            x is not None for x in candidates) else None
        profile=make_profile(core,originals,args.blender_root,args.ac_record_dir)
        Workbench(profile)  # verify true original A/B pair and optional source input
        outfile=Path(args.output).expanduser().resolve()
        outfile.parent.mkdir(parents=True,exist_ok=True)
        # Put local absolute file paths only into owner-readable config.
        descriptor=os.open(outfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,"w",encoding="utf8") as handle:
            json.dump(profile,handle,indent=2,sort_keys=True)
            handle.write("\n")
        print(json.dumps({"project":str(outfile),
                          "status":"private-local-project-sealed",
                          "next":"python -m bridge.band_iq_workbench open --project "+str(outfile)}))
    else:
        bench=Workbench(load(args.project))
        server=serve(bench,args.port,args.open_browser)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()

if __name__=="__main__":
    cli()
