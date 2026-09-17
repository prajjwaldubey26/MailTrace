const $ = (id) => document.getElementById(id);
let map, layer;

function verdictCopy(data) {
  const c = data.threat_class || data.label;
  const map = {
    fraud: {
      cls: "danger",
      title: "Fraud — payment / invoice diversion language",
      sub: "Do not pay, wire, or buy gift cards. Confirm on a known channel.",
    },
    phishing: {
      cls: "danger",
      title: "Phishing — credential or lookalike lure",
      sub: "Do not click links or enter passwords. This is a phishing-class verdict.",
    },
    impersonated: {
      cls: "danger",
      title: "Impersonated — trusted name, unmatched mailbox",
      sub: "Display name or role does not match the From domain. Treat as BEC-style impersonation.",
    },
    suspicious: {
      cls: "warn",
      title: "Suspicious — mixed or weak indicators",
      sub: "Some header, DNS, or content warnings. Verify before you act.",
    },
    legitimate: {
      cls: "ok",
      title: "Legitimate — no strong threat class fired",
      sub: "Stamps and content did not match the fraud / phishing / impersonation rules.",
    },
  };
  if (map[c]) return map[c];
  if ((data.score || 0) >= 65) return map.phishing;
  if ((data.score || 0) >= 40) return map.suspicious;
  return map.legitimate;
}

function stampLabel(val) {
  if (val === "pass") return "real";
  if (val === "fail") return "fake / failed";
  return val || "not present";
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
  if (!pts.length) return "No public server locations found in the headers (common for Gmail-to-Gmail).";
  const countries = [...new Set(pts.map((h) => h.country))];
  return `Path of mail servers: ${countries.join(" → ")}. Red pin = first public hop we could see — a computer, not a person’s house.`;
}

function hopPlain(attr) {
  const g = attr.origin_geo || {};
  const place = [g.city, g.country].filter(Boolean).join(", ") || "unknown";
  return (
    `First public server we saw: ${attr.origin_ip || "n/a"} (${place}). ` +
    `Pattern: ${attr.likely_pattern || "unknown"}. ` +
    `This is infrastructure, not the identity of a human sender.`
  );
}

async function loadCases() {
  const list = await (await fetch("/api/cases")).json();
  const box = $("cases");
  box.innerHTML = "";
  if (!list.length) {
    box.innerHTML = `<p class="hint">Checks you run will appear here.</p>`;
  } else {
    list.slice(0, 12).forEach((c) => {
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
    if (cb) {
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
          p.textContent = `${g.domain} — ${g.count} check(s), max ${g.max_score}/100 (${classes})`;
          cb.appendChild(p);
        });
      }
    }
  } catch (e) {
    /* campaigns endpoint optional */
  }
  return list;
}

function drawMap(hops) {
  if (typeof L === "undefined") {
    $("mapCap").textContent =
      ($("mapCap").textContent || "") + " (Map library did not load — the verdict still works.)";
    return;
  }
  if (!map) {
    map = L.map("map", { worldCopyJump: true }).setView([20, 20], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 8,
    }).addTo(map);
  }
  if (layer) layer.remove();
  layer = L.layerGroup().addTo(map);
  const pts = hops.filter((h) => h.lat != null && h.lon != null);
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
  setTimeout(() => map.invalidateSize(), 200);
}

function render(data) {
  $("empty").classList.add("hidden");
  $("result").classList.remove("hidden");
  const v = verdictCopy(data);
  const box = $("verdict");
  box.className = `verdict ${v.cls}`;
  box.innerHTML = `${v.title}<small>${v.sub}</small>`;
  $("subject").textContent = data.subject || "(no subject)";
  $("from").textContent = "From: " + (data.from_addr || "");
  $("scoreNum").textContent = data.score;
  $("bar").style.width = `${data.score}%`;
  $("bar").style.background = data.score >= 65 ? "#ff5d6c" : data.score >= 40 ? "#ffb020" : "#3ee07a";
  const a = data.auth || {};
  $("authMatrix").innerHTML = ["spf", "dkim", "dmarc"]
    .map((k) => {
      const val = a[k] || "none";
      const cls = val === "pass" ? "pass" : val === "fail" ? "fail" : "";
      return `<div class="auth-cell ${cls}"><b>${k}</b>${stampLabel(val)}</div>`;
    })
    .join("");
  $("auth").innerHTML =
    `<span class="pill">Mail stamps</span>` +
    pill("SPF", a.spf) +
    pill("DKIM", a.dkim) +
    pill("DMARC", a.dmarc);
  $("mapCap").textContent = mapCaption(data.geo_hops);
  const tclass = data.threat_class || data.label;
  $("classLine").textContent = `Threat class: ${tclass} (legitimate / suspicious / impersonated / phishing / fraud)`;
  const exp = data.explain || {};
  $("explainNote").textContent = exp.note || "";
  const hitl = $("hitl");
  if (exp.hitl_review) {
    hitl.className = "status warn";
    hitl.textContent = "Human review: " + (exp.hitl_reason || "Uncertainty band — confirm before acting.");
  } else {
    hitl.className = "status hidden";
    hitl.textContent = "";
  }
  $("intents").innerHTML = (exp.intents || [])
    .map((x) => `<span class="pill">${x}</span>`)
    .join(" ");
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
    .join("") || "<li>No public hops to list (common for Gmail-to-Gmail).</li>";
  const ioc = data.iocs || {};
  const iocLines = []
    .concat((ioc.emails || []).map((x) => "email: " + x))
    .concat((ioc.domains || []).map((x) => "domain: " + x))
    .concat((ioc.ips || []).map((x) => "ip: " + x))
    .concat((ioc.urls || []).slice(0, 8).map((x) => "url: " + x))
    .concat((ioc.files || []).map((x) => "file: " + x));
  $("iocs").innerHTML = iocLines.length
    ? iocLines.map((x) => `<li>${x}</li>`).join("")
    : "<li>No IOCs extracted.</li>";
  $("reasons").innerHTML = (data.reasons || [])
    .map((r) => `<li>${r.detail} <span class="hint">(+${r.points})</span></li>`)
    .join("") || "<li>No warning signs added to the score.</li>";
  $("attr").textContent = hopPlain(data.attribution || {});
  const anoms = data.header_intel?.anomalies || [];
  $("anoms").innerHTML = anoms.length
    ? anoms.map((a) => `<li>${a.detail}</li>`).join("")
    : "<li>No header-domain mismatches flagged.</li>";
  const di = data.domain_intel || {};
  $("domIntel").textContent = di.domain
    ? `${di.domain}: ${(di.notes || []).join(" ")} MX=${(di.mx_records || []).join(", ") || "none"}`
    : "No From domain to look up.";
  const cu = data.custody || {};
  $("custody").textContent = cu.sha256
    ? `${cu.algorithm} ${cu.sha256} (${cu.byte_length} bytes)`
    : "Hash not stored on this older case.";
  $("nlp").textContent = JSON.stringify(
    {
      threat_class: tclass,
      score: data.score,
      header_intel: data.header_intel,
      domain_intel: data.domain_intel,
      custody: data.custody,
      attribution: data.attribution,
      explain: data.explain,
      iocs: data.iocs,
      urls: data.urls,
      attachments: data.attachments,
      hops: data.geo_hops,
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
}

async function run(payload) {
  setStatus("busy", "Checking this email…");
  const fd = new FormData();
  if (payload.raw) fd.set("raw", payload.raw);
  if (payload.file) fd.set("file", payload.file);
  try {
    const res = await fetch("/api/analyze", { method: "POST", body: fd });
    const data = await res.json();
    if (data.error) {
      setStatus("err", data.error === "empty email" ? "Paste the full original email (with headers) or upload a .eml file." : data.error);
      return;
    }
    setStatus("", "");
    render(data);
    loadCases();
  } catch (e) {
    setStatus("err", "Could not reach the MailTrace server. Keep the PowerShell window open.");
  }
}

async function showCase(id) {
  setStatus("busy", "Loading saved check…");
  try {
    const data = await (await fetch(`/api/cases/${id}`)).json();
    if (data.error) {
      setStatus("err", "That saved check was not found.");
      return;
    }
    setStatus("", "");
    render(data);
  } catch (e) {
    setStatus("err", "Could not load that check.");
  }
}

function syncFileUi() {
  const f = $("file").files[0];
  const paste = ($("raw").value || "").trim();
  $("clearFile").classList.toggle("hidden", !f);
  if (f) {
    $("fileName").textContent = `Using uploaded file: ${f.name}. Click Clear file to paste or pick another.`;
  } else if (paste) {
    $("fileName").textContent = "Will check the pasted text.";
  } else {
    $("fileName").textContent = "";
  }
}

function clearUpload() {
  $("file").value = "";
  syncFileUi();
}

$("run").onclick = () => {
  const f = $("file").files[0];
  const paste = ($("raw").value || "").trim();
  if (f) run({ file: f });
  else run({ raw: paste });
};

$("clearFile").onclick = clearUpload;

$("file").addEventListener("change", syncFileUi);
$("raw").addEventListener("input", syncFileUi);

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

(async function boot() {
  try {
    await loadCases();
  } catch (e) {
    setStatus("err", "Could not reach the MailTrace server. Keep the PowerShell window open, then refresh.");
  }
})();
