"use strict";
(() => {
  const $=id=>document.getElementById(id);
  let state=null,working=false;
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
    for(const id of ["song","photos","accept","prepare","make"])$(id).disabled=active;
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
  $("make").addEventListener("click",async()=>{
    if(working||!state?.paper)return;
    const selected=document.querySelector('input[name="lens"]:checked');
    const attestation=$("director").value.trim();
    if(!selected||!attestation||!$("render-ok").checked){
      message("Choose a camera, enter a fresh artist signature and explicitly approve both local trials.");
      return;
    }
    const choice={
      paperTraySha256:state.paper.paperTraySha256,
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
