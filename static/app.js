const $ = (id) => document.getElementById(id);
let map, layer, lastCase, lastQueue = [];

const AUTH_NAMES = {
  spf: "Sender check",
  dkim: "Signature",
  dmarc: "Policy",
};

const CLASS_NAMES = {
  fraud: "payment scam",
  phishing: "phishing",
  impersonated: "fake identity",
  suspicious: "needs a second look",
  legitimate: "looks safe",
};

const INTENT_NAMES = {
  urgency: "rushed language",
  credential: "asks for a password",
  deception: "fake identity",
  payment: "asks for money",
  quishing: "odd QR / link",
  none_detected: "no scam language",
};

const PILLAR_NAMES = {
  auth: "Sender stamps",
  sender: "Who it claims to be",
  url: "Links",
  content: "Words in the email",
  infra: "Mail computers",
};

const IOC_TYPES = {
  ip: "computer address",
  email: "email",
  domain: "website name",
  url: "link",
  file: "attachment",
};

function className(c) {
  return CLASS_NAMES[c] || c || "unknown";
}

function verdictCopy(data) {
  const c = data.threat_class || data.label;
  const map = {
    fraud: {
      cls: "danger",
      title: "Danger: looks like a payment scam",
      sub: "Do not pay, wire money, or buy gift cards. Call the real person on a number you already have.",
    },
    phishing: {
      cls: "danger",
      title: "Danger: looks like a fake login",
      sub: "Do not click links or type your password.",
    },
    impersonated: {
      cls: "danger",
      title: "Danger: someone is pretending to be a trusted person",
      sub: "The name looks familiar, but the mailbox does not match. Treat it as fake.",
    },
    suspicious: {
      cls: "warn",
      title: "Caution: some warning signs",
      sub: "Check with the real person before you act.",
    },
    legitimate: {
      cls: "ok",
      title: "Looks safe",
      sub: "Sender stamps look real, and we did not find the usual scam language.",
    },
  };
  if (map[c]) return map[c];
  if ((data.score || 0) >= 65) return map.phishing;
  if ((data.score || 0) >= 40) return map.suspicious;
  return map.legitimate;
}

function stampLabel(val) {
  if (val === "pass") return "passed";
  if (val === "fail") return "failed";
  return "not found";
}

function pill(name, val) {
  const cls = val === "pass" ? "pass" : val === "fail" ? "fail" : "";
  return `<span class="pill ${cls}">${name}: ${stampLabel(val)}</span>`;
}

function setStatus(kind, text) {
  const el = $("status");
  if (!text) {
    el.className = "status hidden";
    el.textContent = "";
    return;
  }
  el.className = `status ${kind}`;
  el.textContent = text;
}

function mapCaption(hops) {
  const pts = (hops || []).filter((h) => h.country);
  if (!pts.length) return "No public computer locations in the headers (common for Gmail-to-Gmail). That is not a failure.";
  const countries = [...new Set(pts.map((h) => h.country))];
  return `Path of mail computers: ${countries.join(" → ")}. Red pin = first public computer we saw — not a person’s house.`;
}

function hopPlain(attr) {
  const g = attr.origin_geo || {};
  const place = [g.city, g.country].filter(Boolean).join(", ") || "unknown";
  return `First public computer we saw: ${attr.origin_ip || "n/a"} (${place}). Pattern: ${attr.likely_pattern || "unknown"}. This is a server, not a person.`;
}

function riskColor(score) {
  if (score >= 65) return "#ff5d6c";
  if (score >= 40) return "#ffb020";
  return "#3ee07a";
}

function setMode(mode) {
  document.querySelectorAll(".modes button").forEach((b) => b.classList.toggle("on", b.dataset.mode === mode));
  $("view-ingest").classList.toggle("hidden", mode !== "ingest");
  $("view-queue").classList.toggle("hidden", mode !== "queue");
  if (mode === "trace") return;
  if (mode === "ingest") setTimeout(() => map && map.invalidateSize(), 80);
}

function renderQueue(list) {
  lastQueue = list || [];
  const box = $("queueTable");
  if (!lastQueue.length) {
    box.innerHTML = `<p class="hint">No emails checked yet. Open Check email and try one.</p>`;
    return;
  }
  const head = `<div class="qrow head"><span>#</span><span>Score</span><span>Result</span><span>Subject</span><span>From</span><span>When</span></div>`;
  const rows = lastQueue
    .map((c) => {
      const when = (c.created_at || "").replace("T", " ").slice(0, 19);
      return `<button type="button" class="qrow" data-id="${c.id}"><span>#${c.id}</span><span>${c.score}</span><span>${className(c.label)}</span><span>${c.subject || "(no subject)"}</span><span>${c.from_addr || "—"}</span><span>${when}</span></button>`;
    })
    .join("");
  box.innerHTML = head + rows;
  box.querySelectorAll(".qrow[data-id]").forEach((b) => {
    b.onclick = () => {
      setMode("ingest");
      showCase(Number(b.dataset.id));
    };
  });
}

async function loadDashboard() {
  const d = await (await fetch("/api/dashboard")).json();
  $("kpiN").textContent = d.investigations || 0;
  $("kpiAvg").textContent = d.avg_score || 0;
  $("kpiHigh").textContent = d.high_risk || 0;
  $("kpiCamp").textContent = d.campaigns || 0;
  $("kpiSeal").textContent = d.evidence_sealed || 0;
}

async function loadPresets() {
  const box = $("presets");
  try {
    const list = await (await fetch("/api/samples")).json();
    box.innerHTML = list
      .map(
        (s) =>
          `<button type="button" class="sample ${s.tone || "neutral"}" data-id="${s.id}"><span class="expect">${s.expect}</span>${s.title}<span class="blurb">${s.blurb || s.name}</span></button>`
      )
      .join("");
    box.querySelectorAll("button").forEach((b) => {
      b.onclick = () => run({ sample_id: b.dataset.id });
    });
  } catch (e) {
    box.innerHTML = `<p class="hint">Could not load practice emails.</p>`;
  }
}

async function loadCases() {
  await loadDashboard();
  const list = await (await fetch("/api/cases")).json();
  renderQueue(list);
  const box = $("cases");
  box.innerHTML = "";
  if (!list.length) {
    box.innerHTML = `<p class="hint">Checks you run appear here.</p>`;
  } else {
    list.slice(0, 10).forEach((c) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = `#${c.id} [${c.score}] ${c.subject || "(no subject)"}`;
      b.onclick = () => showCase(c.id);
      box.appendChild(b);
    });
  }
  try {
    const camps = await (await fetch("/api/campaigns")).json();
    const cb = $("campaigns");
    cb.innerHTML = "";
    if (!camps.length) {
      cb.innerHTML = `<p class="hint">No repeat senders yet.</p>`;
    } else {
      camps.slice(0, 8).forEach((g) => {
        const p = document.createElement("p");
        p.className = "hint";
        const classes = Object.entries(g.classes || {})
          .map(([k, n]) => `${k}×${n}`)
          .join(", ");
        p.textContent = `${g.domain} — ${g.count} checks · highest ${g.max_score}/100 (${classes})`;
        cb.appendChild(p);
      });
    }
  } catch (e) {
    /* optional */
  }
  return list;
}

async function pingHealth() {
  const el = $("health");
  try {
    const h = await (await fetch("/api/health")).json();
    if (h.ok) {
      el.className = "kpi health on";
      el.textContent = "Checker is on";
      return;
    }
  } catch (e) {
    /* down */
  }
  el.className = "kpi health off";
  el.textContent = "Checker is off — start the server";
}

function drawMap(hops) {
  if (typeof L === "undefined") return;
  if (!map) {
    map = L.map("map", { worldCopyJump: true }).setView([20, 20], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 8,
    }).addTo(map);
  }
  if (layer) layer.remove();
  layer = L.layerGroup().addTo(map);
  const pts = (hops || []).filter((h) => h.lat != null && h.lon != null);
  const latlngs = pts.map((h) => [h.lat, h.lon]);
  pts.forEach((h) => {
    const color = h.role === "origin" ? "#ff5d6c" : "#3ee0c9";
    L.circleMarker([h.lat, h.lon], { radius: 8, color, fillOpacity: 0.85 })
      .addTo(layer)
      .bindPopup(
        `<b>${h.role === "origin" ? "First public computer" : "Mail computer"}</b> ${h.ip}<br>${h.city || ""} ${h.country}<br>${h.isp || ""}`
      );
  });
  if (latlngs.length >= 2) L.polyline(latlngs, { color: "#3ee0c9", weight: 2 }).addTo(layer);
  if (latlngs.length) map.fitBounds(latlngs, { padding: [30, 30], maxZoom: 5 });
  setTimeout(() => map && map.invalidateSize(), 220);
}

function drawGraph(g) {
  const box = $("graph");
  const detail = $("graphDetail");
  $("graphNote").textContent = (g && g.note) || "";
  if (!g || !(g.nodes || []).length) {
    box.innerHTML = `<p class="hint">Nothing to connect yet.</p>`;
    return;
  }
  box.innerHTML = (g.nodes || [])
    .map((n) => {
      const kinds = { ip: "computer", email: "email", domain: "website", url: "link", file: "file", mailbox: "mailbox" };
      return `<button type="button" class="gnode" data-id="${n.id}"><b>${kinds[n.kind] || n.kind}</b>${n.label}</button>`;
    })
    .join("");
  box.querySelectorAll(".gnode").forEach((el) => {
    el.onclick = () => {
      box.querySelectorAll(".gnode").forEach((x) => x.classList.remove("on"));
      el.classList.add("on");
      const n = g.nodes.find((x) => x.id === el.dataset.id);
      const links = (g.edges || []).filter((e) => e.source === n.id || e.target === n.id);
      const kinds = { ip: "computer", email: "email", domain: "website", url: "link", file: "file", mailbox: "mailbox" };
      const kind = kinds[n.kind] || n.kind;
      detail.textContent = `${kind}: ${n.label} — ${n.detail || ""} · ${links.length} link(s)`;
    };
  });
}

function showTab(name) {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("on", t.id === "tab-" + name));
  if (name === "trace") setTimeout(() => map && map.invalidateSize(), 80);
}

function renderIdentity(id) {
  const rows = (id && id.rows) || [];
  if (!rows.length) {
    $("identity").innerHTML = `<p class="hint">Check an email to see if the From name matches the real mailbox.</p>`;
    return;
  }
  $("identity").innerHTML = rows
    .map((r) => {
      const stClass = r.status === "n/a" ? "na" : r.status;
      const label = r.status === "same_org" ? "MATCHES" : r.status === "mismatch" ? "DOESN'T MATCH" : "NOT GIVEN";
      return `<div class="id-row"><div><div class="lab">${r.field}</div></div><div class="val">${r.value}</div><div class="st ${stClass}">${label}</div><div class="hint">${r.note}</div></div>`;
    })
    .join("");
}

function renderIntel(intel) {
  const i = intel || {};
  $("intelNote").textContent = i.note || "This is only what MailTrace has seen on this computer, not a global blacklist.";
  const cells = [
    ["Sender", i.sender],
    ["Website name", i.domain],
    ["First computer", i.origin_ip],
    ["Seen before", { seen_before: (i.prior_sightings || 0) > 0, count: i.prior_sightings, extra: i.correlated_campaign }],
  ];
  $("sights").innerHTML = cells
    .map(([lab, x]) => {
      const seen = x && x.seen_before;
      const n = x && x.count != null ? x.count : "—";
      const extra = x && x.extra ? `<div class="hint">${x.extra}</div>` : lab === "Website name" ? `<div class="hint">grouped by sender</div>` : "";
      return `<div class="sight ${seen ? "yes" : ""}"><span>${lab}</span><b>${seen ? "Seen before" : lab === "Seen before" ? n : "New"}</b>${lab === "Seen before" ? "" : `<div class="hint">${n} earlier</div>`}${extra}</div>`;
    })
    .join("");
  const log = i.incident_log || [];
  $("corrLog").innerHTML = log.length
    ? log
        .map(
          (r) =>
            `<div class="crow"><span>#${r.id}</span><span>${r.subject}</span><span>${r.score} ${r.label || ""}</span><span>${r.origin_ip}</span></div>`
        )
        .join("")
    : `<p class="hint">No earlier match for this sender, website, or computer on this device.</p>`;
}

function revealResult() {
  const grid = document.querySelector(".grid");
  if (grid) grid.classList.add("has-result");
  if (window.matchMedia("(max-width: 980px)").matches) {
    $("result").scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function render(data) {
  lastCase = data;
  $("empty").classList.add("hidden");
  $("result").classList.remove("hidden");
  const v = verdictCopy(data);
  const box = $("verdict");
  box.className = `verdict ${v.cls}`;
  box.innerHTML = `${v.title}<small>${v.sub}</small>`;
  $("subject").textContent = data.subject || "(no subject)";
  $("from").textContent = "From: " + (data.from_addr || "");
  $("scoreNum").textContent = data.score;
  const color = riskColor(data.score || 0);
  const donut = $("donut");
  donut.style.setProperty("--p", String(data.score || 0));
  donut.style.setProperty("--c", color);
  const a = data.auth || {};
  $("authMatrix").innerHTML = ["spf", "dkim", "dmarc"]
    .map((k) => {
      const val = a[k] || "none";
      const cls = val === "pass" ? "pass" : val === "fail" ? "fail" : "";
      return `<div class="auth-cell ${cls}"><b>${AUTH_NAMES[k]}</b>${stampLabel(val)}</div>`;
    })
    .join("");
  $("auth").innerHTML =
    pill(AUTH_NAMES.spf, a.spf) + pill(AUTH_NAMES.dkim, a.dkim) + pill(AUTH_NAMES.dmarc, a.dmarc);
  $("guidance").innerHTML = `<b>What you should do</b>${data.guidance || "Check an email to get advice."}`;
  $("mapCap").textContent = mapCaption(data.geo_hops);
  const tclass = data.threat_class || data.label;
  const exp = data.explain || {};
  $("classLine").textContent = `Result: ${className(tclass)}. How sure we are about the first computer: ${(data.attribution || {}).confidence || "n/a"}.`;
  const sev = (data.severity || exp.severity || "").toLowerCase();
  const sevWord = { critical: "very high", high: "high", medium: "medium", low: "low" }[sev] || sev || "n/a";
  $("sev").textContent = `How serious: ${sevWord} · check #${data.id || "—"}`;
  $("explainNote").textContent =
    exp.note || "Each bar is how much that warning added to the score. These are simple rules, not a chatbot.";
  const hitl = $("hitl");
  if (exp.hitl_review) {
    hitl.className = "status warn";
    hitl.textContent = "A person should look at this: " + (exp.hitl_reason || "the score is in the middle.");
  } else {
    hitl.className = "status hidden";
    hitl.textContent = "";
  }
  $("intents").innerHTML = (exp.intents || [])
    .map((x) => `<span class="pill">${INTENT_NAMES[x] || x}</span>`)
    .join(" ");
  const counts = (data.findings && data.findings.counts) || {};
  $("findCounts").innerHTML = `<span class="high">${counts.high || 0} danger</span><span class="warning">${counts.warning || 0} caution</span><span>${counts.info || 0} notes</span>`;
  const sevTag = { high: "danger", warning: "caution", info: "note" };
  $("findList").innerHTML = ((data.findings && data.findings.items) || [])
    .map(
      (f) =>
        `<div class="find-row ${f.severity}"><span class="sevtag">${sevTag[f.severity] || f.severity}</span><div><b>${f.title}</b><div class="hint">${f.detail}</div></div></div>`
    )
    .join("") || `<p class="hint">No extra notes on this older check — run Check this email again.</p>`;
  const phases = data.phases || [];
  $("phaseCap").textContent = phases.length
    ? `${phases.length} checks completed in ${data.pipeline_s || "?"}s`
    : "Check an email to see the step-by-step result.";
  $("phases").innerHTML = phases
    .map((p) => {
      const ok = p.status !== "FLAGGED";
      return `<li><span class="stamp ${p.status}">${ok ? "OK" : "Warning"}</span><div><div class="pname">${p.name}</div><p class="pdet">${p.detail}</p></div><span class="ptime">${p.elapsed_s}s</span></li>`;
    })
    .join("");
  renderIdentity(data.identity);
  $("relay").innerHTML = (data.hops || [])
    .map((h, i) => `<li>Stop ${i + 1} — ${(h.public_ips || []).join(", ") || "no public address"} · ${(h.header || "").slice(0, 180)}</li>`)
    .join("") || "<li>No path found in the headers.</li>";
  $("pillars").innerHTML = (exp.pillars || [])
    .map((c) => {
      const label = PILLAR_NAMES[c.id] || PILLAR_NAMES[c.label] || c.label;
      return `<div class="rowbar"><span>${label}</span><span class="track"><i style="width:${Math.min(100, c.share)}%"></i></span><span>+${c.points}</span></div>`;
    })
    .join("") || `<p class="hint">No split on this older check — run Check this email again.</p>`;
  $("contrib").innerHTML = (exp.contributions || [])
    .map(
      (c) =>
        `<div class="rowbar"><span>${c.detail || c.code}</span><span class="track"><i style="width:${c.share}%"></i></span><span>+${c.points}</span></div>`
    )
    .join("") || `<p class="hint">No warning signs added to the score.</p>`;
  $("timeline").innerHTML = (data.geo_hops || [])
    .map((h, i) => {
      const place = [h.city, h.country].filter(Boolean).join(", ") || "place unknown";
      return `<li>${h.role === "origin" ? "First public computer" : "Next computer " + (i + 1)} — ${h.ip || "?"} · ${place} · ${h.isp || ""}</li>`;
    })
    .join("") || "<li>No public computers in the headers (common for Gmail-to-Gmail).</li>";
  $("attr").textContent = hopPlain(data.attribution || {});
  const anoms = data.header_intel?.anomalies || [];
  $("anoms").innerHTML = anoms.length ? anoms.map((x) => `<li>${x.detail}</li>`).join("") : "<li>No odd From / Reply-To mismatch.</li>";
  const explorer = data.iocs?.explorer || [];
  $("iocTable").innerHTML = explorer.length
    ? explorer
        .map(
          (i) =>
            `<div class="ioc-row"><span class="pill">${IOC_TYPES[i.type] || i.type}</span><code>${i.defanged}</code><span>${i.confidence}</span><span>${i.reputation}</span><button type="button" class="ghost copy" data-v="${(i.defanged || "").replace(/"/g, "")}">Copy</button></div>`
        )
        .join("")
    : `<p class="hint">No warning clues yet — check an email first.</p>`;
  $("iocTable").querySelectorAll(".copy").forEach((b) => {
    b.onclick = () => navigator.clipboard.writeText(b.dataset.v);
  });
  renderIntel(data.intel);
  const di = data.domain_intel || {};
  $("domIntel").textContent = di.domain
    ? `Website ${di.domain}: ${(di.notes || []).join(" ")} Mail boxes: ${(di.mx_records || []).join(", ") || "none"}`
    : "No From website name.";
  const ev = data.evidence || data.custody || {};
  $("custody").textContent = ev.sha256
    ? `Fingerprint ${ev.sha256} (${ev.byte_length || "?"} bytes) · ${ev.hashed_at || ""}`
    : "No fingerprint on this older check — run Check this email again.";
  $("vaultNote").textContent = ev.vault || ev.note || "Saved on this computer only. Not a courtroom stamp.";
  $("playbook").innerHTML = (data.playbook || []).map((s) => `<li>${s}</li>`).join("") || "<li>Check an email to get next steps.</li>";
  $("reasons").innerHTML = (data.reasons || [])
    .map((r) => `<li>${r.detail} <span class="hint">(+${r.points})</span></li>`)
    .join("") || "<li>No warning signs.</li>";
  drawGraph(data.graph || { nodes: [], edges: [] });
  $("nlp").textContent = JSON.stringify(
    {
      threat_class: tclass,
      severity: data.severity,
      score: data.score,
      identity: data.identity,
      phases: data.phases,
      intel: data.intel,
      findings: data.findings,
      graph: data.graph,
      iocs: data.iocs,
      evidence: data.evidence,
      explain: data.explain,
      attribution: data.attribution,
    },
    null,
    2
  );
  $("pdf").href = `/api/cases/${data.id}/report.pdf`;
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const json = $("json");
  if (json._url) URL.revokeObjectURL(json._url);
  json._url = URL.createObjectURL(blob);
  json.href = json._url;
  json.download = `mailtrace-case-${data.id || "latest"}.json`;
  drawMap(data.geo_hops || []);
  showTab("timeline");
}

async function run(payload) {
  setStatus("busy", "Checking this email…");
  const fd = new FormData();
  if (payload.raw) fd.set("raw", payload.raw);
  if (payload.file) fd.set("file", payload.file);
  if (payload.sample_id) fd.set("sample_id", payload.sample_id);
  try {
    const res = await fetch("/api/analyze", { method: "POST", body: fd });
    const data = await res.json();
    if (data.error) {
      setStatus("err", data.error === "empty email" ? "Paste the full original email or upload a .eml file." : data.error);
      return;
    }
    setStatus("", "");
    render(data);
    loadCases();
    revealResult();
  } catch (e) {
    setStatus("err", "The checker is off. Keep the MailTrace window open, then try again.");
  }
}

async function showCase(id) {
  setStatus("busy", "Opening that check…");
  try {
    const data = await (await fetch(`/api/cases/${id}`)).json();
    if (data.error) {
      setStatus("err", "That check was not found.");
      return;
    }
    setStatus("", "");
    render(data);
    revealResult();
  } catch (e) {
    setStatus("err", "Could not open that check.");
  }
}

function syncFileUi() {
  const f = $("file").files[0];
  const paste = ($("raw").value || "").trim();
  $("fileChip").classList.toggle("hidden", !f);
  if (f) {
    $("fileChipName").textContent = f.name;
    $("fileName").textContent = `Using ${f.name}`;
  } else if (paste) {
    $("fileName").textContent = "Will check the pasted email.";
  } else {
    $("fileName").textContent = "";
  }
}

$("run").onclick = () => {
  const f = $("file").files[0];
  const paste = ($("raw").value || "").trim();
  if (f) run({ file: f });
  else run({ raw: paste });
};
$("clearFile").onclick = () => {
  $("file").value = "";
  syncFileUi();
};
$("file").addEventListener("change", syncFileUi);
$("raw").addEventListener("input", syncFileUi);
$("tabs").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (b && b.dataset.tab) showTab(b.dataset.tab);
});
$("modes").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (b && b.dataset.mode) setMode(b.dataset.mode);
});

const drop = $("drop");
["dragenter", "dragover"].forEach((ev) => {
  drop.addEventListener(ev, (e) => {
    e.preventDefault();
    drop.classList.add("drag");
  });
});
["dragleave", "drop"].forEach((ev) => {
  drop.addEventListener(ev, (e) => {
    e.preventDefault();
    drop.classList.remove("drag");
  });
});
drop.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  if (!f) return;
  const dt = new DataTransfer();
  dt.items.add(f);
  $("file").files = dt.files;
  syncFileUi();
});

function showLanding() {
  $("landing").classList.remove("hidden");
  $("work").classList.add("hidden");
  if (location.hash === "#console") history.replaceState(null, "", location.pathname);
}

function showWork(tab) {
  $("landing").classList.add("hidden");
  $("work").classList.remove("hidden");
  setMode("ingest");
  if (tab) showTab(tab);
  setTimeout(() => map && map.invalidateSize(), 120);
}

$("landEnter").onclick = () => showWork();
$("landSkip").onclick = () => showWork();
$("backLanding").onclick = () => showLanding();
$("landLab").onclick = () => {
  showWork("timeline");
  run({ sample_id: "02_phishing_invoice" });
};
$("landSafe").onclick = () => {
  showWork("timeline");
  run({ sample_id: "01_legitimate_college" });
};
document.querySelectorAll(".land-feat").forEach((b) => {
  b.onclick = () => showWork(b.dataset.goto);
});

(async function boot() {
  pingHealth();
  setInterval(pingHealth, 8000);
  if (location.hash === "#console") showWork();
  try {
    await loadPresets();
    await loadCases();
  } catch (e) {
    setStatus("err", "Could not reach MailTrace. Start the server, then refresh.");
  }
})();
