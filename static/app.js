const $ = (id) => document.getElementById(id);
let map, layer, lastCase, lastQueue = [];

function verdictCopy(data) {
  const c = data.threat_class || data.label;
  const map = {
    fraud: {
      cls: "danger",
      title: "Fraud — payment / invoice diversion",
      sub: "Do not pay, wire, or buy gift cards. Confirm on a known channel.",
    },
    phishing: {
      cls: "danger",
      title: "Phishing — credential or lookalike lure",
      sub: "Do not click links or enter passwords.",
    },
    impersonated: {
      cls: "danger",
      title: "Impersonated — BEC-style identity mismatch",
      sub: "Trusted name, unmatched mailbox. Treat as executive / staff impersonation.",
    },
    suspicious: {
      cls: "warn",
      title: "Suspicious — mixed indicators",
      sub: "Verify before you act. Human review recommended.",
    },
    legitimate: {
      cls: "ok",
      title: "Legitimate — no strong threat class fired",
      sub: "Stamps and content did not match fraud / phishing / impersonation rules.",
    },
  };
  if (map[c]) return map[c];
  if ((data.score || 0) >= 65) return map.phishing;
  if ((data.score || 0) >= 40) return map.suspicious;
  return map.legitimate;
}

function stampLabel(val) {
  if (val === "pass") return "pass";
  if (val === "fail") return "fail";
  return val || "none";
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
  if (!pts.length) return "No public server locations in headers (common for Gmail-to-Gmail).";
  const countries = [...new Set(pts.map((h) => h.country))];
  return `Mail-server path: ${countries.join(" → ")}. Red pin = first public hop — a computer, not a house.`;
}

function hopPlain(attr) {
  const g = attr.origin_geo || {};
  const place = [g.city, g.country].filter(Boolean).join(", ") || "unknown";
  return `First public server: ${attr.origin_ip || "n/a"} (${place}). Pattern: ${attr.likely_pattern || "unknown"}. Infrastructure only.`;
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
    box.innerHTML = `<p class="hint">No investigations yet. Analyze an email on Ingest & Scanner.</p>`;
    return;
  }
  const head = `<div class="qrow head"><span>#</span><span>Risk</span><span>Class</span><span>Subject</span><span>From</span><span>When</span></div>`;
  const rows = lastQueue
    .map((c) => {
      const when = (c.created_at || "").replace("T", " ").slice(0, 19);
      return `<button type="button" class="qrow" data-id="${c.id}"><span>#${c.id}</span><span>${c.score}</span><span>${c.label || "—"}</span><span>${c.subject || "(no subject)"}</span><span>${c.from_addr || "—"}</span><span>${when}</span></button>`;
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
          `<button type="button" class="sample ${s.tone || "neutral"}" data-id="${s.id}"><span class="expect">${s.expect}</span>${s.title}<span class="blurb">LAB · ${s.name}</span></button>`
      )
      .join("");
    box.querySelectorAll("button").forEach((b) => {
      b.onclick = () => run({ sample_id: b.dataset.id });
    });
  } catch (e) {
    box.innerHTML = `<p class="hint">Could not load lab presets.</p>`;
  }
}

async function loadCases() {
  await loadDashboard();
  const list = await (await fetch("/api/cases")).json();
  renderQueue(list);
  const box = $("cases");
  box.innerHTML = "";
  if (!list.length) {
    box.innerHTML = `<p class="hint">Cases you run appear here.</p>`;
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
      cb.innerHTML = `<p class="hint">No grouped domains yet.</p>`;
    } else {
      camps.slice(0, 8).forEach((g) => {
        const p = document.createElement("p");
        p.className = "hint";
        const classes = Object.entries(g.classes || {})
          .map(([k, n]) => `${k}×${n}`)
          .join(", ");
        p.textContent = `${g.domain} — ${g.count} cases · max ${g.max_score}/100 (${classes})`;
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
      el.textContent = "Backend online · heuristics";
      return;
    }
  } catch (e) {
    /* down */
  }
  el.className = "kpi health off";
  el.textContent = "Backend offline — start uvicorn";
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
        `<b>${h.role === "origin" ? "First public hop" : "Mail server"}</b> ${h.ip}<br>${h.city || ""} ${h.country}<br>${h.isp || ""}`
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
    box.innerHTML = `<p class="hint">No artefacts to graph.</p>`;
    return;
  }
  box.innerHTML = (g.nodes || [])
    .map((n) => `<button type="button" class="gnode" data-id="${n.id}"><b>${n.kind}</b>${n.label}</button>`)
    .join("");
  box.querySelectorAll(".gnode").forEach((el) => {
    el.onclick = () => {
      box.querySelectorAll(".gnode").forEach((x) => x.classList.remove("on"));
      el.classList.add("on");
      const n = g.nodes.find((x) => x.id === el.dataset.id);
      const links = (g.edges || []).filter((e) => e.source === n.id || e.target === n.id);
      detail.textContent = `${n.kind}: ${n.label} — ${n.detail || ""} · ${links.length} link(s): ${links.map((e) => e.rel).join(", ") || "none"}`;
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
    $("identity").innerHTML = `<p class="hint">Re-analyze to build identity alignment.</p>`;
    return;
  }
  $("identity").innerHTML = rows
    .map((r) => {
      const stClass = r.status === "n/a" ? "na" : r.status;
      const label = r.status === "same_org" ? "SAME ORG DOMAIN" : r.status === "mismatch" ? "MISMATCH" : "N/A";
      return `<div class="id-row"><div><div class="lab">${r.field}</div></div><div class="val">${r.value}</div><div class="st ${stClass}">${label}</div><div class="hint">${r.note}</div></div>`;
    })
    .join("");
}

function renderIntel(intel) {
  const i = intel || {};
  $("intelNote").textContent = i.note || "Local sightings from this MailTrace case store.";
  const cells = [
    ["Sender", i.sender],
    ["Domain", i.domain],
    ["Origin IP", i.origin_ip],
    ["Prior sightings", { seen_before: (i.prior_sightings || 0) > 0, count: i.prior_sightings, extra: i.correlated_campaign }],
  ];
  $("sights").innerHTML = cells
    .map(([lab, x]) => {
      const seen = x && x.seen_before;
      const n = x && x.count != null ? x.count : "—";
      const extra = x && x.extra ? `<div class="hint">${x.extra}</div>` : lab === "Domain" ? `<div class="hint">cluster</div>` : "";
      return `<div class="sight ${seen ? "yes" : ""}"><span>${lab}</span><b>${seen ? "Seen before" : lab === "Prior sightings" ? n : "New"}</b>${lab === "Prior sightings" ? "" : `<div class="hint">${n} prior</div>`}${extra}</div>`;
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
    : `<p class="hint">No prior matches for this sender / domain / origin IP on this instance.</p>`;
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
      return `<div class="auth-cell ${cls}"><b>${k}</b>${stampLabel(val)}</div>`;
    })
    .join("");
  $("auth").innerHTML = pill("SPF", a.spf) + pill("DKIM", a.dkim) + pill("DMARC", a.dmarc);
  $("guidance").innerHTML = `<b>SOC analyst guidance</b>${data.guidance || "Re-analyze for guidance."}`;
  $("mapCap").textContent = mapCaption(data.geo_hops);
  const tclass = data.threat_class || data.label;
  const exp = data.explain || {};
  $("classLine").textContent = `Threat class: ${tclass} · attribution confidence: ${(data.attribution || {}).confidence || "n/a"}`;
  $("sev").textContent = `Severity ${(data.severity || exp.severity || "n/a").toUpperCase()} · case #${data.id || "—"}`;
  $("explainNote").textContent = exp.note || "";
  const hitl = $("hitl");
  if (exp.hitl_review) {
    hitl.className = "status warn";
    hitl.textContent = "Human review: " + (exp.hitl_reason || "Uncertainty band.");
  } else {
    hitl.className = "status hidden";
    hitl.textContent = "";
  }
  $("intents").innerHTML = (exp.intents || []).map((x) => `<span class="pill">${x}</span>`).join(" ");
  const counts = (data.findings && data.findings.counts) || {};
  $("findCounts").innerHTML = `<span class="high">${counts.high || 0} high</span><span class="warning">${counts.warning || 0} warning</span><span>${counts.info || 0} info</span>`;
  $("findList").innerHTML = ((data.findings && data.findings.items) || [])
    .map(
      (f) =>
        `<div class="find-row ${f.severity}"><span class="sevtag">${(f.severity || "").toUpperCase()}</span><div><b>${f.title}</b><div class="hint">${f.detail}</div></div></div>`
    )
    .join("") || `<p class="hint">No detailed findings on this older case — re-analyze.</p>`;
  const phases = data.phases || [];
  $("phaseCap").textContent = phases.length
    ? `${phases.length} completed phases · pipeline ${data.pipeline_s || "?"}s (wall-clock of this run)`
    : "Re-analyze to stamp a seven-phase timeline.";
  $("phases").innerHTML = phases
    .map(
      (p) =>
        `<li><span class="stamp ${p.status}">${p.status}</span><div><div class="pname">${p.name}</div><p class="pdet">${p.detail}</p></div><span class="ptime">${p.elapsed_s}s</span></li>`
    )
    .join("");
  renderIdentity(data.identity);
  $("relay").innerHTML = (data.hops || [])
    .map((h, i) => `<li>MTA ${i + 1} — ${(h.public_ips || []).join(", ") || "no public IP"} · ${(h.header || "").slice(0, 180)}</li>`)
    .join("") || "<li>No Received hops parsed.</li>";
  $("pillars").innerHTML = (exp.pillars || [])
    .map(
      (c) =>
        `<div class="rowbar"><span>${c.label}</span><span class="track"><i style="width:${Math.min(100, c.share)}%"></i></span><span>+${c.points}</span></div>`
    )
    .join("") || `<p class="hint">No pillar split on this older case — re-analyze.</p>`;
  $("contrib").innerHTML = (exp.contributions || [])
    .map(
      (c) =>
        `<div class="rowbar"><span>${c.code}</span><span class="track"><i style="width:${c.share}%"></i></span><span>+${c.points}</span></div>`
    )
    .join("") || `<p class="hint">No positive risk features.</p>`;
  $("timeline").innerHTML = (data.geo_hops || [])
    .map((h, i) => {
      const place = [h.city, h.country].filter(Boolean).join(", ") || "no geo";
      return `<li>${h.role === "origin" ? "Origin hop" : "Relay " + (i + 1)} — ${h.ip || "?"} · ${place} · ${h.isp || ""}</li>`;
    })
    .join("") || "<li>No public hops (common for Gmail-to-Gmail).</li>";
  $("attr").textContent = hopPlain(data.attribution || {});
  const anoms = data.header_intel?.anomalies || [];
  $("anoms").innerHTML = anoms.length ? anoms.map((x) => `<li>${x.detail}</li>`).join("") : "<li>No header-domain mismatches flagged.</li>";
  const explorer = data.iocs?.explorer || [];
  $("iocTable").innerHTML = explorer.length
    ? explorer
        .map(
          (i) =>
            `<div class="ioc-row"><span class="pill">${i.type}</span><code>${i.defanged}</code><span>${i.confidence}</span><span>${i.reputation}</span><button type="button" class="ghost copy" data-v="${(i.defanged || "").replace(/"/g, "")}">Copy</button></div>`
        )
        .join("")
    : `<p class="hint">No IOCs — re-analyze to build the explorer.</p>`;
  $("iocTable").querySelectorAll(".copy").forEach((b) => {
    b.onclick = () => navigator.clipboard.writeText(b.dataset.v);
  });
  renderIntel(data.intel);
  const di = data.domain_intel || {};
  $("domIntel").textContent = di.domain
    ? `DNS ${di.domain}: ${(di.notes || []).join(" ")} MX=${(di.mx_records || []).join(", ") || "none"}`
    : "No From domain.";
  const ev = data.evidence || data.custody || {};
  $("custody").textContent = ev.sha256
    ? `${ev.algorithm || "SHA-256"} ${ev.sha256} (${ev.byte_length || "?"} bytes) · ${ev.hashed_at || ""}`
    : "Hash not stored on this older case — run Analyze again.";
  $("vaultNote").textContent = ev.vault || ev.note || "Local prototype seal, not a blockchain stamp.";
  $("playbook").innerHTML = (data.playbook || []).map((s) => `<li>${s}</li>`).join("") || "<li>Re-analyze for a playbook.</li>";
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
  setStatus("busy", "Running forensic pipeline…");
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
  } catch (e) {
    setStatus("err", "Server is off. Keep the MailTrace window running, then retry.");
  }
}

async function showCase(id) {
  setStatus("busy", "Opening case…");
  try {
    const data = await (await fetch(`/api/cases/${id}`)).json();
    if (data.error) {
      setStatus("err", "Case not found.");
      return;
    }
    setStatus("", "");
    render(data);
  } catch (e) {
    setStatus("err", "Could not load that case.");
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
    $("fileName").textContent = "Will analyze pasted text.";
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
