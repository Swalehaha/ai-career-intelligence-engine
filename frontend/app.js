const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const THEME_KEY = "acie-theme";

const form = document.getElementById("analyze");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const btnLabel = submitBtn.querySelector(".btn-label");
const btnSpinner = submitBtn.querySelector(".btn-spinner");
const btnArrow = submitBtn.querySelector(".btn-arrow");
const results = document.getElementById("results");
const resumeInput = document.getElementById("resume");
const jdInput = document.getElementById("job_description");
const targetRoleInput = document.getElementById("target_role");
const fileMeta = document.getElementById("file-meta");
const fileError = document.getElementById("file-error");
const jdError = document.getElementById("jd-error");
const errorBox = document.getElementById("error-box");
const errorText = document.getElementById("error-text");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const resumeTitle = document.getElementById("resume-title");
const resumeSub = document.getElementById("resume-sub");
const uploadShell = document.querySelector(".upload-shell");
const statusPdf = document.getElementById("status-pdf");
const statusJd = document.getElementById("status-jd");
const statusReady = document.getElementById("status-ready");
const themeToggle = document.getElementById("theme-toggle");
const startCta = document.getElementById("start-cta");

const LOADING_STAGES = [
  "Extracting resume…",
  "Matching skills…",
  "Analyzing skill gaps…",
  "Preparing your career insights…",
];

let loadingTimer = null;
let loadingStageIndex = 0;

initTheme();
updateReadiness();
updateNavActive();
syncUiFromHash();

resumeInput.addEventListener("change", () => {
  clearFieldError(fileError);
  updateFileMeta(resumeInput.files[0] || null);
  updateReadiness();
});

jdInput.addEventListener("input", () => {
  if (jdInput.value.trim()) clearFieldError(jdError);
  updateReadiness();
});

if (targetRoleInput) {
  targetRoleInput.addEventListener("input", updateReadiness);
}

if (themeToggle) {
  themeToggle.addEventListener("click", toggleTheme);
  themeToggle.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleTheme();
    }
  });
}

if (startCta) {
  startCta.addEventListener("click", () => enterWorkspace(true));
}

document.querySelectorAll('.nav-link[data-nav="analyze"]').forEach((link) => {
  link.addEventListener("click", (event) => {
    if (document.body.classList.contains("ui-landing")) {
      event.preventDefault();
      enterWorkspace(true);
    }
  });
});

window.addEventListener("hashchange", () => {
  syncUiFromHash();
  updateNavActive();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  hideResultsContent();

  const resume = resumeInput.files[0];
  const jobDescription = jdInput.value.trim();

  if (!validateClient(resume, jobDescription)) {
    updateReadiness();
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
    setStatus("");
  } catch (error) {
    console.error("Analyze request failed:", error);
    showError(
      "The analysis service took too long to respond. This can happen after the app has been idle. Please try again."
    );
    setStatus("");
  } finally {
    setAnalyzing(false);
  }
});

function initTheme() {
  const current =
    document.documentElement.getAttribute("data-theme") ||
    localStorage.getItem(THEME_KEY) ||
    "dark";
  applyTheme(current, false);
}

function toggleTheme() {
  const current =
    document.documentElement.getAttribute("data-theme") === "light"
      ? "light"
      : "dark";
  applyTheme(current === "dark" ? "light" : "dark", true);
}

function applyTheme(theme, persist) {
  const next = theme === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  if (persist) {
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* ignore quota / private mode */
    }
  }
  if (themeToggle) {
    themeToggle.setAttribute(
      "aria-label",
      next === "dark" ? "Switch to light theme" : "Switch to dark theme"
    );
  }
}

function syncUiFromHash() {
  const hash = (window.location.hash || "").replace("#", "");
  if (hash === "analyze" || hash === "insights" || hash === "gaps") {
    enterWorkspace(false);
  }
  if ((hash === "insights" || hash === "gaps") && !document.body.classList.contains("has-results")) {
    // Anchors only meaningful after results; still open workspace.
  }
}

function enterWorkspace(scroll) {
  document.body.classList.remove("ui-landing");
  document.body.classList.add("ui-workspace");
  if (scroll) {
    const target = document.getElementById("workspace-shell") || form;
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (history.replaceState) {
      history.replaceState(null, "", "#analyze");
    } else {
      window.location.hash = "analyze";
    }
  }
  updateNavActive();
}

function updateNavActive() {
  const hash = (window.location.hash || "").replace("#", "");
  const effective = hash || (document.body.classList.contains("ui-landing") ? "landing" : "analyze");
  document.querySelectorAll(".nav-link").forEach((link) => {
    const target = (link.getAttribute("href") || "").replace("#", "");
    link.classList.toggle(
      "is-active",
      target === effective || (!hash && target === "analyze" && !document.body.classList.contains("ui-landing"))
    );
  });
}

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
    if (resumeTitle) resumeTitle.textContent = "Upload your resume";
    if (resumeSub) resumeSub.textContent = "PDF only · Drag & drop or browse";
    if (uploadShell) uploadShell.classList.remove("has-file");
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

  if (resumeTitle) resumeTitle.textContent = file.name;
  if (resumeSub) {
    resumeSub.textContent = valid
      ? `PDF · ${formatBytes(file.size)} · Ready`
      : "PDF · Invalid";
  }
  if (uploadShell) uploadShell.classList.toggle("has-file", valid);
}

function updateReadiness() {
  const resume = resumeInput.files[0];
  const pdfOk =
    !!resume &&
    hasPdfExtension(resume.name) &&
    resume.size <= MAX_UPLOAD_BYTES;
  const jdOk = !!jdInput.value.trim();

  if (statusPdf) statusPdf.classList.toggle("is-ready", pdfOk);
  if (statusJd) statusJd.classList.toggle("is-ready", jdOk);
  if (statusReady) statusReady.classList.toggle("is-ready", pdfOk && jdOk);
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
  if (btnArrow) btnArrow.classList.toggle("hidden", isAnalyzing);
  btnLabel.textContent = isAnalyzing ? "Analyzing…" : "Analyze my match";

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

function hideResultsContent() {
  results.classList.add("hidden");
  // Keep compact bar if already in results state (re-analyze flow).
}

function enterResultsState() {
  document.body.classList.remove("ui-landing");
  document.body.classList.add("ui-workspace");
  document.body.classList.add("has-results");
  results.classList.remove("hidden");
}

function interpretScore(score) {
  if (score >= 80) {
    return {
      label: "Strong Match",
      summary:
        "Your profile covers most of the core requirements for this role.",
    };
  }
  if (score >= 55) {
    return {
      label: "Moderate Match",
      summary:
        "You match several requirements, with clear gaps to address before applying.",
    };
  }
  if (score >= 30) {
    return {
      label: "Limited Match",
      summary:
        "Prioritize the skill gaps below to strengthen your fit for this posting.",
    };
  }
  return {
    label: "Weak Match",
    summary:
      "Consider a better-fit role or a targeted resume rewrite for this posting.",
  };
}

function renderResults(data) {
  enterResultsState();

  const score = Number(data.overall_score || 0);
  const interpretation = interpretScore(score);

  const scoreRing = document.querySelector(".score-ring");
  document.getElementById("score-value").textContent = score.toFixed(1);
  if (scoreRing) {
    scoreRing.style.setProperty("--score-angle", "0deg");
    scoreRing.classList.remove("is-animating");
    // Force reflow so the ring animates on each successful analysis.
    void scoreRing.offsetWidth;
    requestAnimationFrame(() => {
      scoreRing.style.setProperty(
        "--score-angle",
        `${Math.min(score, 100) * 3.6}deg`
      );
      scoreRing.classList.add("is-animating");
    });
  }

  const badge = document.getElementById("score-badge");
  if (badge) badge.textContent = interpretation.label;

  document.getElementById("score-headline").textContent = "Career Snapshot";
  document.getElementById("score-summary").textContent = interpretation.summary;

  const roleEl = document.getElementById("results-role");
  const role = targetRoleInput && targetRoleInput.value.trim();
  if (roleEl) {
    if (role) {
      roleEl.textContent = `Target role: ${role}`;
      roleEl.classList.remove("hidden");
    } else {
      roleEl.textContent = "";
      roleEl.classList.add("hidden");
    }
  }

  const heading = document.getElementById("results-heading");
  if (heading) {
    heading.textContent = role
      ? `Here's how your profile matches ${role}.`
      : "Here's how your profile matches the target role.";
  }

  const analyzedAt = document.getElementById("analyzed-at");
  if (analyzedAt) {
    analyzedAt.textContent = `Analyzed on ${new Date().toLocaleString()}`;
  }

  const breakdown = data.score_breakdown || {};

  const matched = data.matched_skills || [];
  const semantic = data.semantic_matched_skills || [];
  const partial = data.partial_skills || [];
  const missing = data.missing_skills || [];
  const exactCount = breakdown.exact_matched_count ?? matched.length;
  const semanticCount = breakdown.semantic_matched_count ?? semantic.length;
  const partialCount = breakdown.partial_count ?? partial.length;
  const relatedCount = semanticCount + partialCount;
  const jdCount =
    breakdown.jd_skill_count ?? (data.jd_skills || []).length;

  const stats = document.getElementById("score-stats");
  stats.innerHTML = "";
  const statItems = [
    { value: exactCount, label: "Exact" },
    { value: semanticCount, label: "Semantic" },
    { value: partialCount, label: "Partial" },
    { value: jdCount, label: "JD Skills" },
  ];
  for (const item of statItems) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${item.value}</strong><span>${item.label}</span>`;
    stats.appendChild(li);
  }

  setCardCount("card-matched", matched.length);
  setCardCount("card-related", relatedCount);
  setCardCount("card-gaps", missing.length);
  setCardCount("card-jd", jdCount);
  fillSnapshotInsights({
    exactCount,
    relatedCount,
    gapCount: missing.length,
    jdCount,
    matched,
  });

  fillChips("matched-list", matched);
  fillRelated("related-list", semantic, partial);
  fillChips("missing-list", missing, "missing");
  fillGaps(data.prioritized_gaps || []);
  fillRecommendations(data.recommendations || {}, data.prioritized_gaps || []);

  results.scrollIntoView({ behavior: "smooth", block: "start" });
  updateNavActive();
}

function fillSnapshotInsights({
  exactCount,
  relatedCount,
  gapCount,
  jdCount,
  matched,
}) {
  const el = document.getElementById("snapshot-insights");
  if (!el) return;
  el.innerHTML = "";

  const lines = [];
  if (jdCount > 0) {
    lines.push(
      `${exactCount} of ${jdCount} requirements found directly`
    );
  }
  if (relatedCount > 0) {
    lines.push(`${relatedCount} related skills identified`);
  }
  if (gapCount > 0) {
    lines.push(
      `${gapCount} skill${gapCount === 1 ? "" : "s"} missing`
    );
  }
  if (matched.length) {
    lines.push(
      `Your strongest overlap: ${matched.slice(0, 3).join(" / ")}`
    );
  }

  for (const line of lines) {
    const li = document.createElement("li");
    li.textContent = line;
    el.appendChild(li);
  }
}

function setCardCount(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = String(value);
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
    li.innerHTML = `
      <span class="rel-jd">${escapeHtml(item.jd_skill || "")}</span>
      <span class="rel-approx">≈</span>
      <span class="rel-resume">${escapeHtml(item.resume_skill || "")}</span>
      <span class="rel-meta">${escapeHtml(String(item.similarity ?? ""))} · ${label}</span>
    `;
    el.appendChild(li);
  }
}

function fillGaps(gaps) {
  const el = document.getElementById("gaps-list");
  el.innerHTML = "";
  if (!gaps.length) {
    const li = document.createElement("li");
    li.className = "empty-priority";
    li.textContent = "No prioritized gaps — strong coverage for this role.";
    el.appendChild(li);
    return;
  }
  for (const gap of gaps) {
    const li = document.createElement("li");
    const rank = String(gap.rank ?? "").padStart(2, "0") || "—";
    const status = gap.status || "missing";
    const statusClass = status === "partial" ? "partial" : "";
    li.innerHTML = `
      <span class="rank">${rank}</span>
      <div class="priority-body">
        <div class="priority-title">
          <strong>${escapeHtml(gap.skill || "")}</strong>
          <span class="status-pill ${statusClass}">${escapeHtml(status)}</span>
        </div>
        <p class="reason">${escapeHtml(gap.reason || "")}</p>
      </div>
    `;
    el.appendChild(li);
  }
}

function fillRecommendations(recs, gaps) {
  const note = document.getElementById("recs-note");
  if (note) {
    note.textContent =
      "A personalized action plan to get you job-ready. " +
      (recs.note ||
        "Suggestions are deterministic templates derived from skill gaps.");
  }

  const tips = recs.resume_suggestions || [];
  const questions = recs.interview_questions || [];
  const missingSkills = new Set(
    (gaps || []).filter((g) => g.status === "missing").map((g) => g.skill)
  );

  const build = [];
  const learn = [];
  const improve = [];

  for (const tip of tips) {
    const lower = (tip.suggestion || "").toLowerCase();
    if (lower.includes("portfolio project") || lower.includes("demonstrates")) {
      build.push(tip);
      if (tip.skill && missingSkills.has(tip.skill)) {
        learn.push(tip);
      }
    } else if (tip.skill && missingSkills.has(tip.skill)) {
      learn.push(tip);
    } else {
      improve.push(tip);
    }
  }

  if (!build.length) {
    for (const q of questions) {
      if ((q.question || "").toLowerCase().includes("project")) {
        build.push({ skill: q.skill, suggestion: q.question });
      }
    }
  }

  if (!improve.length) {
    for (const tip of tips) {
      if (!build.includes(tip)) improve.push(tip);
    }
  }

  renderTipList("move-build", build);
  renderTipList("move-learn", learn);
  renderTipList("move-improve", improve);

  const qEl = document.getElementById("interview-qs");
  qEl.innerHTML = "";
  if (!questions.length) {
    qEl.innerHTML = "<li class='muted'>No questions right now.</li>";
  } else {
    for (const q of questions) {
      const li = document.createElement("li");
      li.innerHTML = `${escapeHtml(q.question || "")}
        <span class="reason">${escapeHtml(q.intent || "")}</span>`;
      qEl.appendChild(li);
    }
  }
}

function renderTipList(elementId, tips) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.innerHTML = "";
  if (!tips.length) {
    el.innerHTML =
      "<li class='empty-tip muted'>No items for this category right now.</li>";
    return;
  }
  for (const tip of tips) {
    const li = document.createElement("li");
    const label = tip.skill ? `<strong>${escapeHtml(tip.skill)}:</strong> ` : "";
    li.innerHTML = `${label}${escapeHtml(tip.suggestion || "")}`;
    el.appendChild(li);
  }
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ============================================================
   DESIGN SYSTEM ENHANCEMENTS
   Appended — no existing functionality modified.
   ============================================================ */

// Check for reduced motion preference
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
).matches;

// ——— Navbar scroll-aware backdrop shadow ———
(function initNavbarScroll() {
  const header = document.querySelector(".site-header");
  if (!header) return;

  function onScroll() {
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll(); // run once on load
})();

// ——— Score count-up animation ———
/**
 * Animates the score value from 0 up to `target` over `duration` ms.
 * Respects prefers-reduced-motion: shows final value immediately.
 */
function animateScoreCountUp(target, duration) {
  const el = document.getElementById("score-value");
  if (!el) return;

  if (prefersReducedMotion) {
    el.textContent = target.toFixed(1);
    return;
  }

  const start = performance.now();
  const from = 0;

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // Ease-out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = from + (target - from) * eased;
    el.textContent = current.toFixed(1);

    if (progress < 1) {
      requestAnimationFrame(tick);
    } else {
      el.textContent = target.toFixed(1);
    }
  }

  requestAnimationFrame(tick);
}

// ——— Chip stagger-in animation ———
/**
 * After chips are added to the DOM, reveal them with a staggered fade-up.
 */
function staggerChips(listId, delayPerItem) {
  if (prefersReducedMotion) {
    // Make all chips instantly visible
    const list = document.getElementById(listId);
    if (!list) return;
    list.querySelectorAll("li").forEach((li) => {
      li.classList.add("chip-visible");
    });
    return;
  }

  const list = document.getElementById(listId);
  if (!list) return;
  const items = list.querySelectorAll("li");
  items.forEach((li, i) => {
    setTimeout(() => {
      li.classList.add("chip-visible");
    }, i * (delayPerItem || 45));
  });
}

// ——— IntersectionObserver scroll reveals ———
(function initScrollReveals() {
  if (prefersReducedMotion) return;

  const sections = document.querySelectorAll(
    ".result-section, .score-panel, .reveal-section"
  );
  if (!sections.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
  );

  sections.forEach((el) => observer.observe(el));

  // Re-observe after results appear (they're hidden initially)
  const resultsEl = document.getElementById("results");
  if (resultsEl) {
    const mutationObserver = new MutationObserver(() => {
      resultsEl.querySelectorAll(".result-section, .score-panel").forEach((el) => {
        el.classList.remove("is-visible");
        observer.observe(el);
      });
    });
    mutationObserver.observe(resultsEl, { attributes: true, attributeFilter: ["class"] });
  }
})();

// ——— Patch renderResults to use count-up and chip stagger ———
// We wrap the existing renderResults call path at the end.
// After the original renderResults sets DOM content, trigger enhancements.
(function patchRenderResults() {
  const originalRenderResults = window.renderResults;
  // renderResults is not on window — use MutationObserver on #results instead.
  // Watch for results becoming visible, then trigger enhancements.
  const resultsEl = document.getElementById("results");
  if (!resultsEl) return;

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (
        mutation.type === "attributes" &&
        mutation.attributeName === "class" &&
        !resultsEl.classList.contains("hidden")
      ) {
        // Results just became visible — trigger enhancements
        setTimeout(() => {
          // Count-up score
          const scoreText = document.getElementById("score-value");
          if (scoreText) {
            const finalScore = parseFloat(scoreText.textContent) || 0;
            animateScoreCountUp(finalScore, 1050);
          }

          // Stagger matched chips
          staggerChips("matched-list", 48);

          // Stagger missing chips (slight delay)
          setTimeout(() => staggerChips("missing-list", 42), 120);

          // Make result sections visible via IntersectionObserver
          // (observer already set up — sections will trigger when scrolled into view)
          // For sections already in viewport, force-trigger:
          if (!prefersReducedMotion) {
            resultsEl.querySelectorAll(".result-section, .score-panel").forEach((el) => {
              const rect = el.getBoundingClientRect();
              if (rect.top < window.innerHeight) {
                el.classList.add("is-visible");
              }
            });
          }
        }, 80);
      }
    });
  });

  observer.observe(resultsEl, { attributes: true, attributeFilter: ["class"] });
})();
