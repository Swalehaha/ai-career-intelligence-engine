const form = document.getElementById("analyze-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const results = document.getElementById("results");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const resume = document.getElementById("resume").files[0];
  const jobDescription = document.getElementById("job_description").value.trim();

  if (!resume || !jobDescription) {
    statusEl.textContent = "Please provide both a resume PDF and a job description.";
    return;
  }

  const body = new FormData();
  body.append("resume", resume);
  body.append("job_description", jobDescription);

  submitBtn.disabled = true;
  statusEl.textContent = "Analyzing — extracting skills and running embeddings…";
  results.classList.add("hidden");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body,
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Analysis failed");
    }

    renderResults(payload);
    statusEl.textContent = "Analysis complete.";
  } catch (error) {
    statusEl.textContent = error.message || "Something went wrong.";
  } finally {
    submitBtn.disabled = false;
  }
});

function renderResults(data) {
  results.classList.remove("hidden");

  const score = Number(data.overall_score || 0);
  document.getElementById("score-value").textContent = score.toFixed(1);
  document.querySelector(".score-ring").style.setProperty(
    "--score-angle",
    `${Math.min(score, 100) * 3.6}deg`
  );

  const breakdown = data.score_breakdown || {};
  document.getElementById("score-formula").textContent =
    breakdown.formula ||
    "Score combines exact, semantic, and partial coverage.";

  const stats = document.getElementById("score-stats");
  stats.innerHTML = "";
  const statItems = [
    `Exact: ${breakdown.exact_matched_count ?? 0}`,
    `Semantic: ${breakdown.semantic_matched_count ?? 0}`,
    `Partial: ${breakdown.partial_count ?? 0}`,
    `JD skills: ${breakdown.jd_skill_count ?? (data.jd_skills || []).length}`,
  ];
  for (const item of statItems) {
    const li = document.createElement("li");
    li.textContent = item;
    stats.appendChild(li);
  }

  fillChips("matched-list", data.matched_skills || []);
  fillSemantic("semantic-list", data.semantic_matched_skills || []);
  fillPartial("partial-list", data.partial_skills || []);
  fillChips("missing-list", data.missing_skills || [], "missing");
  fillGaps(data.prioritized_gaps || []);
  fillRecommendations(data.recommendations || {});
}

function fillChips(elementId, items, className) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "None";
    el.appendChild(li);
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    if (className) li.className = className;
    li.textContent = item;
    el.appendChild(li);
  }
}

function fillSemantic(elementId, items) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "None";
    el.appendChild(li);
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = `${item.jd_skill} ≈ ${item.resume_skill} (${item.similarity})`;
    el.appendChild(li);
  }
}

function fillPartial(elementId, items) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "None";
    el.appendChild(li);
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.className = "partial";
    li.textContent = `${item.jd_skill} ≈ ${item.resume_skill} (${item.similarity})`;
    el.appendChild(li);
  }
}

function fillGaps(gaps) {
  const el = document.getElementById("gaps-list");
  el.innerHTML = "";
  if (!gaps.length) {
    const li = document.createElement("li");
    li.textContent = "No prioritized gaps — strong coverage.";
    el.appendChild(li);
    return;
  }
  for (const gap of gaps) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${gap.skill}</strong> <em>(${gap.status})</em>
      <span class="reason">${gap.reason || ""}</span>`;
    el.appendChild(li);
  }
}

function fillRecommendations(recs) {
  const note = document.getElementById("recs-note");
  note.textContent = recs.note || "Rule-based tips from skill gaps (not part of the score).";

  const tipsEl = document.getElementById("resume-tips");
  tipsEl.innerHTML = "";
  const tips = recs.resume_suggestions || [];
  if (!tips.length) {
    tipsEl.innerHTML = "<li class='muted'>No suggestions.</li>";
  } else {
    for (const tip of tips) {
      const li = document.createElement("li");
      const label = tip.skill ? `<strong>${tip.skill}:</strong> ` : "";
      li.innerHTML = `${label}${tip.suggestion || ""}`;
      tipsEl.appendChild(li);
    }
  }

  const qEl = document.getElementById("interview-qs");
  qEl.innerHTML = "";
  const questions = recs.interview_questions || [];
  if (!questions.length) {
    qEl.innerHTML = "<li class='muted'>No questions.</li>";
  } else {
    for (const q of questions) {
      const li = document.createElement("li");
      li.innerHTML = `${q.question || ""}
        <span class="reason">${q.intent || ""}</span>`;
      qEl.appendChild(li);
    }
  }
}
