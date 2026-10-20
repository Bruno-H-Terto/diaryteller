const RING = 150;
const state = { app: null, pending: new Map(), selected: null, dragging: null, suppressClick: false };

const $ = (id) => document.getElementById(id);
const api = async (path, options) => {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error((await response.json()).detail || response.statusText);
  return response.json();
};

const colour = (value) => `#${Number(value ?? 0).toString(16).padStart(6, "0").slice(-6)}`;

function tab(name) {
  document.querySelectorAll("nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === name);
  });
  document.querySelectorAll("section").forEach((section) => {
    section.classList.toggle("active", section.id === `tab-${name}`);
  });
}

document.querySelectorAll("nav button").forEach((button) => {
  button.addEventListener("click", () => tab(button.dataset.tab));
});

async function refresh() {
  $("sync-pill").textContent = `${state.pending.size} alterações`;
  try {
    state.app = await api("/api/app");
    $("app-pill").textContent = "app online";
    $("app-pill").classList.remove("down");
  } catch (error) {
    state.app = null;
    $("app-pill").textContent = "app offline";
    $("app-pill").classList.add("down");
  }
  renderMap();
  renderPeople();
  renderRecords();
  renderEvents();
  loadStack();
  loadI18n();
}

function countOf(entityId) {
  return (state.app?.links || []).filter((link) => link.entityId === entityId).length;
}

function positionOf(entity) {
  const pin = (state.app?.pins || []).find((item) => item.entityId === entity.id);
  if (pin) return { x: pin.x * RING, y: pin.y * RING };
  const nodes = state.app.entities.filter((item) => item.id !== "self");
  const index = nodes.findIndex((item) => item.id === entity.id);
  const angle = (index / Math.max(nodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
  return { x: Math.cos(angle) * RING, y: Math.sin(angle) * RING };
}

function renderMap() {
  const map = $("map");
  map.innerHTML = "";
  if (!state.app) {
    map.innerHTML = '<p class="hint" style="padding:20px">App offline: rode <code>make app</code> e tente de novo.</p>';
    return;
  }
  const centre = document.createElement("div");
  centre.className = "node centre";
  centre.style.cssText = "width:86px;height:86px;left:50%;top:50%";
  centre.innerHTML = `<span>${countOf("self") + state.app.records.length} registros</span>`;
  map.append(centre);
  state.app.entities.filter((entity) => entity.id !== "self").forEach((entity) => {
    const node = document.createElement("div");
    const size = Math.min(46 + countOf(entity.id) * 7, 74);
    node.className = `node${state.selected === entity.id ? " selected" : ""}`;
    node.style.width = `${size}px`;
    node.style.height = `${size}px`;
    node.dataset.id = entity.id;
    node.innerHTML = `<span>${entity.name}</span>`;
    const place = () => {
      const offset = state.pending.get(entity.id) || positionOf(entity);
      node.style.left = `calc(50% + ${offset.x}px)`;
      node.style.top = `calc(50% + ${offset.y}px)`;
    };
    place();
    node.addEventListener("pointerdown", (event) => {
      node.setPointerCapture(event.pointerId);
      state.dragging = { entity, node, startX: event.clientX, startY: event.clientY, moved: false };
      state.dragging.offset = state.pending.get(entity.id) || positionOf(entity);
    });
    node.addEventListener("pointermove", (event) => {
      if (!state.dragging || state.dragging.node !== node) return;
      const offset = {
        x: state.dragging.offset.x + (event.clientX - state.dragging.startX),
        y: state.dragging.offset.y + (event.clientY - state.dragging.startY),
      };
      if (Math.hypot(offset.x - state.dragging.offset.x, offset.y - state.dragging.offset.y) > 4) {
        state.dragging.moved = true;
      }
      node.style.left = `calc(50% + ${offset.x}px)`;
      node.style.top = `calc(50% + ${offset.y}px)`;
    });
    node.addEventListener("pointerup", () => {
      if (!state.dragging || state.dragging.node !== node) return;
      const x = parseFloat(node.style.left.split("+")[1]);
      const y = parseFloat(node.style.top.split("+")[1]);
      if (!state.dragging.moved) {
        state.dragging = null;
        return;
      }
      state.pending.set(entity.id, { x: x / RING, y: y / RING });
      state.suppressClick = true;
      state.dragging = null;
      $("sync-pill").textContent = `${state.pending.size} alterações`;
      $("save-layout").disabled = state.pending.size === 0;
    });
    node.addEventListener("click", () => {
      if (state.suppressClick) {
        state.suppressClick = false;
        return;
      }
      state.selected = entity.id;
      tab("people");
      renderMap();
      renderPeople();
    });
    map.append(node);
  });
}

function renderPeople() {
  const list = state.app?.entities.filter((entity) => entity.id !== "self") || [];
  const select = $("person-select");
  select.innerHTML = list.map((entity) => `<option value="${entity.id}">${entity.name}</option>`).join("");
  const entity = list.find((item) => item.id === state.selected) || list[0];
  if (!entity) return;
  state.selected = entity.id;
  select.value = entity.id;
  $("person-name").value = entity.name;
  $("person-model").value = entity.model;
  $("person-bg").value = colour(entity.background);
}

$("person-select").addEventListener("change", (event) => {
  state.selected = event.target.value;
  renderPeople();
  renderMap();
});

$("person-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: $("person-name").value,
    model: $("person-model").value,
    background: parseInt($("person-bg").value.slice(1), 16),
  };
  await api(`/api/app/entities/${state.selected}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  await refresh();
});

$("save-layout").addEventListener("click", async () => {
  for (const [entityId, offset] of state.pending) {
    await api("/api/app/pins", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ entityId, x: offset.x, y: offset.y }),
    });
  }
  state.pending.clear();
  await refresh();
});

$("reset-layout").addEventListener("click", async () => {
  await api("/api/app/pins/reset", { method: "POST" });
  state.pending.clear();
  await refresh();
});

$("table-select").addEventListener("change", (event) => loadTable(event.target.value));

$("voice-simulate").addEventListener("click", async () => {
  const result = $("voice-result");
  result.textContent = "Preparando áudio local…";
  try {
    const prepared = await api("/api/voice/simulate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: $("voice-text").value, language: $("voice-language").value }),
    });
    result.textContent = prepared.ready
      ? "Pronto. No app, abra Conversas e toque no microfone."
      : "O áudio foi criado, mas o replay não ficou disponível.";
  } catch (error) {
    result.textContent = `Falha: ${error.message}`;
  }
});
refresh();
