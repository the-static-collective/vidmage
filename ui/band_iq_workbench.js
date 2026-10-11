"use strict";
(() => {
  const $=id=>document.getElementById(id);
  let context=null;
  let busy=false;
  const stateNames={
    verified:"verified source",ready:"ready to enter",recorded:"human decision recorded",
    "awaiting-human":"your turn",observed:"actually measured",
    available:"choose a comparison", "not-configured":"not yet connected",
    "not-yet":"not yet", 
  };
  function text(id,value){$(id).textContent=String(value);}
  function jump(label,href){
    const a=document.createElement("a");
    a.className="smallaction";a.href=href;
    a.textContent=label+" ↗";
    return a;
  }
  function linkForDoor(door) {
    const statuses=context.steps;
    const recorded=!!context.firstReviewDecision;
    const available=context.candidates.some(c=>c.observationSha256);
    if(door.id==="bring")return ["See source custody","#receipt-heading"];
    if(door.id==="listen")return [door.status==="ready"?"Enter film room":"See verified films","/room"];
    if(door.id==="make")return ["Watch existing films","/room"];
    if(door.id==="wonder")return [recorded?"Revisit first review":"Make your first choice","/room"];
    if(door.id==="revise")return ["Explore a question","/room"];
    if(door.id==="notice")
      return available?["See observed trials","#experiments"]:["Find an experiment","/room"];
    if(door.id==="choose")
      return available?["Choose an A/C pair","#experiments"]:["Begin from A/B","/room"];
    return null;
  }
  function showDoors(steps){
    $("doors").replaceChildren();
    steps.forEach((door,index)=>{
      const article=document.createElement("article");
      article.className="door";
      article.dataset.state=door.status;
      const number=document.createElement("div");
      number.className="index";
      number.textContent=String(index+1).padStart(2,"0")+" / 07";
      const middle=document.createElement("div");
      const title=document.createElement("h3");title.textContent=door.name;
      const verb=document.createElement("p");verb.className="verb";verb.textContent=door.verb;
      middle.append(title,verb);
      const bottom=document.createElement("div");
      const state=document.createElement("div");
      state.className="state";state.textContent=stateNames[door.status]||door.status;
      bottom.appendChild(state);
      const link=linkForDoor(door);
      if(link)bottom.appendChild(jump(link[0],link[1]));
      article.append(number,middle,bottom);
      $("doors").appendChild(article);
    });
  }
  function renderExperiments(candidates) {
    $("experiments").replaceChildren();
    if(!candidates.length){
      const p=document.createElement("p");
      p.className="empty";
      p.textContent=context.firstReviewDecision==="ANOTHER_EXPERIMENT"
        ?"The question is here. A human-approved local trial has not yet been found in this project drawer."
        :"No revised films in this project's drawer yet. Begin with the two existing films.";
      $("experiments").appendChild(p);
      return;
    }
    for(const [index,item] of candidates.entries()){
      const card=document.createElement("article");
      card.className="experiment";
      const marker=document.createElement("div");
      marker.className="index";
      marker.textContent="FILM "+String(index+1).padStart(2,"0")+" · "+
        (item.observationSha256?"OBSERVED":"TRIAL ONLY");
      const heading=document.createElement("h3");
      const display={
        SWAP_CARD:"One image, another possibility",
        REFOCUS_CARD:"A shift in attention",
        CHANGE_LENS:"A different camera language",
      };
      heading.textContent=display[item.experiment]||"An authored local experiment";
      const q=document.createElement("p");
      q.textContent=item.question?"Question: “"+item.question+"”":
        "The creator's original question was not available in this receipt.";
      const details=document.createElement("p");
      details.className="hash";
      details.textContent="Trial "+item.revisionSha256.slice(0,16)+"…";
      const action=document.createElement("button");
      action.type="button";
      if(item.observationSha256){
        action.textContent="Open original ↔ revision";
        action.addEventListener("click",()=>selectPair(item,card));
      }else{
        action.textContent="Open original review";
        action.addEventListener("click",()=>{window.location.assign("/room");});
      }
      card.append(marker,heading,q,details,action);
      $("experiments").appendChild(card);
    }
  }
  function present(data){
    if(data.schema!=="vidmage/band-iq-008-workbench-status/v1")
      throw new Error("Unexpected workbench source contract.");
    context=data;
    showDoors(data.steps);
    renderExperiments(data.candidates);
    text("project-sha",data.projectSha256);
    text("a-sha",data.originalFilmSha256);
    text("b-sha",data.alternateFilmSha256);
    text("first-review-sha",data.firstReviewSha256||"No human decision yet");
    text("ignored-receipts",data.ignoredInvalidReceipts);
    text("question",data.questionVerbatim||
      "No next question has been written here yet. It is allowed to enjoy a film before changing it.");
    text("status",data.activePair?
      "A/C comparison openable · "+(data.activePair.reviewed?"human choice recorded":"awaiting your choice"):
      "Source films verified · "+data.candidates.length+" recorded trial / observation pairing(s)");
    if(data.activePair) {
      const button=document.createElement("a");
      button.href="/ac/";
      button.className="primary action";
      button.textContent="Return to selected A/C review ↗";
      $("bench-message").replaceChildren(button);
    } else {
      $("bench-message").textContent=
        "Nothing here creates a new film on its own. Select a measured trial to open a separate human A/C room.";
    }
  }
  async function refresh(){
    if(busy)return;
    busy=true;
    $("refresh").disabled=true;
    text("status","Checking which local source artifacts really exist…");
    try{
      const response=await fetch("/api/workbench/status",{cache:"no-store"});
      if(!response.ok)throw new Error("The local project map could not be verified.");
      present(await response.json());
    }catch(error){
      text("status","HOLD · "+(error.message||"Local project evidence unavailable"));
      $("bench-message").textContent="Review original files and receipts locally; no source film has been changed.";
    }finally{
      busy=false;$("refresh").disabled=false;
    }
  }
  async function selectPair(item,card){
    if(busy||!context||!item.observationSha256)return;
    busy=true;card.setAttribute("aria-busy","true");
    text("bench-message","Rechecking the exact revision, original film and native observations…");
    try{
      const response=await fetch("/api/workbench/select",{
        method:"POST",cache:"no-store",
        headers:{"Content-Type":"application/json",
                 "X-Workbench-Token":context.token},
        body:JSON.stringify({
          revisionSha256:item.revisionSha256,
          observationSha256:item.observationSha256,
        }),
      });
      const result=await response.json();
      if(!response.ok||!result.ok||!result.ac)
        throw new Error(result.message||"The pair did not pass actual source verification.");
      window.location.assign("/ac/");
    }catch(error){
      text("bench-message",error.message||
        "The selected source pair is unavailable. Originals remain unchanged.");
    }finally{busy=false;card.removeAttribute("aria-busy");}
  }
  $("refresh").addEventListener("click",refresh);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden)refresh();});
  refresh();
})();
