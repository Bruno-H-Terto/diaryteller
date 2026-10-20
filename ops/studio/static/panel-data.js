/* Data views: diary, events, stack tables and translation coverage. */

function renderRecords() {
  const records = state.app?.records || [];
  $("records-body").innerHTML = records
    .map((record) => `<tr><td>${record.title}</td><td class="truncate">${record.preview}</td>` +
      `<td>${record.eventDate || "—"}</td><td>${record.hasAudio ? "sim" : "—"}</td></tr>`)
    .join("");
}

function renderEvents() {
  const events = state.app?.events || [];
  $("events-body").innerHTML = events
    .map((event) => `<tr><td>${event.title}</td><td>${event.eventDate || "—"}</td>` +
      `<td>${event.precision}</td><td>${event.state}</td></tr>`)
    .join("");
}

async function loadStack() {
  const status = await api("/api/status");
  $("service-cards").innerHTML = status.services
    .map((service) => `<div class="card"><h3>${service.name}</h3>` +
      `<p>${service.up ? "no ar" : "fora"} · ${service.url}</p></div>`)
    .join("");
  const tables = await api("/api/backend/tables");
  const select = $("table-select");
  const previous = select.value;
  select.innerHTML = tables.tables
    .map((table) => `<option value="${table.name}">${table.name} (${table.rows})</option>`)
    .join("");
  if (previous) select.value = previous;
  if (select.value) await loadTable(select.value);
  $("table-hint").textContent = tables.error ? `banco indisponível: ${tables.error}` : "somente leitura";
}

async function loadTable(name) {
  const data = await api(`/api/backend/tables/${name}`);
  const columns = data.rows.length ? Object.keys(data.rows[0]) : [];
  $("table-head").innerHTML = `<tr>${columns.map((column) => `<th>${column}</th>`).join("")}</tr>`;
  $("table-body").innerHTML = data.rows
    .map((row) => `<tr>${columns.map((column) => {
      const value = row[column];
      const text = value === null ? "—" : String(Array.isArray(value) ? value.join(", ") : value);
      return `<td class="truncate">${text}</td>`;
    }).join("")}</tr>`)
    .join("");
}

async function loadI18n() {
  const data = await api("/api/i18n");
  $("i18n-body").innerHTML = data.languages
    .map((language) => `<tr><td>${language.file}</td><td>${language.language}</td>` +
      `<td>${language.label}</td><td>${language.strings}</td><td>${language.plurals}</td>` +
      `<td>${language.missing.length ? language.missing.length : "—"}</td></tr>`)
    .join("");
}
