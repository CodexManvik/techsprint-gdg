const state = {
  apiBase: "http://localhost:8000",
  token: localStorage.getItem("im_token") || "",
  sessionId: "",
  resumeText: "",
  ws: null,
  mediaRecorder: null,
  mediaChunks: [],
  stream: null,
  trackingInterval: null,
  pendingTurnStartTs: 0,
  perfEvents: [],
};

const jdPresets = {
  backend: `Role: Backend Engineer\nResponsibilities:\n- Build resilient APIs with Python/FastAPI and SQL databases\n- Design data models, optimize queries, and monitor reliability\n- Write tests and own production debugging\nRequirements:\n- 2+ years backend development\n- Strong API design, authentication, and performance tuning\n- Clear communication and ownership mindset`,
  frontend: `Role: Frontend Engineer\nResponsibilities:\n- Build production-grade interfaces with React and TypeScript\n- Translate product requirements into intuitive UX\n- Optimize performance and accessibility\nRequirements:\n- Strong JavaScript/TypeScript fundamentals\n- Experience with component architecture and testing\n- Good collaboration with design and backend teams`,
  ml: `Role: Machine Learning Engineer\nResponsibilities:\n- Build and deploy ML pipelines for prediction and ranking\n- Evaluate model quality and monitor drift in production\n- Collaborate with product teams on measurable impact\nRequirements:\n- Strong Python and SQL skills\n- Model evaluation, experimentation, and trade-off analysis\n- Experience shipping ML systems to production`,
  product: `Role: Product Analyst\nResponsibilities:\n- Define metrics, dashboards, and experiment frameworks\n- Analyze user behavior and present actionable insights\n- Partner with PM and engineering on roadmap impact\nRequirements:\n- Strong SQL and business reasoning\n- Ability to communicate quantitative findings clearly\n- Experience with A/B testing and funnel analysis`,
};

const el = {
  apiBase: document.getElementById("apiBase"),
  token: document.getElementById("token"),
  fullName: document.getElementById("fullName"),
  email: document.getElementById("email"),
  password: document.getElementById("password"),
  registerBtn: document.getElementById("registerBtn"),
  loginBtn: document.getElementById("loginBtn"),
  authStatus: document.getElementById("authStatus"),

  persona: document.getElementById("persona"),
  difficulty: document.getElementById("difficulty"),
  topic: document.getElementById("topic"),
  jdPreset: document.getElementById("jdPreset"),
  jobDescription: document.getElementById("jobDescription"),
  customInstructions: document.getElementById("customInstructions"),
  resumeFile: document.getElementById("resumeFile"),
  uploadResumeBtn: document.getElementById("uploadResumeBtn"),
  loadOptionsBtn: document.getElementById("loadOptionsBtn"),
  startInterviewBtn: document.getElementById("startInterviewBtn"),
  setupStatus: document.getElementById("setupStatus"),

  camera: document.getElementById("camera"),
  startCameraBtn: document.getElementById("startCameraBtn"),
  connectWsBtn: document.getElementById("connectWsBtn"),
  startTrackingBtn: document.getElementById("startTrackingBtn"),
  stopTrackingBtn: document.getElementById("stopTrackingBtn"),
  recordBtn: document.getElementById("recordBtn"),
  stopRecordBtn: document.getElementById("stopRecordBtn"),
  interviewStatus: document.getElementById("interviewStatus"),
  chatLog: document.getElementById("chatLog"),
  robot: document.getElementById("robot"),

  refreshReportBtn: document.getElementById("refreshReportBtn"),
  overallScore: document.getElementById("overallScore"),
  summary: document.getElementById("summary"),
  radarBars: document.getElementById("radarBars"),
  scorerStatus: document.getElementById("scorerStatus"),

  loadHistoryBtn: document.getElementById("loadHistoryBtn"),
  historyList: document.getElementById("historyList"),
  historyStatus: document.getElementById("historyStatus"),

  healthBtn: document.getElementById("healthBtn"),
  exportPerfBtn: document.getElementById("exportPerfBtn"),
  clearPerfBtn: document.getElementById("clearPerfBtn"),
  avgTurnLatency: document.getElementById("avgTurnLatency"),
  p95TurnLatency: document.getElementById("p95TurnLatency"),
  requestCount: document.getElementById("requestCount"),
  perfLog: document.getElementById("perfLog"),
  perfStatus: document.getElementById("perfStatus"),
};

function setStatus(target, message, level = "info") {
  target.textContent = message;
  if (level === "error") {
    target.style.color = "#ff8f8f";
  } else if (level === "ok") {
    target.style.color = "#84f2a6";
  } else {
    target.style.color = "";
  }
}

function addChat(role, text) {
  const item = document.createElement("article");
  item.className = `msg ${role}`;
  item.textContent = `${role === "ai" ? "AI" : "You"}: ${text}`;
  el.chatLog.appendChild(item);
  el.chatLog.scrollTop = el.chatLog.scrollHeight;
}

function authHeaders(includeJson = true) {
  const headers = {};
  if (includeJson) headers["Content-Type"] = "application/json";
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  return headers;
}

function normalizeBaseUrl() {
  state.apiBase = el.apiBase.value.trim().replace(/\/$/, "");
}

function wsUrlForSession(sessionId) {
  const base = state.apiBase.replace(/^http/, "ws");
  const tokenPart = state.token ? `?token=${encodeURIComponent(state.token)}` : "";
  return `${base}/ws/interview/${sessionId}${tokenPart}`;
}

function nowMs() {
  return performance.now();
}

function percentile(values, p) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.floor((p / 100) * (sorted.length - 1));
  return sorted[idx];
}

function recordPerf(name, durationMs, meta = "") {
  const entry = {
    ts: new Date().toISOString(),
    name,
    durationMs: Number(durationMs.toFixed(2)),
    meta,
  };
  state.perfEvents.push(entry);
  renderPerf();
}

function renderPerf() {
  el.requestCount.textContent = String(state.perfEvents.length);

  const turnLatencies = state.perfEvents
    .filter((e) => e.name === "turn_roundtrip")
    .map((e) => e.durationMs);

  if (turnLatencies.length) {
    const avg = turnLatencies.reduce((a, b) => a + b, 0) / turnLatencies.length;
    const p95 = percentile(turnLatencies, 95);
    el.avgTurnLatency.textContent = `${avg.toFixed(0)} ms`;
    el.p95TurnLatency.textContent = `${p95.toFixed(0)} ms`;
  } else {
    el.avgTurnLatency.textContent = "--";
    el.p95TurnLatency.textContent = "--";
  }

  el.perfLog.innerHTML = "";
  const tail = state.perfEvents.slice(-120).reverse();
  tail.forEach((evt) => {
    const row = document.createElement("div");
    row.className = "perf-row";
    row.innerHTML = `<span>${evt.name}</span><span>${evt.durationMs} ms</span><span>${evt.meta || ""}</span>`;
    el.perfLog.appendChild(row);
  });
}

function exportPerf() {
  const payload = {
    exported_at: new Date().toISOString(),
    session_id: state.sessionId,
    events: state.perfEvents,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `interview-perf-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  setStatus(el.perfStatus, "Performance JSON exported.", "ok");
}

async function timedFetch(name, url, options = {}, meta = "") {
  const start = nowMs();
  const response = await fetch(url, options);
  recordPerf(name, nowMs() - start, meta || url);
  return response;
}

async function loadConfigOptions() {
  normalizeBaseUrl();
  try {
    const resp = await timedFetch("config_options", `${state.apiBase}/api/config/options`);
    if (!resp.ok) throw new Error(`Config request failed (${resp.status})`);

    const data = await resp.json();
    hydrateSelect(el.persona, data.personas || []);
    hydrateSelect(el.difficulty, data.difficulties || []);
    hydrateSelect(el.topic, data.topics || []);
    setStatus(el.setupStatus, "Loaded persona, difficulty and topic options.", "ok");
  } catch (err) {
    setStatus(el.setupStatus, err.message, "error");
  }
}

function hydrateSelect(node, values) {
  node.innerHTML = "";
  values.forEach((entry) => {
    const value = typeof entry === "string" ? entry : entry?.name || "Unknown";
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    node.appendChild(opt);
  });
}

async function registerUser() {
  normalizeBaseUrl();
  const fullName = el.fullName.value.trim();
  const email = el.email.value.trim();
  const password = el.password.value;

  if (!fullName || !email || !password) {
    setStatus(el.authStatus, "Full name, email, and password are required for register.", "error");
    return;
  }

  try {
    const resp = await timedFetch(
      "auth_register",
      `${state.apiBase}/auth/register`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, email, password }),
      },
      email
    );
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Register failed (${resp.status}) ${text}`);
    }

    setStatus(el.authStatus, "Registration complete. You can log in now.", "ok");
  } catch (err) {
    setStatus(el.authStatus, err.message, "error");
  }
}

async function login() {
  normalizeBaseUrl();
  const email = el.email.value.trim();
  const password = el.password.value;
  if (!email || !password) {
    setStatus(el.authStatus, "Provide email and password.", "error");
    return;
  }

  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  try {
    const resp = await timedFetch(
      "auth_login",
      `${state.apiBase}/auth/login`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      },
      email
    );
    if (!resp.ok) throw new Error(`Login failed (${resp.status})`);

    const data = await resp.json();
    state.token = data.access_token;
    el.token.value = state.token;
    localStorage.setItem("im_token", state.token);
    setStatus(el.authStatus, "Authenticated. Token stored locally.", "ok");
  } catch (err) {
    setStatus(el.authStatus, err.message, "error");
  }
}

async function uploadResume() {
  normalizeBaseUrl();
  const file = el.resumeFile.files?.[0];
  if (!file) {
    setStatus(el.setupStatus, "Choose a PDF resume first.", "error");
    return;
  }
  if (!state.token) {
    setStatus(el.setupStatus, "Login or paste token before uploading resume.", "error");
    return;
  }

  const form = new FormData();
  form.append("file", file);

  try {
    setStatus(el.setupStatus, "Extracting resume text...");
    const resp = await timedFetch(
      "upload_resume",
      `${state.apiBase}/api/upload-resume`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${state.token}` },
        body: form,
      },
      file.name
    );
    if (!resp.ok) throw new Error(`Resume upload failed (${resp.status})`);

    const data = await resp.json();
    state.resumeText = data.text || "";
    setStatus(el.setupStatus, `Resume extracted (${state.resumeText.length} chars).`, "ok");
  } catch (err) {
    setStatus(el.setupStatus, err.message, "error");
  }
}

async function startInterview() {
  normalizeBaseUrl();
  state.token = el.token.value.trim();
  if (!state.token) {
    setStatus(el.setupStatus, "A valid token is required to start interview.", "error");
    return;
  }

  const body = {
    persona: el.persona.value,
    difficulty: el.difficulty.value,
    topic: el.topic.value,
    job_description: el.jobDescription.value.trim(),
    resume_text: state.resumeText || null,
    custom_instructions: el.customInstructions.value.trim() || null,
  };

  if (!body.job_description) {
    setStatus(el.setupStatus, "Provide a job description to keep interview on-track.", "error");
    return;
  }

  try {
    setStatus(el.setupStatus, "Starting interview session...");
    const resp = await timedFetch(
      "start_interview",
      `${state.apiBase}/api/start-interview`,
      {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify(body),
      },
      `${body.persona}/${body.topic}`
    );
    if (!resp.ok) {
      let details = "";
      try {
        const errPayload = await resp.json();
        details = errPayload?.detail ? `: ${JSON.stringify(errPayload.detail)}` : "";
      } catch {
        // Keep fallback status-only message if body is not JSON.
      }
      throw new Error(`Start interview failed (${resp.status})${details}`);
    }

    const data = await resp.json();
    state.sessionId = data.session_id;
    setStatus(el.setupStatus, `Session started: ${state.sessionId}`, "ok");
    setStatus(el.interviewStatus, "Session ready. Connect socket and record your answer.", "ok");
    addChat("ai", data.opening_question || "Interview started.");
  } catch (err) {
    setStatus(el.setupStatus, err.message, "error");
  }
}

function connectSocket() {
  if (!state.sessionId) {
    setStatus(el.interviewStatus, "Start interview first to get a session id.", "error");
    return;
  }

  if (state.ws && (state.ws.readyState === WebSocket.OPEN || state.ws.readyState === WebSocket.CONNECTING)) {
    setStatus(el.interviewStatus, "Socket already active (open/connecting).", "ok");
    return;
  }

  if (state.ws && state.ws.readyState === WebSocket.CLOSING) {
    setStatus(el.interviewStatus, "Socket is closing, wait a second and reconnect.", "info");
    return;
  }

  const wsOpenStart = nowMs();
  const url = wsUrlForSession(state.sessionId);
  const ws = new WebSocket(url);

  ws.onopen = () => {
    recordPerf("ws_connect", nowMs() - wsOpenStart, state.sessionId);
    setStatus(el.interviewStatus, "Socket connected. You can record answers now.", "ok");
  };

  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.type === "connected") {
        setStatus(el.interviewStatus, `Socket connected to session ${payload.session_id}.`, "ok");
        return;
      }
      if (payload.type === "error") {
        setStatus(el.interviewStatus, `${payload.code}: ${payload.message}`, "error");
        return;
      }
      if (payload.type === "ai_response") {
        if (state.pendingTurnStartTs > 0) {
          recordPerf("turn_roundtrip", nowMs() - state.pendingTurnStartTs, "audio->ai_response");
          state.pendingTurnStartTs = 0;
        }
        if (payload.transcript) addChat("user", payload.transcript);
        if (payload.reply) addChat("ai", payload.reply);
        if (payload.audio) playAiAudio(payload.audio);
      }
      if (payload.type === "metrics_update" && payload.alert) {
        setStatus(el.interviewStatus, payload.alert, payload.severity === "critical" ? "error" : "info");
      }
    } catch {
      setStatus(el.interviewStatus, "Received non-JSON message from websocket.", "error");
    }
  };

  ws.onerror = () => {
    setStatus(el.interviewStatus, "Websocket error encountered.", "error");
  };

  ws.onclose = (event) => {
    stopTrackingSimulation();
    const reason = event.reason ? ` reason=${event.reason}` : "";
    setStatus(el.interviewStatus, `Socket disconnected (code=${event.code}${reason}).`, "info");
  };

  state.ws = ws;
}

function startCamera() {
  navigator.mediaDevices
    .getUserMedia({ video: true, audio: true })
    .then((stream) => {
      state.stream = stream;
      el.camera.srcObject = stream;
      setStatus(el.interviewStatus, "Camera and microphone ready.", "ok");
    })
    .catch((err) => {
      setStatus(el.interviewStatus, `Camera access denied: ${err.message}`, "error");
    });
}

function base64FromBlob(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result;
      if (typeof result !== "string") {
        reject(new Error("Unexpected file reader output"));
        return;
      }
      const b64 = result.split(",")[1];
      resolve(b64);
    };
    reader.onerror = () => reject(new Error("Failed to encode audio"));
    reader.readAsDataURL(blob);
  });
}

function startRecording() {
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
    setStatus(el.interviewStatus, "Connect websocket before recording.", "error");
    return;
  }
  if (!state.stream) {
    setStatus(el.interviewStatus, "Start camera first to enable microphone.", "error");
    return;
  }

  state.mediaChunks = [];
  const rec = new MediaRecorder(state.stream, { mimeType: "audio/webm" });
  rec.ondataavailable = (e) => {
    if (e.data.size > 0) state.mediaChunks.push(e.data);
  };
  rec.onstop = async () => {
    try {
      const blob = new Blob(state.mediaChunks, { type: "audio/webm" });
      const audioB64 = await base64FromBlob(blob);
      state.pendingTurnStartTs = nowMs();
      state.ws.send(JSON.stringify({ type: "conversation", audio_data: audioB64 }));
      setStatus(el.interviewStatus, "Answer sent. Waiting for interviewer...", "info");
    } catch (err) {
      setStatus(el.interviewStatus, err.message, "error");
    }
  };

  rec.start();
  state.mediaRecorder = rec;
  el.recordBtn.disabled = true;
  el.stopRecordBtn.disabled = false;
  setStatus(el.interviewStatus, "Recording... click Stop when done.", "info");
}

function stopRecording() {
  if (!state.mediaRecorder || state.mediaRecorder.state === "inactive") return;
  state.mediaRecorder.stop();
  el.recordBtn.disabled = false;
  el.stopRecordBtn.disabled = true;
}

function makeLandmarksFrame() {
  const points = Array.from({ length: 500 }, () => ({ x: 0.5, y: 0.5 }));
  const jitter = () => (Math.random() - 0.5) * 0.01;

  points[1] = { x: 0.5 + jitter(), y: 0.55 + jitter() };
  points[33] = { x: 0.42 + jitter(), y: 0.45 + jitter() };
  points[133] = { x: 0.48 + jitter(), y: 0.45 + jitter() };
  points[263] = { x: 0.62 + jitter(), y: 0.45 + jitter() };
  points[468] = { x: 0.45 + jitter(), y: 0.45 + jitter() };
  points[55] = { x: 0.44 + jitter(), y: 0.36 + jitter() };
  points[285] = { x: 0.56 + jitter(), y: 0.36 + jitter() };
  points[61] = { x: 0.44 + jitter(), y: 0.62 + jitter() };
  points[291] = { x: 0.56 + jitter(), y: 0.62 + jitter() };

  return points;
}

function startTrackingSimulation() {
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
    setStatus(el.interviewStatus, "Connect websocket before streaming metrics.", "error");
    return;
  }
  if (state.trackingInterval) return;

  state.trackingInterval = setInterval(() => {
    const landmarks = makeLandmarksFrame();
    state.ws.send(JSON.stringify({ type: "tracking", landmarks }));
  }, 700);

  el.startTrackingBtn.disabled = true;
  el.stopTrackingBtn.disabled = false;
  setStatus(el.interviewStatus, "Metrics stream started (synthetic landmarks).", "ok");
}

function stopTrackingSimulation() {
  if (!state.trackingInterval) return;
  clearInterval(state.trackingInterval);
  state.trackingInterval = null;
  el.startTrackingBtn.disabled = false;
  el.stopTrackingBtn.disabled = true;
  setStatus(el.interviewStatus, "Metrics stream stopped.", "info");
}

function playAiAudio(base64Audio) {
  const binary = atob(base64Audio);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  const audioBlob = new Blob([bytes], { type: "audio/mpeg" });
  const url = URL.createObjectURL(audioBlob);
  const audio = new Audio(url);

  el.robot.classList.add("talking");
  audio.onended = () => {
    el.robot.classList.remove("talking");
    URL.revokeObjectURL(url);
  };
  audio.onerror = () => {
    el.robot.classList.remove("talking");
    URL.revokeObjectURL(url);
  };
  audio.play().catch(() => {
    el.robot.classList.remove("talking");
    URL.revokeObjectURL(url);
  });
}

async function refreshReport() {
  normalizeBaseUrl();
  if (!state.sessionId) {
    setStatus(el.scorerStatus, "Start interview first to fetch a report.", "error");
    return;
  }
  if (!state.token) {
    setStatus(el.scorerStatus, "Token is required for report endpoint.", "error");
    return;
  }

  try {
    setStatus(el.scorerStatus, "Fetching report...");
    const resp = await timedFetch(
      "fetch_report",
      `${state.apiBase}/api/report?session_id=${encodeURIComponent(state.sessionId)}`,
      { headers: authHeaders(false) },
      state.sessionId
    );
    if (!resp.ok) throw new Error(`Report failed (${resp.status})`);

    const data = await resp.json();
    el.overallScore.textContent = String(data.overallScore ?? "--");
    el.summary.textContent = data.summary || "No summary returned.";
    renderRadarBars(data.radarData || []);
    setStatus(el.scorerStatus, "Report updated.", "ok");
  } catch (err) {
    setStatus(el.scorerStatus, err.message, "error");
  }
}

function renderRadarBars(rows) {
  el.radarBars.innerHTML = "";
  rows.forEach((row) => {
    const wrap = document.createElement("div");
    wrap.className = "bar-row";

    const label = document.createElement("span");
    label.textContent = row.category || "Metric";

    const track = document.createElement("div");
    track.className = "bar-track";

    const fill = document.createElement("div");
    fill.className = "bar-fill";
    const score = Math.max(0, Math.min(100, Number(row.user || 0)));
    fill.style.width = `${score}%`;

    const value = document.createElement("span");
    value.textContent = String(score);

    track.appendChild(fill);
    wrap.append(label, track, value);
    el.radarBars.appendChild(wrap);
  });
}

async function loadHistory() {
  normalizeBaseUrl();
  if (!state.token) {
    setStatus(el.historyStatus, "Login first to load session history.", "error");
    return;
  }

  try {
    const resp = await timedFetch(
      "load_history",
      `${state.apiBase}/api/history`,
      { headers: authHeaders(false) },
      "history"
    );
    if (!resp.ok) throw new Error(`History failed (${resp.status})`);

    const rows = await resp.json();
    el.historyList.innerHTML = "";

    if (!rows.length) {
      setStatus(el.historyStatus, "No sessions found for this user.", "info");
      return;
    }

    rows.forEach((row) => {
      const item = document.createElement("button");
      item.className = "history-item";
      item.innerHTML = `<strong>${row.topic || "Unknown Topic"}</strong><span>${row.persona || "General"} | ${row.difficulty || "Medium"}</span><span>${row.session_id}</span>`;
      item.addEventListener("click", () => {
        state.sessionId = row.session_id;
        setStatus(el.historyStatus, `Selected session ${row.session_id}`, "ok");
        setStatus(el.setupStatus, `Using existing session: ${row.session_id}`, "ok");
      });
      el.historyList.appendChild(item);
    });

    setStatus(el.historyStatus, `Loaded ${rows.length} sessions. Click one to inspect/report.`, "ok");
  } catch (err) {
    setStatus(el.historyStatus, err.message, "error");
  }
}

async function healthCheck() {
  normalizeBaseUrl();
  try {
    const resp = await timedFetch("health_check", `${state.apiBase}/health`, {}, "health");
    if (!resp.ok) throw new Error(`Health check failed (${resp.status})`);
    const data = await resp.json();
    const llmHealthy = data?.llm?.healthy ? "healthy" : "unhealthy";
    const redisState = data?.redis?.connected ? "connected" : "disconnected";
    setStatus(el.perfStatus, `Health ok. LLM ${llmHealthy}, Redis ${redisState}.`, "ok");
  } catch (err) {
    setStatus(el.perfStatus, err.message, "error");
  }
}

function clearPerf() {
  state.perfEvents = [];
  renderPerf();
  setStatus(el.perfStatus, "Cleared perf data.", "ok");
}

function wireUi() {
  el.token.value = state.token;

  el.apiBase.addEventListener("change", normalizeBaseUrl);
  el.registerBtn.addEventListener("click", registerUser);
  el.loginBtn.addEventListener("click", login);
  el.loadOptionsBtn.addEventListener("click", loadConfigOptions);
  el.uploadResumeBtn.addEventListener("click", uploadResume);
  el.startInterviewBtn.addEventListener("click", startInterview);

  el.jdPreset.addEventListener("change", () => {
    const key = el.jdPreset.value;
    if (!key) return;
    if (key === "custom") {
      el.jobDescription.focus();
      return;
    }
    el.jobDescription.value = jdPresets[key] || "";
  });

  el.startCameraBtn.addEventListener("click", startCamera);
  el.connectWsBtn.addEventListener("click", connectSocket);
  el.startTrackingBtn.addEventListener("click", startTrackingSimulation);
  el.stopTrackingBtn.addEventListener("click", stopTrackingSimulation);
  el.recordBtn.addEventListener("click", startRecording);
  el.stopRecordBtn.addEventListener("click", stopRecording);

  el.refreshReportBtn.addEventListener("click", refreshReport);
  el.loadHistoryBtn.addEventListener("click", loadHistory);

  el.healthBtn.addEventListener("click", healthCheck);
  el.exportPerfBtn.addEventListener("click", exportPerf);
  el.clearPerfBtn.addEventListener("click", clearPerf);
}

wireUi();
loadConfigOptions();
if (state.token) {
  setStatus(el.authStatus, "Token loaded from local storage.", "ok");
}
