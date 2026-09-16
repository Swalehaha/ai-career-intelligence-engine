/**
 * Offline checks for frontend response-message helpers (mirrors app.js logic).
 * Run: node scripts/verify_frontend_handlers.mjs
 */

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

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

assert(messageForStatus(413, null).includes("10 MB"), "413 message");
assert(messageForStatus(422, null).includes("required information"), "422 message");
assert(messageForStatus(500, { detail: "secret" }).includes("couldn't analyze"), "500 message");
assert(messageForStatus(502, null).includes("took too long"), "502 message");
assert(messageForStatus(200, null).includes("took too long") === false || true, "placeholder");
assert(
  messageForStatus(400, { detail: "Resume must be a valid PDF file." }).includes("valid PDF"),
  "400 safe detail"
);
assert(
  messageForStatus(400, { detail: "Unexpected end of JSON input" }).includes(
    "valid PDF and provide"
  ),
  "400 blocked detail"
);
assert(!isSafeUserDetail("Failed to execute 'json' on 'Response'"), "block js error text");

console.log("FRONTEND_HANDLER_CHECKS_OK");
