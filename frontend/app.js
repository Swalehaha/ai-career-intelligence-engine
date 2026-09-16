const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

const form = document.getElementById("analyze-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const btnLabel = submitBtn.querySelector(".btn-label");
const btnSpinner = submitBtn.querySelector(".btn-spinner");
const results = document.getElementById("results");
const resumeInput = document.getElementById("resume");
const jdInput = document.getElementById("job_description");
const fileMeta = document.getElementById("file-meta");
const fileError = document.getElementById("file-error");
const jdError = document.getElementById("jd-error");
const errorBox = document.getElementById("error-box");
const errorText = document.getElementById("error-text");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");

const LOADING_STAGES = [
  "Extracting resume…",
  "Matching skills…",
  "Analyzing skill gaps…",
  "Preparing your career insights…",
];

let loadingTimer = null;
let loadingStageIndex = 0;

resumeInput.addEventListener("change", () => {
  clearFieldError(fileError);
  updateFileMeta(resumeInput.files[0] || null);
});

jdInput.addEventListener("input", () => {
  if (jdInput.value.trim()) clearFieldError(jdError);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  hideResults();

  const resume = resumeInput.files[0];
  const jobDescription = jdInput.value.trim();

  if (!validateClient(resume, jobDescription)) {
    return;
  }

  const body = new FormData();
  body.append("resume", resume);
  body.append("job_description", jobDescription);

  setAnalyzing(true);
  setStatus("Analysis in progress…");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body,
    });

    const parsed = await parseApiResponse(response);
    if (!parsed.ok) {
      showError(parsed.message);
      setStatus("");
      return;
    }

    renderResults(parsed.data);
    setStatus("Analysis complete.");
  } catch (error) {
    // Network / abort / unexpected client failures — never show raw JS errors
    console.error("Analyze request failed:", error);
    showError(
      "The analysis service took too long to respond. This can happen after the app has been idle. Please try again."
    );
    setStatus("");
  } finally {
    setAnalyzing(false);
  }
});

function validateClient(resume, jobDescription) {
  let valid = true;

  if (!resume) {
    showFieldError(fileError, "Please select a resume PDF.");
    valid = false;
  } else if (!hasPdfExtension(resume.name)) {
    showFieldError(fileError, "Resume must be a PDF file (.pdf).");
    updateFileMeta(resume, false);
    valid = false;
  } else if (resume.size > MAX_UPLOAD_BYTES) {
    showFieldError(
      fileError,
      "Your resume PDF is too large. Please upload a file smaller than 10 MB."
    );
    updateFileMeta(resume, false);
    valid = false;
  } else {
    updateFileMeta(resume, true);
  }

  if (!jobDescription) {
    showFieldError(jdError, "Please paste a job description.");
    valid = false;
  }

  return valid;
}

function hasPdfExtension(name) {
  return typeof name === "string" && name.toLowerCase().endsWith(".pdf");
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function updateFileMeta(file, isValid) {
  if (!file) {
    fileMeta.classList.add("hidden");
    fileMeta.textContent = "";
    return;
  }

  const valid =
    typeof isValid === "boolean"
      ? isValid
      : hasPdfExtension(file.name) && file.size <= MAX_UPLOAD_BYTES;

  fileMeta.classList.remove("hidden");
  fileMeta.classList.toggle("invalid", !valid);
  fileMeta.classList.toggle("valid", valid);
  fileMeta.textContent = `${file.name} · ${formatBytes(file.size)}${
    valid ? " · Ready" : " · Invalid"
  }`;
}

/**
 * Safely parse API responses without blindly calling response.json().
 * Never surfaces SyntaxError / "Unexpected end of JSON input" to the UI.
 */
async function parseApiResponse(response) {
  const status = response.status;
  let rawText = "";

  try {
    rawText = await response.text();
  } catch {
    return {
      ok: false,
      message:
        "The analysis service took too long to respond. This can happen after the app has been idle. Please try again.",
    };
  }

  const trimmed = (rawText || "").trim();
  if (!trimmed) {
    return {
      ok: false,
      message: messageForStatus(status, null),
    };
  }

  const contentType = (response.headers.get("content-type") || "").toLowerCase();
  const looksJson =
    contentType.includes("application/json") ||
    trimmed.startsWith("{") ||
    trimmed.startsWith("[");

  let data = null;
  if (looksJson) {
    try {
      data = JSON.parse(trimmed);
    } catch {
      return {
        ok: false,
        message: messageForStatus(status, null),
      };
    }
  } else {
    return {
      ok: false,
      message: messageForStatus(status, null),
    };
  }

  if (!response.ok) {
    return {
      ok: false,
      message: messageForStatus(status, data),
    };
  }

  return { ok: true, data };
}

function messageForStatus(status, payload) {
  if (status === 413) {
    return "Your resume PDF is too large. Please upload a file smaller than 10 MB.";
  }
  if (status === 422) {
    return "Some required information is missing. Please check your resume and job description.";
  }
  if (status === 400) {
    const detail = normalizeDetail(payload && payload.detail);
    if (detail && isSafeUserDetail(detail)) {
      return detail;
    }
    return "Please upload a valid PDF and provide a job description.";
  }
  if (status === 500) {
    return "We couldn't analyze your resume right now. Please try again.";
  }
  if (status === 502 || status === 504 || status === 503 || status === 0) {
    return "The analysis service took too long to respond. This can happen after the app has been idle. Please try again.";
  }
  if (!status || status >= 500) {
    return "We couldn't analyze your resume right now. Please try again.";
  }
  return "The analysis service took too long to respond. This can happen after the app has been idle. Please try again.";
}

function normalizeDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item.msg === "string") return item.msg;
        return "";
      })
      .filter(Boolean)
      .join(" ");
  }
  return "";
}

function isSafeUserDetail(text) {
  const lower = text.toLowerCase();
  const blocked = [
    "traceback",
    "exception",
    "torch",
    "cuda",
    "/opt/",
    "/home/",
    "site-packages",
    "unexpected end of json",
    "failed to execute",
  ];
  return !blocked.some((token) => lower.includes(token));
}

function setAnalyzing(isAnalyzing) {
  submitBtn.disabled = isAnalyzing;
  btnSpinner.classList.toggle("hidden", !isAnalyzing);
  btnLabel.textContent = isAnalyzing ? "Analyzing…" : "Analyze match";

  if (isAnalyzing) {
    loading.classList.remove("hidden");
    loadingStageIndex = 0;
    loadingText.textContent = LOADING_STAGES[0];
    clearInterval(loadingTimer);
    loadingTimer = setInterval(() => {
      loadingStageIndex = Math.min(
        loadingStageIndex + 1,
        LOADING_STAGES.length - 1
      );
      loadingText.textContent = LOADING_STAGES[loadingStageIndex];
    }, 2200);
  } else {
    loading.classList.add("hidden");
    clearInterval(loadingTimer);
    loadingTimer = null;
  }
}

function showError(message) {
  errorBox.classList.remove("hidden");
  errorText.textContent = message;
}

function clearErrors() {
  errorBox.classList.add("hidden");
  errorText.textContent = "";
  clearFieldError(fileError);
  clearFieldError(jdError);
}

function showFieldError(el, message) {
  el.textContent = message;
  el.classList.remove("hidden");
}

function clearFieldError(el) {
  el.textContent = "";
  el.classList.add("hidden");
}

function setStatus(text) {
  statusEl.textContent = text;
}

function hideResults() {
  results.classList.add("hidden");
}

function interpretScore(score) {
  if (score >= 80) {
    return "Strong alignment — your resume covers most of what this role asks for.";
  }
  if (score >= 55) {
    return "Moderate alignment — you match several requirements, with clear gaps to address.";
  }
  if (score >= 30) {
    return "Limited alignment — prioritize the skill gaps below before applying.";
  }
  return "Weak alignment for this posting — consider a better-fit role or a targeted resume rewrite.";
}

function renderResults(data) {
  results.classList.remove("hidden");

  const score = Number(data.overall_score || 0);
  document.getElementById("score-value").textContent = score.toFixed(1);
  document.querySelector(".score-ring").style.setProperty(
    "--score-angle",
    `${Math.min(score, 100) * 3.6}deg`
  );

  document.getElementById("score-headline").textContent = "Your match at a glance";
  document.getElementById("score-summary").textContent = interpretScore(score);

  const breakdown = data.score_breakdown || {};
  document.getElementById("score-formula").textContent =
    breakdown.formula ||
    "Score is a transparent heuristic over exact, semantic, and partial coverage.";

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
  fillRelated("related-list", data.semantic_matched_skills || [], data.partial_skills || []);
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
    li.textContent = "None found";
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

function fillRelated(elementId, semanticItems, partialItems) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  const combined = [
    ...semanticItems.map((item) => ({ ...item, kind: "semantic" })),
    ...partialItems.map((item) => ({ ...item, kind: "partial" })),
  ];

  if (!combined.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "None found";
    el.appendChild(li);
    return;
  }

  for (const item of combined) {
    const li = document.createElement("li");
    if (item.kind === "partial") li.className = "partial";
    const label = item.kind === "partial" ? "partial" : "related";
    li.textContent = `${item.jd_skill} ≈ ${item.resume_skill} (${item.similarity}, ${label})`;
    el.appendChild(li);
  }
}

function fillGaps(gaps) {
  const el = document.getElementById("gaps-list");
  el.innerHTML = "";
  if (!gaps.length) {
    const li = document.createElement("li");
    li.textContent = "No prioritized gaps — strong coverage for this role.";
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
  note.textContent =
    recs.note ||
    "Rule-based tips from skill gaps. They do not change the match score.";

  const tipsEl = document.getElementById("resume-tips");
  tipsEl.innerHTML = "";
  const tips = recs.resume_suggestions || [];
  if (!tips.length) {
    tipsEl.innerHTML = "<li class='muted'>No suggestions right now.</li>";
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
    qEl.innerHTML = "<li class='muted'>No questions right now.</li>";
  } else {
    for (const q of questions) {
      const li = document.createElement("li");
      li.innerHTML = `${q.question || ""}
        <span class="reason">${q.intent || ""}</span>`;
      qEl.appendChild(li);
    }
  }
}
