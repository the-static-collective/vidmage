"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const a=$("a"),c=$("c");
  let context=null, sealed=false;
  const message=(id,v)=>{$(id).textContent=String(v);};
  const names={
    CONTINUE_ORIGINAL:"A · ORIGINAL selected for further local work",
    CONTINUE_REVISION:"C · REVISION selected for further local work",
    DECLINE_BOTH:"NEITHER film selected · both histories preserved",
    ASK_ANOTHER_QUESTION:"NEW QUESTION recorded · no editing started",
  };
  function chooseAudio(side){a.muted=side!=="a";c.muted=side!=="c";}
  function finish(choice) {
    sealed=true;
    $("ac-form").hidden=true;
    $("sealed").hidden=false;
    message("sealed-choice",names[choice.decision]||"Decision sealed");
    message("sealed-sha","Independent A/C review receipt SHA-256 "+choice.reviewSha256);
    message("status","Human A/C decision recorded · read-only");
  }
  function showMeasured(context) {
    const m=context.measurements;
    message("whole-difference",
      (m.sampling.pixelMAEAcrossSong*100).toFixed(2)+
      "% average absolute grayscale pixel difference across actual sampled source films; NOT a quality ranking.");
    $("timeline").replaceChildren();
    for(const row of m.windows){
      const el=document.createElement("div");el.className="ac-window";
      const label=document.createElement("div");label.className="ac-window-label";
      label.textContent=row.start.toFixed(1)+"–"+row.end.toFixed(1)+" s · "+
        (row.operatorEditOverlapsThisWindow?"Selected author edit overlaps":"Outside selected edit");
      const progress=document.createElement("progress");progress.className="ac-meter";
      progress.max=1;progress.value=row.pixelMeanAbsoluteDifference;
      progress.setAttribute("aria-label","Actual sampled pixel difference, "+row.id);
      const caption=document.createElement("small");
      caption.textContent=(row.pixelMeanAbsoluteDifference*100).toFixed(2)+
        "% mean pixel difference · "+(row.changedFrameFractionAt2PctMAE*100).toFixed(0)+
        "% frames over 2% · non-stillness Δ "+
        row.nonStillnessDelta.toFixed(3);
      el.append(label,progress,caption);
      $("timeline").appendChild(el);
    }
    message("observation-sha",context.observationSha256);
    message("revision-sha",context.revisionSha256);
    message("pair-sha",context.pairSha256);
  }
  async function load(){
    const response=await fetch("/api/context",{cache:"no-store"});
    if(!response.ok)throw new Error("The local A/C source films could not be verified.");
    const data=await response.json();
    if(data.schema!=="vidmage/band-iq-007-local-review-ui/v1")
      throw new Error("Unknown A/C evidence contract.");
    context=data;
    a.src=data.renderers.a.url;
    c.src=data.renderers.c.url;
    chooseAudio("a");
    message("status",data.status==="recorded"?"Recorded":"Awaiting independent human A/C choice");
    message("operation","EDIT · "+data.operation);
    message("question",data.question);
    message("original-review-sha",data.originalReviewSha256);
    message("sha-a",data.renderers.a.sha256.slice(0,24)+"…");
    message("sha-c",data.renderers.c.sha256.slice(0,24)+"…");
    showMeasured(data);
    if(data.decision)finish(data.decision);
  }
  function updateQuestion(){
    const choice=document.querySelector('input[name="decision"]:checked');
    const active=!!choice&&choice.value==="ASK_ANOTHER_QUESTION";
    $("new-question").hidden=!active;
    $("new-question-label").hidden=!active;
    $("new-question").required=active;
    if(!active)$("new-question").value="";
  }
  async function submit(event){
    event.preventDefault();
    if(sealed||!context)return;
    const picked=document.querySelector('input[name="decision"]:checked');
    if(!picked) {message("feedback","Select a choice.");return;}
    const data={
      decision:picked.value,
      operatorAttestationId:$("creator").value.trim(),
      rationale:$("why").value,
      nextQuestion:$("new-question").value,
      acknowledgedLocalOnly:$("acknowledge").checked,
    };
    if(!data.operatorAttestationId||!data.acknowledgedLocalOnly||
       (data.decision==="ASK_ANOTHER_QUESTION"&&!data.nextQuestion.trim())){
      message("feedback","New reviewer attestation and explicit acknowledgement are required.");return;
    }
    const okay=window.confirm(
      "Seal one new, separate A/C human decision?\n\n"+
      names[data.decision]+
      "\n\nThis action will not publish, export, erase, edit or launch another film.");
    if(!okay)return;
    $("submit").disabled=true;
    message("feedback","Verifying the original film, revision, question and measurement receipts…");
    try{
      const response=await fetch("/api/decision",{
        method:"POST",cache:"no-store",
        headers:{"Content-Type":"application/json","X-Review-Token":context.reviewToken},
        body:JSON.stringify(data),
      });
      const result=await response.json();
      if(!response.ok||!result.ok||!result.receipt)
        throw new Error(result.message||"A/C review was not accepted.");
      finish(result.receipt);
      message("feedback","Your independent decision is saved. Both original films remain unchanged.");
    }catch(error){
      message("feedback",error.message||"A/C review refused.");
      try{
        const response=await fetch("/api/context",{cache:"no-store"});
        if(response.ok){const newer=await response.json();if(newer.decision)finish(newer.decision);}
      }catch{}
      $("submit").disabled=sealed;
    }
  }
  $("play").addEventListener("click",async()=>{
    if(a.readyState>=1&&c.readyState>=1)c.currentTime=a.currentTime;
    const results=await Promise.allSettled([a.play(),c.play()]);
    if(results.some(x=>x.status==="rejected"))
      message("feedback","Browser playback was interrupted; use the individual film controls.");
  });
  $("pause").addEventListener("click",()=>{a.pause();c.pause();});
  $("sync").addEventListener("click",()=>{if(Number.isFinite(a.currentTime))c.currentTime=a.currentTime;});
  document.querySelectorAll('input[name="sound"]').forEach(radio=>{
    radio.addEventListener("change",()=>{if(radio.checked)chooseAudio(radio.value);});
  });
  document.querySelectorAll('input[name="decision"]').forEach(radio=>{
    radio.addEventListener("change",updateQuestion);
  });
  $("ac-form").addEventListener("submit",submit);
  load().catch(error=>{
    message("status","HOLD · Local source evidence unavailable");
    message("feedback",error.message||"Missing original or revised source evidence");
    $("submit").disabled=true;
  });
})();
