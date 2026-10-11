"use strict";
(() => {
  const $=id=>document.getElementById(id);
  let state=null,working=false;
  let storyDraft=null,activeShot=0;
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
    for(const id of ["song","photos","accept","prepare","make","story-seal","make-filmstrip"])$(id).disabled=active;
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
  }
  function drawStorytable(){
    const table=state?.storytable;
    if(!table)return;
    if(!storyDraft||storyDraft.length!==table.shots.length||table.sealed){
      storyDraft=table.shots.map(x=>({
        shotId:x.shotId,start:x.start,end:x.end,
        sourceAssetId:x.sourceAssetId,
        focus:x.focus.slice(),protectText:x.protectText,
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
  }
  $("story-focus-x").addEventListener("input",changeFocus);
  $("story-focus-y").addEventListener("input",changeFocus);
  $("story-protect").addEventListener("change",()=>{
    if(!storyDraft||state?.storytable?.sealed)return;
    storyDraft[activeShot].protectText=$("story-protect").checked;
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
