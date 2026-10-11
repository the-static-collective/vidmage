"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const a = $("a"), b = $("b");
  let context = null;
  let committed = false;

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
  changeAudio("a");
  fetchContext().then(applyContext).catch((error) => {
    text("status", "HOLD · local review unavailable");
    text("feedback", error.message || "The comparison could not be loaded.");
    $("commit").disabled = true;
  });
})();
