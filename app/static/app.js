const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const setStatus = (id, message, isError = false) => {
  const node = $(id);
  if (!node) return;
  node.textContent = message;
  node.classList.toggle("error", isError);
};

const requestJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const detail = data.detail || data.error || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
};

const switchView = (viewId) => {
  $$(".tab").forEach((button) => button.classList.toggle("active", button.dataset.view === viewId));
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === viewId));
  if (viewId === "drafts") loadDrafts();
};

const selectedPlatforms = () => {
  const platforms = $$('input[name="platform"]:checked').map((input) => input.value);
  return platforms.length ? platforms : ["linkedin"];
};

const renderDraftCard = (draft) => {
  const template = $("#draft-card-template");
  const card = template.content.firstElementChild.cloneNode(true);
  card.querySelector(".platform").textContent = draft.platform;
  card.querySelector(".status-pill").textContent = draft.status || "draft";
  card.querySelector(".draft-content").textContent = draft.content;

  card.querySelector(".copy-btn").addEventListener("click", async () => {
    await navigator.clipboard.writeText(draft.content);
    card.querySelector(".copy-btn").textContent = "Copiado";
    setTimeout(() => {
      card.querySelector(".copy-btn").textContent = "Copiar";
    }, 1400);
  });

  const approve = card.querySelector(".approve-btn");
  approve.disabled = draft.status === "approved" || draft.status === "published" || !draft.id;
  approve.addEventListener("click", async () => {
    approve.disabled = true;
    await requestJson(`/drafts/${draft.id}/approve`, { method: "POST" });
    draft.status = "approved";
    card.querySelector(".status-pill").textContent = "approved";
  });

  return card;
};

const renderDrafts = (container, drafts) => {
  container.innerHTML = "";
  if (!drafts.length) {
    container.innerHTML = '<div class="ideas empty">Todavia no hay borradores.</div>';
    return;
  }
  drafts.forEach((draft) => container.appendChild(renderDraftCard(draft)));
};

const loadDrafts = async () => {
  const list = $("#drafts-list");
  list.innerHTML = '<div class="ideas empty">Cargando borradores...</div>';
  try {
    const drafts = await requestJson("/drafts");
    renderDrafts(list, drafts);
  } catch (error) {
    list.innerHTML = `<div class="ideas empty">Error: ${error.message}</div>`;
  }
};

$$(".tab").forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.view));
});

$("#ingest-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("#ingest-status", "Guardando...");
  try {
    await requestJson("/posts/ingest", {
      method: "POST",
      body: JSON.stringify({
        platform: $("#example-platform").value,
        text: $("#example-text").value,
        url: $("#example-url").value || null,
      }),
    });
    $("#example-text").value = "";
    $("#example-url").value = "";
    setStatus("#ingest-status", "Ejemplo guardado");
  } catch (error) {
    setStatus("#ingest-status", error.message, true);
  }
});

$("#ideas-btn").addEventListener("click", async () => {
  const topic = $("#topic").value.trim();
  if (!topic) {
    setStatus("#generate-status", "Agrega un tema primero", true);
    return;
  }
  setStatus("#generate-status", "Generando ideas...");
  $("#ideas-output").textContent = "Pensando angulos...";
  $("#ideas-output").classList.remove("empty");
  try {
    const data = await requestJson("/ideas", {
      method: "POST",
      body: JSON.stringify({
        topic,
        brand_context: $("#brand-context").value || null,
      }),
    });
    $("#ideas-output").textContent = data.ideas;
    setStatus("#generate-status", "Ideas listas");
  } catch (error) {
    $("#ideas-output").textContent = error.message;
    setStatus("#generate-status", error.message, true);
  }
});

$("#generate-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("#generate-status", "Generando borradores...");
  const output = $("#generated-output");
  output.innerHTML = '<div class="ideas empty">Creando versiones por plataforma...</div>';
  try {
    const data = await requestJson("/generate", {
      method: "POST",
      body: JSON.stringify({
        topic: $("#topic").value,
        platforms: selectedPlatforms(),
        examples_per_platform: 3,
        brand_context: $("#brand-context").value || null,
      }),
    });
    renderDrafts(output, data.drafts.map((draft) => ({ ...draft, status: "draft" })));
    setStatus("#generate-status", "Borradores listos");
  } catch (error) {
    output.innerHTML = `<div class="ideas empty">Error: ${error.message}</div>`;
    setStatus("#generate-status", error.message, true);
  }
});

$("#profile-btn").addEventListener("click", async () => {
  const topic = $("#profile-topic").value.trim();
  if (!topic) {
    setStatus("#profile-status", "Agrega un tema", true);
    return;
  }
  setStatus("#profile-status", "Buscando...");
  const output = $("#profile-output");
  output.classList.remove("empty");
  output.textContent = "Recuperando ejemplos similares...";
  try {
    const data = await requestJson(`/style-profile?topic=${encodeURIComponent(topic)}`);
    output.innerHTML = `<p>${data.profile}</p>` + data.examples.map((example) => `
      <div class="example-item">
        <div><strong>${example.platform}</strong> <span class="score">${Number(example.score).toFixed(3)}</span></div>
        <p>${example.text}</p>
      </div>
    `).join("");
    setStatus("#profile-status", "Listo");
  } catch (error) {
    output.textContent = error.message;
    setStatus("#profile-status", error.message, true);
  }
});

$("#load-drafts").addEventListener("click", loadDrafts);
$("#refresh-drafts").addEventListener("click", loadDrafts);
