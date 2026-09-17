const $ = (id) => document.getElementById(id);
let map, layer;

function verdictCopy(data) {
  const s = data.score;
  if (s >= 65) {
    return {
      cls: "danger",
      title: "Dangerous — do not click links or pay",
      sub: "This looks like a scam or someone pretending to be a trusted person.",
    };
  }
  if (s >= 40) {
    return {
      cls: "warn",
      title: "Suspicious — check with the real person on another channel",
      sub: "Some warning signs. Do not send money until you confirm.",
    };
  }
  return {
    cls: "ok",
    title: "Looks legitimate",
    sub: "Mail stamps look real and we did not find the usual scam language.",
  };
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
    return list;
  }
  list.slice(0, 12).forEach((c) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = `#${c.id} [${c.score}] ${c.subject || "(no subject)"}`;
    b.onclick = () => showCase(c.id);
    box.appendChild(b);
  });
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
  $("auth").innerHTML =
    `<span class="pill">Mail stamps</span>` +
    pill("SPF", a.spf) +
    pill("DKIM", a.dkim) +
    pill("DMARC", a.dmarc);
  $("mapCap").textContent = mapCaption(data.geo_hops);
  $("reasons").innerHTML = (data.reasons || [])
    .map((r) => `<li>${r.detail} <span class="hint">(+${r.points})</span></li>`)
    .join("") || "<li>No warning signs added to the score.</li>";
  $("attr").textContent = hopPlain(data.attribution || {});
  $("nlp").textContent = JSON.stringify(
    {
      classification: data.label,
      urgency: data.nlp?.urgency_cues,
      impersonation: data.nlp?.impersonation_cues,
      lookalike: data.nlp?.lookalike_tokens,
      urls: data.urls,
      url_issues: data.nlp?.url_issues,
      attachments: data.attachments,
      hops: data.geo_hops,
    },
    null,
    2
  );
  $("pdf").href = `/api/cases/${data.id}/report.pdf`;
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

(async function boot() {
  try {
    await loadCases();
  } catch (e) {
    setStatus("err", "Could not reach the MailTrace server. Keep the PowerShell window open, then refresh.");
  }
})();
