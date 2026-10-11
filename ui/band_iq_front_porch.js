"use strict";
(() => {
  const $=id=>document.getElementById(id);
  let state=null,working=false;
  let storyDraft=null,activeShot=0;
  let contactShot=-1,contactDraft=null,contactEvidence=null;
  let trayDrafts=[],grabbedBit=null,candidateEvidence=null,candidateNumber=0;
  const lensNames={
    landscape:"Wide & wandering",
    architecture:"Rooms & corridors",
    organism:"Breathing close",
    sigil:"Glyphs & sharp cuts",
    weather:"Wind & weather",
    "dimensional-space":"A fold in space",
  };
  function message(text){$("feedback").textContent=String(text);}
  function setBusy(active){
    working=active;
    for(const id of ["song","photos","accept","prepare","make","story-seal","make-filmstrip","contact-compare","contact-apply","candidate-save","candidate-apply","bit-cross","bit-grab"])$(id).disabled=active;
  }
  async function request(route,body,options={}){
    const headers={"X-Porch-Token":state.token};
    const isFile=!!options.file;
    if(isFile){
      headers["Content-Type"]="application/octet-stream";
      headers["X-Porch-Kind"]=options.kind;
      headers["X-Porch-Name"]=encodeURIComponent(options.name);
    }else{
      headers["Content-Type"]="application/json";
    }
    const response=await fetch(route,{
      method:"POST",cache:"no-store",
      headers,body:isFile?body:JSON.stringify(body),
    });
    const reply=await response.json();
    if(!response.ok||!reply.ok)throw new Error(reply.message||"Local action could not be completed.");
    state=reply.state;
    return reply;
  }
  function setStep(step) {
    const numbers=[1,2,3];
    numbers.forEach(n=>{
      $("step-"+n).className="step"+(n===step?" current":n<step?" done":"");
    });
  }
  function drawPhotos(images) {
    $("photo-line").replaceChildren();
    images.forEach((picture,i)=>{
      const card=document.createElement("div");
      card.className="thumb";
      const image=document.createElement("img");
      image.src=picture.url;
      image.alt="Owned source picture "+(i+1);
      image.loading="lazy";
      const caption=document.createElement("div");
      caption.className="caption";
      caption.textContent="IMAGE "+String(i+1).padStart(2,"0");
      card.append(image,caption);
      $("photo-line").append(card);
    });
  }
  function lensPicker(ids){
    $("lens-picker").replaceChildren();
    ids.forEach((id,i)=>{
      const label=document.createElement("label");
      label.className="lens";
      const radio=document.createElement("input");
      radio.type="radio";radio.name="lens";radio.value=id;
      radio.required=true;
      if(i===0)radio.checked=true;
      const title=document.createElement("span");
      title.textContent=lensNames[id]||id;
      label.append(radio,title);
      $("lens-picker").append(label);
    });
  }
  function storyShots(){
    return storyDraft||[];
  }
  function shotText(shot,i){
    return "SHOT "+String(i+1).padStart(2,"0")+" · "+
      shot.start.toFixed(1)+"–"+shot.end.toFixed(1)+" s";
  }
  function currentShotChoice(){
    const shot=storyDraft?.[activeShot];
    if(!shot)return null;
    const result={
      sourceAssetId:shot.sourceAssetId,
      focus:shot.focus.slice(),
      protectText:shot.protectText,
    };
    if(shot.crossBit)result.crossBit=JSON.parse(JSON.stringify(shot.crossBit));
    return result;
  }
  function sourceOptionList(){
    const table=state?.storytable;
    $("contact-image").replaceChildren();
    (table?.images||[]).forEach((source,i)=>{
      const option=document.createElement("option");
      option.value=source.assetId;
      option.textContent="Owned picture "+String(i+1).padStart(2,"0");
      $("contact-image").append(option);
    });
  }
  function invalidateContact(reason){
    contactEvidence=null;
    $("contact-result").hidden=true;
    $("contact-status").textContent=reason||
      "This is still just a possible shot. Nothing has been applied or sealed.";
  }
  function syncContactForShot(){
    const table=state?.storytable;
    $("contact-sheet").hidden=!table||table.sealed;
    if(!table||table.sealed){
      contactEvidence=null;
      return;
    }
    const left=currentShotChoice();
    if(!left)return;
    if(contactShot!==activeShot||!contactDraft){
      contactShot=activeShot;
      contactDraft={
        sourceAssetId:left.sourceAssetId,
        focus:left.focus.slice(),
        protectText:left.protectText,
        ...(left.crossBit?{crossBit:JSON.parse(JSON.stringify(left.crossBit))}:{}),
      };
      sourceOptionList();
      $("contact-image").value=contactDraft.sourceAssetId;
      $("contact-x").value=Math.round(contactDraft.focus[0]*100);
      $("contact-y").value=Math.round(contactDraft.focus[1]*100);
      $("contact-protect").checked=contactDraft.protectText;
      invalidateContact("Choose a new image or focus to compare with this song moment.");
    }else if(contactEvidence &&
      JSON.stringify(contactEvidence.left)!==JSON.stringify(left)){
      invalidateContact("The current draft changed. Compare again to see the new pixels.");
    }
    $("contact-current-label").textContent=
      "Shot "+(activeShot+1)+" · owned picture "+
      String((table.images.findIndex(x=>x.assetId===left.sourceAssetId)+1)).padStart(2,"0")+
      " · focus "+Math.round(left.focus[0]*100)+"% / "+
      Math.round(left.focus[1]*100)+"%"+
      (left.protectText?" · writing protected":"");
  }
  function contactControlsChanged(){
    if(!contactDraft||state?.storytable?.sealed)return;
    contactDraft={
      sourceAssetId:$("contact-image").value,
      focus:[Number($("contact-x").value)/100,
             Number($("contact-y").value)/100],
      protectText:$("contact-protect").checked,
      ...(contactDraft.crossBit?{crossBit:JSON.parse(JSON.stringify(contactDraft.crossBit))}:{}),
    };
    $("contact-x-value").textContent=Math.round(contactDraft.focus[0]*100)+"%";
    $("contact-y-value").textContent=Math.round(contactDraft.focus[1]*100)+"%";
    invalidateContact("Alternative changed. Compare again before applying.");
  }
  function drawContactFrames(receipt,side,target){
    $(target).replaceChildren();
    receipt[side].frames.forEach((sample,j)=>{
      const button=document.createElement("button");
      button.type="button";
      button.className="contact-frame";
      button.setAttribute("aria-label",
        "Listen at "+sample.atSeconds.toFixed(2)+" seconds, "+
        (side==="left"?"current shot":"alternative")+" frame "+(j+1));
      const picture=document.createElement("img");
      picture.src="/api/porch/contact/frame/"+receipt.comparisonSha256+
        "/"+side+"/"+j;
      picture.alt=(side==="left"?"Current":"Alternative")+
        " actual sourced VidMage frame at "+sample.atSeconds.toFixed(2)+" seconds";
      const stamp=document.createElement("small");
      stamp.textContent=sample.atSeconds.toFixed(2)+"s";
      button.append(picture,stamp);
      button.addEventListener("click",()=>{
        try{$("story-audio").currentTime=sample.atSeconds;}catch{}
      });
      $(target).append(button);
    });
  }

  function selectShot(index){
    const shots=storyShots(),table=state?.storytable;
    if(!table||!shots.length)return;
    activeShot=Math.max(0,Math.min(index,shots.length-1));
    const shot=shots[activeShot];
    $("story-shot-heading").textContent=shotText(shot,activeShot);
    $("story-focus-x").value=Math.round(shot.focus[0]*100);
    $("story-focus-y").value=Math.round(shot.focus[1]*100);
    $("story-x-value").textContent=Math.round(shot.focus[0]*100)+"%";
    $("story-y-value").textContent=Math.round(shot.focus[1]*100)+"%";
    $("story-protect").checked=shot.protectText;
    $("story-photos").replaceChildren();
    table.images.forEach((source,i)=>{
      const btn=document.createElement("button");
      btn.className="story-choice";
      btn.type="button";
      btn.setAttribute("aria-pressed",String(shot.sourceAssetId===source.assetId));
      btn.disabled=table.sealed;
      const img=document.createElement("img");
      img.src=source.url;
      img.alt="Owned image "+(i+1);
      const label=document.createElement("span");
      label.textContent="PICTURE "+String(i+1).padStart(2,"0");
      btn.append(img,label);
      btn.addEventListener("click",()=>{
        shot.sourceAssetId=source.assetId;
        selectShot(activeShot);
        touchDraft("Draft source changed; comparisons need fresh source pixels.");
      });
      $("story-photos").append(btn);
    });
    const found=table.images.find(a=>a.assetId===shot.sourceAssetId);
    if(found)$("story-preview").src=found.url;
    $("story-preview").className="story-focus-x-"+Math.round(shot.focus[0]*100)+
      " story-focus-y-"+Math.round(shot.focus[1]*100);
    $("story-timeline").querySelectorAll("button").forEach((btn,i)=>{
      btn.setAttribute("aria-pressed",String(i===activeShot));
    });
    $("story-previous").disabled=activeShot===0;
    $("story-next").disabled=activeShot===shots.length-1;
    syncContactForShot();
    refreshBitGuides();
  }
  function drawStorytable(){
    const table=state?.storytable;
    if(!table)return;
    if(!storyDraft||storyDraft.length!==table.shots.length||table.sealed){
      storyDraft=table.shots.map(x=>({
        shotId:x.shotId,start:x.start,end:x.end,
        sourceAssetId:x.sourceAssetId,
        focus:x.focus.slice(),protectText:x.protectText,
        ...(x.crossBit?{crossBit:JSON.parse(JSON.stringify(x.crossBit))}:{}),
      }));
    }
    $("story-audio").src="/api/porch/story/audio";
    $("story-timeline").replaceChildren();
    const total=table.shots[table.shots.length-1].end;
    storyDraft.forEach((shot,i)=>{
      const button=document.createElement("button");
      button.type="button";
      button.className="story-shot";
      button.classList.add("story-span-"+Math.max(1,Math.min(5,
        Math.round((shot.end-shot.start)/(total/storyDraft.length)))));
      button.setAttribute("aria-label",shotText(shot,i));
      button.setAttribute("aria-pressed",String(i===activeShot));
      const mark=document.createElement("span");mark.className="story-mark";
      mark.textContent=String(i+1).padStart(2,"0");
      const time=document.createElement("small");
      time.textContent=shot.start.toFixed(1)+"–"+shot.end.toFixed(1)+"s";
      button.append(mark,time);
      button.addEventListener("click",()=>{
        selectShot(i);
        try{$("story-audio").currentTime=shot.start;}catch{}
      });
      $("story-timeline").append(button);
    });
    selectShot(Math.min(activeShot,storyDraft.length-1));
    for(const id of ["story-focus-x","story-focus-y","story-protect","story-author",
                     "story-ack","story-seal"]){
      $(id).disabled=table.sealed;
    }
    $("story-sealing").hidden=table.sealed;
    $("story-sealed").hidden=!table.sealed;
    $("camera-step").hidden=!table.sealed;
    if(table.sealed){
      $("story-sha").textContent="Storytable receipt SHA-256 "+table.storySha256;
    }
    drawFilmstrip();
    drawTray();
  }

  function cloneShotList(items){
    return JSON.parse(JSON.stringify(items.map(row=>({
      shotId:row.shotId,sourceAssetId:row.sourceAssetId,
      focus:row.focus,protectText:row.protectText,
      ...(row.crossBit?{crossBit:row.crossBit}:{}),
    }))));
  }
  function clearCandidatePreview(reason){
    candidateEvidence=null;
    $("candidate-comparison").hidden=true;
    if(reason)$("candidate-status").textContent=reason;
  }
  function syncBitSourceOptions(){
    const chosen=$("bit-source").value;
    $("bit-source").replaceChildren();
    (state?.storytable?.images||[]).forEach((entry,i)=>{
      const option=document.createElement("option");
      option.value=entry.assetId;
      option.textContent="Owned picture "+String(i+1).padStart(2,"0");
      $("bit-source").append(option);
    });
    if(chosen&&state.storytable.images.some(x=>x.assetId===chosen)){
      $("bit-source").value=chosen;
    }
  }
  function bitRectangle(prefix){
    const size=Number($(prefix+"-size").value)/100;
    const x=Math.min(Number($(prefix+"-x").value)/100,1-size);
    const y=Math.min(Number($(prefix+"-y").value)/100,1-size);
    return [Number(x.toFixed(3)),Number(y.toFixed(3)),
            Number(size.toFixed(3)),Number(size.toFixed(3))];
  }
  function drawBitGuide(id,assetId,rect,legend){
    const canvas=$(id);
    if(!canvas||!state?.storytable)return;
    const imageRef=state.storytable.images.find(x=>x.assetId===assetId);
    if(!imageRef)return;
    const context=canvas.getContext("2d");
    const img=new Image();
    img.onload=()=>{
      if(state?.storytable?.sealed)return;
      context.clearRect(0,0,320,180);
      context.drawImage(img,0,0,320,180);
      context.fillStyle="rgba(8,21,14,.37)";
      context.fillRect(0,0,320,180);
      const [x,y,w,h]=rect;
      context.drawImage(img,x*320,y*180,w*320,h*180,
                        x*320,y*180,w*320,h*180);
      context.lineWidth=3;
      context.strokeStyle="#e9d391";
      context.strokeRect(x*320+1,y*180+1,w*320-2,h*180-2);
      context.font="bold 12px ui-monospace,monospace";
      context.fillStyle="#fff1c7";
      context.fillText(legend,10,18);
    };
    img.src=imageRef.url;
  }
  function refreshBitGuides(){
    if(!state?.storytable||state.storytable.sealed)return;
    for(const id of ["bit-grab-x","bit-grab-y","bit-grab-size",
                     "bit-cross-x","bit-cross-y","bit-cross-size","bit-opacity"]){
      $(id+"-out").textContent=$(id).value+"%";
    }
    drawBitGuide("bit-grab-guide",$("bit-source").value,
                 bitRectangle("bit-grab"),"GRAB / OWNED SOURCE");
    const current=storyDraft?.[activeShot];
    if(current)drawBitGuide("bit-cross-guide",current.sourceAssetId,
                  bitRectangle("bit-cross"),"CROSS / TARGET SHOT");
  }
  function drawTray(){
    const table=state?.storytable;
    $("candidate-tray").hidden=!table||table.sealed;
    if(!table||table.sealed){
      trayDrafts=[];grabbedBit=null;candidateEvidence=null;return;
    }
    syncBitSourceOptions();
    refreshBitGuides();
    $("candidate-collection").replaceChildren();
    if(!trayDrafts.length){
      const notice=document.createElement("p");
      notice.className="candidate-empty";
      notice.textContent="No alternate arrangements pinned yet. You can keep up to four independent drafts in this local tray.";
      $("candidate-collection").append(notice);
    }
    trayDrafts.forEach((item,i)=>{
      const card=document.createElement("article");
      card.className="candidate-pinned";
      const name=document.createElement("strong");
      name.textContent=item.title;
      const metadata=document.createElement("small");
      const diff=item.shots.filter((shot,j)=>
        JSON.stringify(shot)!==JSON.stringify(cloneShotList(storyDraft)[j])).length;
      metadata.textContent=diff+" shot(s) differ from current draft · "+
        item.shots.filter(s=>s.crossBit).length+" grabbed/crossed bit(s)";
      const actions=document.createElement("div");
      actions.className="candidate-buttons";
      const compare=document.createElement("button");
      compare.type="button";compare.className="story-navigate";
      compare.textContent="Compare this arrangement ↔";
      compare.disabled=diff===0||working;
      compare.addEventListener("click",()=>comparePinnedCandidate(item));
      const remove=document.createElement("button");
      remove.type="button";remove.className="candidate-remove";
      remove.textContent="Unpin";
      remove.addEventListener("click",()=>{
        trayDrafts.splice(i,1);
        clearCandidatePreview("The unsealed alternative was discarded. Your draft is unchanged.");
        drawTray();
      });
      actions.append(compare,remove);
      card.append(name,metadata,actions);
      $("candidate-collection").append(card);
    });
    $("candidate-save").disabled=trayDrafts.length>=4||working;
  }
  function touchDraft(reason){
    clearCandidatePreview(reason);
    if(!state?.storytable?.sealed)drawTray();
  }
  async function comparePinnedCandidate(entry){
    if(working||!state?.paper||state.storytable?.sealed)return;
    const old=cloneShotList(storyDraft);
    const alt=cloneShotList(entry.shots);
    const changed=alt.some((row,i)=>JSON.stringify(row)!==JSON.stringify(old[i]));
    if(!changed){
      $("candidate-status").textContent="This candidate is identical to the working draft.";
      return;
    }
    const payload={
      paperTraySha256:state.paper.paperTraySha256,
      baseShots:old,candidateShots:alt,
      compareOnly:true,allowStorySeal:false,allowMovieRender:false,
      allowPublication:false,allowNetworkUpload:false,allowPaidProviders:false,
    };
    setBusy(true);
    clearCandidatePreview("Rendering bounded actual pixels for the changed song windows…");
    try{
      const answer=await request("/api/porch/candidate/compare",payload);
      const receipt=answer.receipt;
      if(receipt.schema!=="vidmage/band-iq-013-temporary-candidate-tray/v1"||
         receipt.totalChangedShotCount<1||
         receipt.baseDraftSha256===receipt.candidateDraftSha256){
        throw Error("Actual candidate versions did not verify.");
      }
      candidateEvidence={
        receipt,old,alt,title:entry.title,
        oldJson:JSON.stringify(old),altJson:JSON.stringify(alt),
      };
      $("candidate-comparison-grid").replaceChildren();
      receipt.nativeComparisons.forEach((one,index)=>{
        const card=document.createElement("div");
        card.className="candidate-pair";
        const title=document.createElement("strong");
        title.textContent="SHOT "+String(one.shotIndex+1).padStart(2,"0")+
          " · "+one.shotId;
        const pair=document.createElement("div");
        pair.className="candidate-pair-frames";
        for(const side of ["left","right"]){
          const panel=document.createElement("div");
          const label=document.createElement("small");
          label.textContent=side==="left"?"CURRENT DRAFT":"PINNED ALTERNATIVE";
          panel.append(label);
          const photos=document.createElement("div");
          photos.className="candidate-three";
          one[side].frames.forEach((frame,frameIndex)=>{
            const button=document.createElement("button");
            button.type="button";
            const img=document.createElement("img");
            img.src="/api/porch/candidate/frame/"+receipt.candidateSha256+
              "/"+index+"/"+side+"/"+frameIndex;
            img.alt=side+" authored real frame at "+frame.atSeconds.toFixed(2)+"s";
            button.append(img);
            button.addEventListener("click",()=>{
              selectShot(one.shotIndex);
              try{$("story-audio").currentTime=frame.atSeconds;}catch{}
            });
            photos.append(button);
          });
          panel.append(photos);pair.append(panel);
        }
        card.append(title,pair);
        $("candidate-comparison-grid").append(card);
      });
      $("candidate-coverage").textContent=
        "Compared "+receipt.observedShotCount+" of "+
        receipt.totalChangedShotCount+" changed native song windows. "+
        (receipt.omittedChangesUnjudged?
          "Remaining changed windows have not been measured or judged.":"All changed windows sampled.")+
        " No native movie has been made.";
      $("candidate-comparison").hidden=false;
      $("candidate-status").textContent=
        "Both variants are still candidates. Apply the whole pinned arrangement only if you choose.";
    }catch(e){
      clearCandidatePreview(e.message||"Cannot compare these exact candidate sources.");
    }finally{setBusy(false);drawTray();}
  }

  function drawFilmstrip(){
    const table=state?.storytable;
    const sketch=state?.filmstrip;
    const visible=!!table?.sealed;
    $("living-filmstrip").hidden=!visible;
    if(!visible||!sketch)return;
    $("filmstrip-prompt").hidden=sketch.ready;
    $("filmstrip-results").hidden=!sketch.ready;
    if(!sketch.ready)return;
    const total=sketch.totalNativeShotCount;
    $("filmstrip-detail").textContent=
      "The native raster engine made "+sketch.sampledWindowCount+
      " small sets of three real frames. You can compare the beginning, middle and end of each sampled shot.";
    $("filmstrip-coverage").textContent=sketch.limitedSampling?
      "A bounded visual survey: "+sketch.sampledWindowCount+" of "+total+
      " song windows sampled evenly. Missing windows have NOT been rejected or judged.":
      "All "+total+" native song windows sampled, three source-real stills apiece. "+
      "The frames do not reproduce a moving camera or predict the independent Playdeck performance.";
    $("filmstrip-sha").textContent="Private sketch receipt SHA-256 "+sketch.filmstripSha256;
    $("filmstrip-reel").replaceChildren();
    sketch.frames.forEach((row,i)=>{
      const group=document.createElement("div");
      group.className="filmstrip-group";
      const header=document.createElement("div");
      header.className="filmstrip-mark";
      header.textContent="SHOT "+String(row.shotIndex+1).padStart(2,"0")+
        " · "+row.start.toFixed(1)+"–"+row.end.toFixed(1)+" s"+
        (row.protectText?" · TEXT PROTECTED":"");
      group.append(header);
      const triplet=document.createElement("div");
      triplet.className="filmstrip-triplet";
      row.samples.forEach((sample,j)=>{
        const button=document.createElement("button");
        button.type="button";button.className="filmstrip-frame";
        button.setAttribute("aria-label",
          "Hear the song at "+sample.atSeconds.toFixed(2)+
          " seconds and select Storytable shot "+(row.shotIndex+1));
        const image=document.createElement("img");
        image.loading="lazy";
        image.src=sample.url;image.alt=
          "Real VidMage still from shot "+(row.shotIndex+1)+
          " at "+sample.atSeconds.toFixed(2)+" seconds";
        const caption=document.createElement("small");
        caption.textContent=sample.atSeconds.toFixed(2)+"s";
        button.append(image,caption);
        button.addEventListener("click",()=>{
          selectShot(row.shotIndex);
          try{$("story-audio").currentTime=sample.atSeconds;}catch{}
        });
        triplet.append(button);
      });
      group.append(triplet);
      $("filmstrip-reel").append(group);
    });
  }

  function render() {
    const stage=state.stage;
    const haveConsent=!!state.consent;
    const prepared=!!state.paper;
    const made=!!state.films;
    $("bring").hidden=haveConsent;
    $("paper").hidden=!haveConsent||made;
    $("films").hidden=!made;
    setStep(made?3:haveConsent?2:1);
    if(stage==="bring"){
      $("song-name").textContent=state.song?
        "Song received · "+state.song.durationSeconds.toFixed(1)+" sec":
        "Nothing brought yet";
      $("photo-count").textContent=state.images.length+
        " of "+state.limits.minImages+" minimum images received";
    }
    drawPhotos(state.images);
    if(haveConsent) {
      $("source-recap").textContent=state.consent.title+
        " · "+state.images.length+" owned images · "+
        (state.song?state.song.durationSeconds.toFixed(1)+" seconds of actual audio":"no song");
      $("prepare").hidden=prepared;
    }
    if(prepared){
      $("paper-preview").hidden=false;
      $("plan-status").textContent=state.paper.durationSeconds.toFixed(1)+
        " seconds planned · "+state.paper.sourceCount+
        " owned images · all selected films remain trials until a human KEEP.";
      lensPicker(state.paper.lensIds);
      drawStorytable();
    }
    if(made){
      $("receipt-status").textContent="Original VidMage "+state.films.originalVidmageSha256+
        " · Native Playdeck "+state.films.nativePlaydeckSha256;
      message("Two real films exist. Your source is preserved; their future is yours.");
    }else{
      const digest=state.paper?.paperTraySha256||state.consent?.sha256||state.song?.sha256;
      $("receipt-status").textContent=digest?
        "Private source proof: "+digest:"No local authorization or film receipts yet.";
    }
  }
  async function refresh(){
    const r=await fetch("/api/porch/state",{cache:"no-store"});
    const payload=await r.json();
    if(!r.ok||payload.schema!=="vidmage/band-iq-009-front-porch-ui/v1")
      throw Error(payload.message||"Private source evidence cannot be verified.");
    state=payload;
    render();
  }
  async function uploadFile(file,kind){
    if(!file)return;
    const limit=kind==="audio"?36*1024*1024:12*1024*1024;
    if(file.size>limit)throw Error("This file exceeds the "+(kind==="audio"?"36":"12")+" MB local limit.");
    if(file.size===0)throw Error("Empty files cannot become source material.");
    message("Bringing your "+(kind==="audio"?"song":"picture")+" into the private workroom…");
    await request("/api/porch/upload",file,{file:true,kind,name:file.name});
    render();
  }
  $("song").addEventListener("change",async()=>{
    if(working||!$("song").files?.length)return;
    setBusy(true);
    try{
      await uploadFile($("song").files[0],"audio");
      message("Song received. Your original bytes remain unchanged.");
    }catch(error){message(error.message||"Song could not be read.");}
    finally{setBusy(false);}
  });
  $("photos").addEventListener("change",async()=>{
    if(working)return;
    const list=Array.from($("photos").files||[]);
    setBusy(true);
    try{
      for(const picture of list)await uploadFile(picture,"image");
      message("Pictures received. They're still private and unselected.");
    }catch(error){message(error.message||"One image could not be read.");}
    finally{setBusy(false);}
  });
  $("consent-form").addEventListener("submit",async(event)=>{
    event.preventDefault();
    if(working||!state)return;
    if(!state.song||state.images.length<2){
      message("Bring one song and at least two actual owned images first.");
      return;
    }
    const body={
      title:$("title").value.trim(),
      operatorAttestationId:$("maker").value.trim(),
      ownedOrLicensed:$("rights").checked,
      allowLocalDerivatives:$("derivatives").checked,
      noPublicRelease:$("no-release").checked,
      allowNetworkUpload:false,
      allowPaidProviders:false,
    };
    if(!body.title||!body.operatorAttestationId||!body.ownedOrLicensed||
       !body.allowLocalDerivatives||!body.noPublicRelease){
      message("All three explicit source permissions and a named creator are required.");
      return;
    }
    const yes=window.confirm(
      "Seal this private source intake? Original media will be preserved. "+
      "Preparation is permitted, but no film is yet authorized, and nothing is published.");
    if(!yes)return;
    setBusy(true);message("Sealing exactly these owned sources and your permission…");
    try{await request("/api/porch/consent",body);render();
      message("Source permission recorded. Now you can prepare the paper film plan.");
    }catch(error){message(error.message||"Source permission was refused.");}
    finally{setBusy(false);}
  });
  $("prepare").addEventListener("click",async()=>{
    if(working)return;
    const yes=window.confirm(
      "Prepare your song and pictures locally using pinned Toaster and Blender? "+
      "This makes a paper plan and local copies, but NO video is rendered.");
    if(!yes)return;
    setBusy(true);message("Listening to actual audio and laying out owned pictures…");
    try{await request("/api/porch/prepare",{prepareLocalPaper:true});
      render();message("The paper tray is ready. Nothing has been rendered.");
    }catch(error){message(error.message||"Local preparation could not be verified.");}
    finally{setBusy(false);}
  });
  function changeFocus(){
    if(!storyDraft||state?.storytable?.sealed)return;
    const shot=storyDraft[activeShot];
    shot.focus=[
      Number($("story-focus-x").value)/100,
      Number($("story-focus-y").value)/100,
    ];
    $("story-protect").checked=shot.protectText;
    selectShot(activeShot);
    touchDraft("Draft focus changed. Old candidate pixels are stale.");
  }
  function guidePointer(event,canvasId,prefix){
    if(state?.storytable?.sealed||working)return;
    const box=$(canvasId).getBoundingClientRect();
    const size=Number($(prefix+"-size").value);
    const cx=(event.clientX-box.left)/box.width*100;
    const cy=(event.clientY-box.top)/box.height*100;
    if(!Number.isFinite(cx)||!Number.isFinite(cy))return;
    $(""+prefix+"-x").value=String(
      Math.min(100-size,Math.max(0,Math.round((cx-size/2)/5)*5)));
    $(""+prefix+"-y").value=String(
      Math.min(100-size,Math.max(0,Math.round((cy-size/2)/5)*5)));
    refreshBitGuides();
  }
  for(const prefix of ["bit-grab","bit-cross"]){
    for(const dimension of ["x","y","size"]){
      $(prefix+"-"+dimension).addEventListener("input",refreshBitGuides);
    }
  }
  $("bit-opacity").addEventListener("input",refreshBitGuides);
  $("bit-source").addEventListener("change",refreshBitGuides);
  $("bit-grab-guide").addEventListener("click",e=>
    guidePointer(e,"bit-grab-guide","bit-grab"));
  $("bit-cross-guide").addEventListener("click",e=>
    guidePointer(e,"bit-cross-guide","bit-cross"));
  $("bit-grab").addEventListener("click",()=>{
    if(!state?.storytable||state.storytable.sealed)return;
    grabbedBit={
      sourceAssetId:$("bit-source").value,
      crop:bitRectangle("bit-grab"),
    };
    $("bit-status").textContent=
      "Piece grabbed. It remains an in-memory idea; no image has been changed.";
  });
  $("bit-cross").addEventListener("click",()=>{
    if(!grabbedBit||!storyDraft||state?.storytable?.sealed){
      $("bit-status").textContent="Grab a piece from an owned photograph first.";
      return;
    }
    const bit={
      sourceAssetId:grabbedBit.sourceAssetId,
      crop:grabbedBit.crop.slice(),
      place:bitRectangle("bit-cross"),
      opacity:Number($("bit-opacity").value)/100,
    };
    if(!window.confirm(
      "Cross this piece of owned imagery into the selected UNSEALED draft shot? "+
      "Neither original changes. An actual crossed working image is created only "+
      "after a separate human Storytable seal."))return;
    storyDraft[activeShot].crossBit=bit;
    selectShot(activeShot);
    touchDraft("Crossed an owned fragment into the unsealed shot. "+
      "Use THIS/THAT to inspect the actual resulting pixels.");
    $("bit-status").textContent="Crossed into song shot "+(activeShot+1)+
      ". Source and position will be preserved if the artist seals the Storytable.";
  });
  $("bit-uncross").addEventListener("click",()=>{
    if(!storyDraft||state?.storytable?.sealed)return;
    if(!storyDraft[activeShot].crossBit){
      $("bit-status").textContent="No source fragment is crossed into this shot.";
      return;
    }
    delete storyDraft[activeShot].crossBit;
    selectShot(activeShot);
    touchDraft("The crossed fragment was lifted from the unsealed draft.");
    $("bit-status").textContent="Cross removed; owned source files stay unchanged.";
  });
  $("candidate-save").addEventListener("click",()=>{
    if(!storyDraft||state?.storytable?.sealed||trayDrafts.length>=4)return;
    const snap=cloneShotList(storyDraft);
    if(trayDrafts.some(t=>JSON.stringify(t.shots)===JSON.stringify(snap))){
      $("candidate-status").textContent="This precise arrangement is already pinned.";
      return;
    }
    candidateNumber++;
    trayDrafts.push({
      title:"POSSIBILITY "+String(candidateNumber).padStart(2,"0"),
      shots:snap,
    });
    $("candidate-status").textContent=
      "Pinned the complete unsealed draft in session memory. No story or film created.";
    drawTray();
  });
  $("candidate-apply").addEventListener("click",()=>{
    const candidate=candidateEvidence;
    if(!candidate||state?.storytable?.sealed||!storyDraft||
       JSON.stringify(cloneShotList(storyDraft))!==candidate.oldJson){
      clearCandidatePreview("The draft changed; compare again before applying.");
      return;
    }
    if(!window.confirm(
      "Apply the WHOLE selected alternative to the UNSEALED draft? "+
      "No source image, signed story or published film will be altered. "+
      "The Storytable must still be sealed separately."))return;
    storyDraft=storyDraft.map((row,i)=>({
      ...row,...JSON.parse(JSON.stringify(candidate.alt[i])),
    }));
    clearCandidatePreview("This candidate entered the draft. Nothing was sealed.");
    contactShot=-1;
    contactDraft=null;
    selectShot(activeShot);
    drawTray();
  });
  $("candidate-cancel").addEventListener("click",()=>{
    clearCandidatePreview("No candidate applied; your draft is unchanged.");
  });
  $("contact-image").addEventListener("change",contactControlsChanged);
  $("contact-x").addEventListener("input",contactControlsChanged);
  $("contact-y").addEventListener("input",contactControlsChanged);
  $("contact-protect").addEventListener("change",contactControlsChanged);
  $("contact-compare").addEventListener("click",async()=>{
    if(working||!storyDraft||state.storytable?.sealed||!contactDraft)return;
    const selected=storyDraft[activeShot];
    const left=currentShotChoice();
    const right={...contactDraft,focus:contactDraft.focus.slice()};
    const body={
      paperTraySha256:state.paper.paperTraySha256,
      shotId:selected.shotId,left,right,
      compareOnly:true,allowStorySeal:false,allowMovieRender:false,
      allowNetworkUpload:false,allowPaidProviders:false,allowPublication:false,
    };
    setBusy(true);
    $("contact-status").textContent=
      "Sampling the same exact song window with your two source and framing choices…";
    try{
      const result=await request("/api/porch/contact/compare",body);
      const compared=result.receipt;
      if(compared.schema!=="vidmage/band-iq-012-ephemeral-contact-sheet/v1"||
         compared.shotId!==selected.shotId||
         JSON.stringify(left)!==JSON.stringify({
           sourceAssetId:compared.left.sourceAssetId,
           focus:compared.left.focus,
           protectText:compared.left.protectText,
           ...(compared.left.crossBit?{crossBit:compared.left.crossBit}:{}),
         })){
        throw Error("Comparison did not belong to the exact original draft.");
      }
      contactEvidence={receipt:compared,left,right,shotId:selected.shotId};
      drawContactFrames(compared,"left","contact-left-frames");
      drawContactFrames(compared,"right","contact-right-frames");
      $("contact-digest").textContent=
        "Temporary local comparison SHA-256 "+compared.comparisonSha256+
        " · no files or story receipts written";
      $("contact-result").hidden=false;
      $("contact-status").textContent=
        "Two real samples, neither selected. Apply THAT, or leave this draft untouched.";
    }catch(error){invalidateContact(error.message||"Comparison could not be generated.");}
    finally{setBusy(false);}
  });
  $("contact-apply").addEventListener("click",()=>{
    const idea=contactEvidence;
    if(!idea||state?.storytable?.sealed||!storyDraft||
       storyDraft[activeShot].shotId!==idea.shotId||
       JSON.stringify(currentShotChoice())!==JSON.stringify(idea.left)||
       JSON.stringify(contactDraft)!==JSON.stringify(idea.right)){
      invalidateContact("This comparison is no longer current. Compare again.");
      return;
    }
    if(!window.confirm(
      "Apply the alternative image/framing to this UNSEALED draft only? "+
      "The saved original, source plan, and any sealed film remain untouched. "+
      "You will still need to explicitly seal the complete Storytable later."))return;
    storyDraft[activeShot]={
      ...storyDraft[activeShot],
      sourceAssetId:idea.right.sourceAssetId,
      focus:idea.right.focus.slice(),
      protectText:idea.right.protectText,
      ...(idea.right.crossBit?{crossBit:JSON.parse(JSON.stringify(idea.right.crossBit))}:{}),
    };
    invalidateContact("Alternative applied to this on-screen draft only. Storytable still unsealed.");
    selectShot(activeShot);
    touchDraft("Alternative entered your draft; no Storytable has been sealed.");
  });
  $("contact-leave").addEventListener("click",()=>{
    invalidateContact("Your original on-screen draft is unchanged. No comparison was applied.");
  });
  $("story-focus-x").addEventListener("input",changeFocus);
  $("story-focus-y").addEventListener("input",changeFocus);
  $("story-protect").addEventListener("change",()=>{
    if(!storyDraft||state?.storytable?.sealed)return;
    storyDraft[activeShot].protectText=$("story-protect").checked;
    touchDraft("Draft text treatment changed. Existing comparisons are stale.");
  });
  $("story-previous").addEventListener("click",()=>selectShot(activeShot-1));
  $("story-next").addEventListener("click",()=>selectShot(activeShot+1));
  $("story-audio").addEventListener("timeupdate",()=>{
    const t=$("story-audio").currentTime;
    if(!storyDraft||!Number.isFinite(t))return;
    const next=storyDraft.findIndex((s,i)=>
      t>=s.start&& (t<s.end||i===storyDraft.length-1&&t<=s.end));
    if(next>=0&&next!==activeShot)selectShot(next);
  });
  $("story-seal").addEventListener("click",async()=>{
    if(working||!storyDraft||state.storytable?.sealed)return;
    const artist=$("story-author").value.trim();
    if(!artist||!$("story-ack").checked){
      message("Name the creator and approve this precise local shot arrangement first.");
      return;
    }
    const form={
      paperTraySha256:state.paper.paperTraySha256,
      operatorAttestationId:artist,
      decision:"SEAL_STORYTABLE",
      shots:storyDraft.map(x=>({
        shotId:x.shotId,sourceAssetId:x.sourceAssetId,
        focus:x.focus.slice(),protectText:x.protectText,
        ...(x.crossBit?{crossBit:JSON.parse(JSON.stringify(x.crossBit))}:{}),
      })),
      preserveOriginals:true,publish:false,
      allowPaidProviders:false,allowNetworkUpload:false,
    };
    if(!window.confirm(
      "Seal your authored storytable? Each actual song window, chosen owned picture, "+
      "focus and protected-writing setting will be preserved. "+
      "No film is rendered by this action."))return;
    setBusy(true);
    message("Preserving the exact timed human arrangement and source image hashes…");
    try{
      await request("/api/porch/story/seal",form);
      render();
      message("Your Storytable is sealed. Now you can choose a camera language.");
    }catch(error){message(error.message||"The source arrangement was not accepted.");}
    finally{setBusy(false);}
  });

  $("make-filmstrip").addEventListener("click",async()=>{
    if(working||!state?.storytable?.sealed||state.films)return;
    const yes=window.confirm(
      "Develop a private filmstrip of sampled actual VidMage raster frames from "+
      "your SEALED Storytable? This is not a rendered moving film and does not "+
      "authorize external uploads, provider cost, KEEP or publication.");
    if(!yes)return;
    setBusy(true);
    message("Developing a few actual source-bound frames from the author-sealed table…");
    try{
      const form={
        storySha256:state.storytable.storySha256,
        makeLocalSketch:true,
        acknowledgeSketchNotFilm:true,
        allowNetworkUpload:false,allowPaidProviders:false,allowPublication:false,
      };
      await request("/api/porch/filmstrip/make",form);
      render();
      message("Your sourced sketch is developed; each still has its own time and SHA.");
    }catch(error){message(error.message||"The local sketch could not be verified.");}
    finally{setBusy(false);}
  });

  $("make").addEventListener("click",async()=>{
    if(working||!state?.paper)return;
    if(!state.storytable?.sealed){
      message("Choose and seal the actual timed scene cards before making any film.");
      return;
    }
    const selected=document.querySelector('input[name="lens"]:checked');
    const attestation=$("director").value.trim();
    if(!selected||!attestation||!$("render-ok").checked){
      message("Choose a camera, enter a fresh artist signature and explicitly approve both local trials.");
      return;
    }
    const choice={
      paperTraySha256:state.paper.paperTraySha256,
      storySha256:state.storytable.storySha256,
      lensId:selected.value,
      operatorAttestationId:attestation,
      makeOneLocalABPair:true,
      allowPaidProviders:false,
      allowNetworkUpload:false,
      allowPublicRelease:false,
      acknowledgeUnselectedTrials:true,
    };
    const yes=window.confirm(
      "Render a new local A/B pair using "+(lensNames[selected.value]||selected.value)+
      "? Your song and original images will remain unchanged. "+
      "This creates actual films but does not KEEP, export, spend credits or publish.");
    if(!yes)return;
    setBusy(true);
    message("Making two actual local films: VidMage A and native Playdeck B. "+
      "The page may stay unchanged while the local render runs. "+
      "Do not submit again.");
    try{
      await request("/api/porch/make",choice);
      render();
      message("Both real films were verified. The living workbench is now yours.");
    }catch(error){
      message(error.message||"Rendering was refused; the original song and images remain untouched.");
    }finally{setBusy(false);}
  });
  refresh().catch(error=>{message(error.message||"Source state could not be loaded.");
    for(const id of ["song","photos","accept","prepare","make"])$(id).disabled=true;});
})();
