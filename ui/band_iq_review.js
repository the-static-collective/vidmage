"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const a = $("a"), b = $("b");
  let context = null;
  let committed = false;
  let nextSet = null;
  let nextRendered = false;

  const text = (id, value) => { $(id).textContent = String(value); };
  const outcomeNames = {
    KEEP_VIDMAGE: "KEEP A · VidMage chosen for local continuation",
    KEEP_PLAYDECK: "KEEP B · Playdeck chosen for local continuation",
    SCRAPE_BOTH: "SCRAPE BOTH · Neither film selected; both preserved",
    ANOTHER_EXPERIMENT: "NEW QUESTION · No new film has been executed",
  };

  function showCommitted(decision) {
    committed = true;
    $("review-form").hidden = true;
    $("sealed").hidden = false;
    text("sealed-outcome", outcomeNames[decision.decision] || "Review recorded");
    text("sealed-receipt", "Review receipt · SHA-256 " + decision.reviewSha256);
    text("status", "One human review receipt sealed · read-only");
    if (decision.decision === "ANOTHER_EXPERIMENT" &&
        context && context.constraints.nextQuestionToolsConfigured) {
      loadNextQuestion();
    }
  }

  async function fetchContext() {
    const response = await fetch("/api/context", {cache:"no-store"});
    if (!response.ok) throw new Error("Couldn't verify the local review pair.");
    const data = await response.json();
    if (data.schema !== "vidmage/band-iq-review-ui/v1") {
      throw new Error("Unknown local evidence contract.");
    }
    return data;
  }

  function applyContext(data) {
    context = data;
    a.src = data.renderers.a.url;
    b.src = data.renderers.b.url;
    text("sha-a", data.renderers.a.sha256.slice(0,24) + "…");
    text("sha-b", data.renderers.b.sha256.slice(0,24) + "…");
    text("status", data.status === "recorded" ? "Recorded" : "Awaiting explicit human review");
    text("lens", "LENS · " + data.selection.lensId);
    text("window", "SELECTED WINDOW · " + data.selection.targetStart.toFixed(2) +
      "–" + data.selection.targetEnd.toFixed(2) + " seconds");
    text("pair", data.comparisonSha256);
    text("same-audio", data.source.audioSame ? "Verified same" : "HOLD");
    text("same-images", data.source.imagesSame ? "Verified same" : "HOLD");
    text("same-question", data.source.questionSame ? "Verified same" : "HOLD");
    if (data.decision) showCommitted(data.decision);
  }

  function fillOptions(element, choices) {
    element.replaceChildren();
    for (const [value, label] of choices) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      element.appendChild(option);
    }
  }

  function activeExperiment() {
    if (!nextSet) return null;
    const checked = document.querySelector('input[name="next-operation"]:checked');
    return checked ? nextSet.proposals.find(p => p.kind === checked.value) : null;
  }

  function refreshReplacement() {
    const selected = activeExperiment();
    if (!selected || selected.kind !== "SWAP_CARD") return;
    const choices = selected.eligibleReplacementAssetIdsByShot[$("next-shot").value] || [];
    fillOptions($("next-replacement"), choices.map(id => [id, id]));
  }

  function updateNextControls() {
    const selected = activeExperiment();
    const hasShot = selected && selected.kind !== "CHANGE_LENS";
    $("next-shot-fields").hidden = !hasShot;
    $("next-replacement-fields").hidden = !selected || selected.kind !== "SWAP_CARD";
    $("next-focus-fields").hidden = !selected || selected.kind !== "REFOCUS_CARD";
    $("next-lens-fields").hidden = !selected || selected.kind !== "CHANGE_LENS";
    if (hasShot) {
      fillOptions($("next-shot"),selected.eligibleShotIds.map(id => [id,id]));
      refreshReplacement();
    } else if (selected) {
      fillOptions($("next-lens"),selected.eligibleLensIds.map(id => [id,id]));
    }
  }

  async function loadNextQuestion() {
    if (nextSet || nextRendered) return;
    $("next-lab").hidden = false;
    text("next-feedback", "Verifying the author's question and the exact source films…");
    try {
      const response = await fetch("/api/next/questions", {cache:"no-store"});
      const result = await response.json();
      if (!response.ok || !result.ok || !result.questions) {
        throw new Error(result.message || "Next-question material not yet available.");
      }
      nextSet = result.questions;
      text("next-question-text", "Your question: “" + nextSet.humanQuestionVerbatim + "”");
      for (const radio of document.querySelectorAll('input[name="next-operation"]')) {
        const proposal = nextSet.proposals.find(p => p.kind === radio.value);
        radio.disabled = !proposal || proposal.status !== "proposal-only";
      }
      const first = [...document.querySelectorAll('input[name="next-operation"]')]
        .find(radio => !radio.disabled);
      if (first) first.checked = true;
      updateNextControls();
      text("next-feedback", "Choose one experimental operation. None has run.");
    } catch (error) {
      text("next-feedback",error.message || "Source verification refused.");
      $("next-commit").disabled = true;
    }
  }

  async function submitNext(event) {
    event.preventDefault();
    if (!nextSet || nextRendered || !context) return;
    const proposal = activeExperiment();
    if (!proposal || proposal.status !== "proposal-only") {
      text("next-feedback", "No available experiment is selected.");
      return;
    }
    const kind = proposal.kind;
    const choice = {
      schema:"vidmage/band-iq-005-trial-authorization/v1",
      questionSetSha256:nextSet.questionSetSha256,
      proposalSha256:proposal.proposalSha256,
      operatorAttestationId:$("next-operator").value.trim(),
      decision:"RENDER_ONE_LOCAL_TRIAL",
      shotId:kind === "CHANGE_LENS" ? null : $("next-shot").value,
      replacementAssetId:kind === "SWAP_CARD" ? $("next-replacement").value : null,
      newFocus:kind === "REFOCUS_CARD"
        ? [Number($("next-focus-x").value),Number($("next-focus-y").value)] : null,
      newLensId:kind === "CHANGE_LENS" ? $("next-lens").value : null,
      allowLocalExecution:true,
      allowPaidProviders:false,
      allowNetworkUpload:false,
    };
    if (!choice.operatorAttestationId || !$("next-acknowledge").checked) {
      text("next-feedback", "A new independent signature and acknowledgement are required.");
      return;
    }
    const approved = window.confirm(
      "Render one NEW local trial of " + kind + "?\n\n" +
      "Source films and the earlier review will remain unchanged. " +
      "This does not select KEEP or publish anything."
    );
    if (!approved) return;
    $("next-commit").disabled = true;
    text("next-feedback","Rendering your one approved local experiment…");
    try {
      const response = await fetch("/api/next/execute",{
        method:"POST",cache:"no-store",
        headers:{"Content-Type":"application/json",
                 "X-Review-Token":context.reviewToken},
        body:JSON.stringify({authorization:choice}),
      });
      const result=await response.json();
      if (!response.ok || !result.ok || !result.trial) {
        throw new Error(result.message || "The trial was refused.");
      }
      nextRendered=true;
      $("next-form").hidden=true;
      $("next-result").hidden=false;
      $("next-video").src="/media/next";
      text("next-sha","Verified third-film SHA-256 "+result.trial.movieSha256);
      text("next-feedback","Local trial completed. A new human review is still required to KEEP.");
      $("question-lab").hidden=!context.constraints.nativeQuestionDoctorConfigured;
    } catch (error) {
      text("next-feedback",error.message || "The new trial was refused.");
      $("next-commit").disabled=false;
    }
  }

  function changeAudio(master) {
    a.muted = master !== "a";
    b.muted = master !== "b";
  }

  async function playBoth() {
    const lead = a.readyState >= 1 ? a : b;
    if (lead.readyState >= 1) {
      const target = lead.currentTime;
      if (a.readyState >= 1) a.currentTime = target;
      if (b.readyState >= 1) b.currentTime = target;
    }
    const settled = await Promise.allSettled([a.play(), b.play()]);
    if (settled.some((x) => x.status === "rejected")) {
      text("feedback", "Your browser blocked playback; use the individual video controls.");
    }
  }

  function pauseBoth() {
    a.pause();
    b.pause();
  }

  function updateQuestionVisibility() {
    const chosen = document.querySelector('input[name="decision"]:checked');
    const show = chosen && chosen.value === "ANOTHER_EXPERIMENT";
    $("question").hidden = !show;
    $("question-label").hidden = !show;
    $("question").required = !!show;
    if (!show) $("question").value = "";
  }

  async function submit(event) {
    event.preventDefault();
    if (committed || !context) return;
    const decision = document.querySelector('input[name="decision"]:checked');
    if (!decision) {
      text("feedback", "Select one disposition.");
      return;
    }
    const payload = {
      decision: decision.value,
      operatorAttestationId: $("operator").value.trim(),
      rationale: $("rationale").value,
      nextQuestion: $("question").value,
      acknowledgedTrialOnly: $("acknowledge").checked,
    };
    if (!payload.operatorAttestationId || !payload.acknowledgedTrialOnly ||
        (payload.decision === "ANOTHER_EXPERIMENT" && !payload.nextQuestion.trim())) {
      text("feedback", "An explicit signature, acknowledgement, and any required question are needed.");
      return;
    }
    const summary = outcomeNames[payload.decision];
    const approved = window.confirm(
      "Record this as the ONE enduring local review decision?\n\n" +
      summary + "\n\nThis will NOT render, export, publish, or delete files."
    );
    if (!approved) return;
    $("commit").disabled = true;
    text("feedback", "Checking source evidence and sealing your decision…");
    try {
      const response = await fetch("/api/decision", {
        method: "POST",
        cache: "no-store",
        headers: {"Content-Type":"application/json","X-Review-Token":context.reviewToken},
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok || !result.ok || !result.receipt) {
        throw new Error(result.message || "The source or choice was refused.");
      }
      showCommitted(result.receipt);
      text("feedback", "Decision sealed. Original films remain unchanged.");
    } catch (error) {
      text("feedback", error.message || "The decision could not be recorded.");
      try {
        const fresh = await fetchContext();
        if (fresh.decision) showCommitted(fresh.decision);
      } catch {}
    } finally {
      $("commit").disabled = committed;
    }
  }

  async function inspectQuestionLab() {
    if (!nextRendered || !context || !context.constraints.nativeQuestionDoctorConfigured) {
      text("question-lab-status","A performed third film and native source-pinned Doctor are required.");
      return;
    }
    const consent=window.confirm(
      "Inspect the TWO actual local MP4s with the native Blender Doctor? " +
      "This read-only analysis samples pixels and records an immutable receipt; " +
      "it does NOT choose a film, change edits, or publish anything."
    );
    if (!consent) return;
    $("question-lab-inspect").disabled=true;
    text("question-lab-status","Measuring native Blender windows and real frame pixels…");
    try {
      const response=await fetch("/api/next/observe",{
        method:"POST",cache:"no-store",
        headers:{"Content-Type":"application/json","X-Review-Token":context.reviewToken},
        body:JSON.stringify({inspectActualFilms:true}),
      });
      const result=await response.json();
      if (!response.ok || !result.ok || !result.observation) {
        throw new Error(result.message || "Source verification refused.");
      }
      const observed=result.observation;
      text("lab-human-question",observed.humanQuestionVerbatim);
      const edit=observed.humanChosenEdit;
      text("lab-edit",observed.humanChosenOperation+
        (edit.shotId ? " · "+edit.shotId : "")+
        (edit.toLensId ? " · "+edit.toLensId : ""));
      text("lab-overall",(observed.sampling.pixelMAEAcrossSong*100).toFixed(2)+
        "% mean absolute grayscale pixel difference, not a quality score");
      $("lab-timeline").replaceChildren();
      for (const item of observed.windows) {
        const row=document.createElement("div");
        row.className="lab-window";
        const label=document.createElement("div");
        label.textContent=item.start.toFixed(1)+"–"+item.end.toFixed(1)+"s · "+
          (item.operatorEditOverlapsThisWindow?"Selected edit overlaps":"Outside selected edit");
        const rail=document.createElement("div");
        rail.className="lab-rail";
        const bar=document.createElement("div");
        bar.className="lab-difference";
        bar.style.width=Math.min(100,item.pixelMeanAbsoluteDifference*100)+"%";
        rail.appendChild(bar);
        const caption=document.createElement("small");
        caption.textContent=(item.pixelMeanAbsoluteDifference*100).toFixed(2)+
          "% pixel difference · "+(item.changedFrameFractionAt2PctMAE*100).toFixed(0)+
          "% sampled frames exceed 2% · non-stillness Δ "+
          item.nativeDoctor.nonStillnessDelta.toFixed(3);
        row.append(label,rail,caption);
        $("lab-timeline").appendChild(row);
      }
      $("lab-questions").replaceChildren();
      for (const candidate of observed.possibleNextQuestions) {
        const li=document.createElement("li");
        li.textContent=candidate.question+" (human choice needed; no execution)";
        $("lab-questions").appendChild(li);
      }
      text("lab-sha","Source-verified observation · "+observed.observationSha256);
      $("question-lab-results").hidden=false;
      text("question-lab-status","Actual film comparison recorded. No new creative choice made.");
    } catch(error) {
      text("question-lab-status",error.message || "Actual media comparison refused.");
      $("question-lab-inspect").disabled=false;
    }
  }

  $("play").addEventListener("click", playBoth);
  $("pause").addEventListener("click", pauseBoth);
  $("sync").addEventListener("click", () => {
    if (Number.isFinite(a.currentTime)) b.currentTime = a.currentTime;
  });
  document.querySelectorAll('input[name="sound"]').forEach((radio) => {
    radio.addEventListener("change", () => { if (radio.checked) changeAudio(radio.value); });
  });
  document.querySelectorAll('input[name="decision"]').forEach((radio) => {
    radio.addEventListener("change", updateQuestionVisibility);
  });
  $("review-form").addEventListener("submit", submit);
  $("next-form").addEventListener("submit",submitNext);
  $("question-lab-inspect").addEventListener("click",inspectQuestionLab);
  $("next-shot").addEventListener("change",refreshReplacement);
  document.querySelectorAll('input[name="next-operation"]').forEach(radio => {
    radio.addEventListener("change",updateNextControls);
  });
  changeAudio("a");
  fetchContext().then(applyContext).catch((error) => {
    text("status", "HOLD · local review unavailable");
    text("feedback", error.message || "The comparison could not be loaded.");
    $("commit").disabled = true;
  });
})();
