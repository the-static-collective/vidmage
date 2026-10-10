"""Owner-local VIDMAGE scene-card renderer.

Consumes native Toaster L BRANCH observations and native Blender Paper Director
shot boundaries, plus an explicitly authored asset-to-shot proposal. This is
VIDMAGE raster execution, NOT a claim to execute Blender's render() itself.
Optional kinetic motion is a separate, bypassable trial.
"""
import argparse, hashlib, json, math, subprocess, tempfile
from pathlib import Path
import cv2

WIDTH,HEIGHT,FPS=640,360,12

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def validate(plan,cards,bank,root):
    if plan.get("schema")!="haunted-blender/paper-director-plan/v1":raise ValueError("Native Blender shot plan required")
    if cards.get("schema")!="vidmage/editorial-scene-cards/v1" or cards.get("status")!="proposal-only":
        raise ValueError("Only explicitly proposed scene cards are supported")
    if bank.get("schema")!="vidmage/toaster-lbranch-observation/v1" or bank.get("laneBank",{}).get("schema")!="haunted-toaster/lane-bank/v1":
        raise ValueError("Native Toaster observation required")
    shots=plan.get("shots",[])
    choices=cards.get("shots",[])
    if not 1<=len(shots)<=256 or len(choices)!=len(shots):raise ValueError("Wrong shot count")
    duration=float(plan.get("durationSeconds",0))
    if not math.isfinite(duration) or not 0<duration<=3600:raise ValueError("Bad duration")
    cursor=0.
    for shot,choice in zip(shots,choices):
        start,end=float(shot["start"]),float(shot["end"])
        if not math.isfinite(start+end) or abs(start-cursor)>.015 or end<=start:raise ValueError("Gap/overlap in shot plan")
        if choice.get("shotId")!=shot["id"] or choice.get("assetId") not in cards.get("assets",{}):
            raise ValueError("Unbound editorial source")
        cursor=end
    if abs(cursor-duration)>.02:raise ValueError("Full-song coverage required")
    root=Path(root).resolve(strict=True)
    material={}
    for key,record in cards["assets"].items():
        target=(root/record["path"]).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file():raise ValueError("Asset escapes root")
        mode=record.get("mode","subject")
        if mode not in ("subject","protect-text"):raise ValueError("Unknown mode")
        focus=record.get("focus",[.5,.5])
        if len(focus)!=2 or any(not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=1 for x in focus):
            raise ValueError("Bad focus")
        image=cv2.imread(str(target))
        if image is None:raise ValueError("Unreadable source")
        material[key]={"image":image,"mode":mode,"focus":focus,"sha256":sha(target)}
    lanes={x["id"]:x["knots"] for x in bank["laneBank"]["lanes"]}
    if "raw-energy-envelope" not in lanes:raise ValueError("Missing raw energy")
    return duration,material,lanes

def value(knots,t):
    if not knots:return 0.
    if t<=knots[0]["atSeconds"]:return float(knots[0]["value"])
    for left,right in zip(knots,knots[1:]):
        if left["atSeconds"]<=t<=right["atSeconds"]:
            amount=(t-left["atSeconds"])/max(.00001,right["atSeconds"]-left["atSeconds"])
            return max(0.,min(1.,left["value"]*(1-amount)+right["value"]*amount))
    return float(knots[-1]["value"])

def pulse_times(knots):
    possible=sorted((x for x in knots if x["value"]>.32),key=lambda x:-x["value"])
    chosen=[]
    for item in possible:
        t=item["atSeconds"]
        if all(abs(t-other)>=5 for other in chosen):chosen.append(t)
        if len(chosen)==20:break
    return sorted(chosen)

def frame_for(source,progress,energy,pulse):
    image=source["image"];focus=source["focus"];mode=source["mode"]
    ih,iw=image.shape[:2]
    if mode=="protect-text":
        scale=min(WIDTH/iw,HEIGHT/ih)
        w,h=max(1,int(iw*scale)),max(1,int(ih*scale))
        fg=cv2.resize(image,(w,h))
        bg=cv2.GaussianBlur(cv2.resize(image,(WIDTH,HEIGHT)),(0,0),13)
        bg=cv2.convertScaleAbs(bg,alpha=.45,beta=0)
        x,y=(WIDTH-w)//2,(HEIGHT-h)//2
        bg[y:y+h,x:x+w]=fg
        return bg
    base_w=min(iw,int(ih*WIDTH/HEIGHT));base_h=int(base_w*HEIGHT/WIDTH)
    zoom=1.035+.028*progress+.038*energy*progress+.072*pulse
    cw,ch=max(24,int(base_w/zoom)),max(24,int(base_h/zoom))
    fx,fy=focus
    cx=int(iw*(fx+.025*(progress-.5)));cy=int(ih*(fy+.013*(progress-.5)))
    x=max(0,min(iw-cw,cx-cw//2));y=max(0,min(ih-ch,cy-ch//2))
    frame=cv2.resize(image[y:y+ch,x:x+cw],(WIDTH,HEIGHT),interpolation=cv2.INTER_AREA)
    if pulse>.04:
        matrix=cv2.getRotationMatrix2D((WIDTH/2,HEIGHT/2),pulse*1.05,1.008)
        frame=cv2.warpAffine(frame,matrix,(WIDTH,HEIGHT),borderMode=cv2.BORDER_REPLICATE)
    return frame

def render(plan,cards,observations,audio,root,output,kinetic=False):
    output=Path(output).resolve();audio=Path(audio).resolve(strict=True)
    if output.exists() or output.with_suffix(".receipt.json").exists():
        raise FileExistsError("Create-only: will not replace an output")
    duration,assets,lanes=validate(plan,cards,observations,root)
    pulses=pulse_times(lanes.get("transient-pressure",[])) if kinetic else []
    frames=round(duration*FPS)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vidmage-scenes-") as temp:
        silent=Path(temp)/"silent.mp4"
        command=["ffmpeg","-nostdin","-v","error","-y","-f","rawvideo",
                 "-pixel_format","bgr24","-video_size",f"{WIDTH}x{HEIGHT}",
                 "-framerate",str(FPS),"-i","pipe:0","-an","-c:v","libx264",
                 "-threads","2","-preset","veryfast","-crf","22","-pix_fmt","yuv420p",str(silent)]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            at_shot=0
            for i in range(frames):
                tm=i/FPS
                while at_shot<len(plan["shots"])-1 and tm>=plan["shots"][at_shot]["end"]:at_shot+=1
                shot=plan["shots"][at_shot];choice=cards["shots"][at_shot]
                source=assets[choice["assetId"]]
                fraction=max(0.,min(1.,(tm-shot["start"])/max(.00001,shot["end"]-shot["start"])))
                energy=value(lanes["raw-energy-envelope"],tm)
                pulse=max([max(0,1-abs(tm-t)/.52)**2 for t in pulses] or [0])
                if not choice.get("kineticSafe") or source["mode"]=="protect-text":pulse=0
                process.stdin.write(frame_for(source,fraction,energy,pulse).tobytes())
            process.stdin.close()
            if process.wait(timeout=75)!=0:raise RuntimeError(process.stderr.read().decode()[-400:])
            process.stderr.close()
            subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",str(silent),"-i",str(audio),
                            "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k",
                            "-shortest",str(output)],check=True)
        except Exception:
            process.kill();output.unlink(missing_ok=True);raise
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height","-of","json",str(output)]))
    observed=float(probe["format"]["duration"])
    if abs(observed-duration)>.10:output.unlink(missing_ok=True);raise ValueError("Duration mismatch")
    receipt={"schema":"vidmage/local-film-render-receipt/v1","status":"trial-only",
             "outputSha256":sha(output),"audioSha256":sha(audio),
             "requestedSeconds":duration,"observedSeconds":observed,"frames":frames,
             "blenderPlanId":plan["id"],"toasterLaneBankHash":observations["laneBank"]["laneBankHash"],
             "sources":{k:v["sha256"] for k,v in assets.items()},
             "kineticSelected":bool(kinetic),"kineticEvents":pulses,
             "humanKeep":False,"published":False,"providerCredits":0,"externalGenerations":0,
             "streams":probe["streams"]}
    output.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt

def main():
    p=argparse.ArgumentParser()
    for flag in ["plan","scene-cards","toaster-observation","audio","asset-root","output"]:
        p.add_argument("--"+flag,required=True)
    p.add_argument("--kinetic",action="store_true")
    a=p.parse_args()
    report=render(json.loads(Path(a.plan).read_text()),json.loads(Path(a.scene_cards).read_text()),
                  json.loads(Path(a.toaster_observation).read_text()),a.audio,a.asset_root,a.output,a.kinetic)
    print(json.dumps({"outputSha256":report["outputSha256"],"seconds":report["observedSeconds"],
                      "kinetic":report["kineticSelected"]}))
if __name__=="__main__":main()
