// Editor de Notas estilo Obsidian con Live Preview, Autocompletado [[ ]] y #, Backlinks y Unlinked Mentions
const Editor = (() => {
  let container = null;
  let currentNote = null;
  let saveTimer = null;
  let viewMode = "split"; // "edit" | "preview" | "split"
  let allNotesList = [];
  let onNoteUpdatedCallback = null;

  function init(containerEl, onNoteUpdated) {
    container = containerEl;
    onNoteUpdatedCallback = onNoteUpdated;
    preloadNotesIndex();
  }

  async function preloadNotesIndex() {
    try {
      allNotesList = await API.listNotes({ limit: 500 });
    } catch (e) {
      console.warn("Could not preload notes index:", e);
    }
  }

  async function open(noteId) {
    if (!container) return;
    container.innerHTML = '<div class="editor-loading">Cargando nota...</div>';
    try {
      const note = await API.getNote(noteId);
      currentNote = note;
      renderEditor();
      await loadBacklinksAndMentions(note.id);
    } catch (e) {
      container.innerHTML = `<div class="editor-error">Error cargando nota: ${escapeHtml(e.message)}</div>`;
    }
  }

  function renderEditor() {
    if (!currentNote) {
      container.innerHTML = `
        <div class="editor-empty">
          <div class="empty-icon">🧠</div>
          <h3>Selecciona o crea una nota</h3>
          <p>Usa el explorador a la izquierda o pulsa en cualquier nodo del grafo.</p>
          <div class="empty-actions">
            <button onclick="Explorer.openDailyNote()">📅 Abrir Nota de Hoy</button>
          </div>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="note-editor-wrap">
        <!-- Top Toolbar del Editor -->
        <div class="editor-header">
          <input type="text" id="note-title-input" class="note-title-input" value="${escapeAttr(currentNote.title)}" placeholder="Título de la nota..." />
          <div class="editor-controls">
            <span id="save-status" class="save-status">Guardado ✓</span>
            <div class="view-mode-buttons">
              <button class="mode-btn ${viewMode === 'edit' ? 'active' : ''}" data-mode="edit" title="Solo Editor">✏️</button>
              <button class="mode-btn ${viewMode === 'split' ? 'active' : ''}" data-mode="split" title="Doble Panel (Split)">◫</button>
              <button class="mode-btn ${viewMode === 'preview' ? 'active' : ''}" data-mode="preview" title="Solo Vista Previa">👁️</button>
            </div>
            <button id="btn-local-graph" class="btn-tool" title="Ver Grafo Local">🕸️ Grafo Local</button>
          </div>
        </div>

        <!-- Barra de Formato Markdown -->
        <div class="markdown-toolbar">
          <button data-insert="**" data-suffix="**" title="Negrita (Ctrl+B)"><b>B</b></button>
          <button data-insert="*" data-suffix="*" title="Cursiva (Ctrl+I)"><i>I</i></button>
          <button data-insert="# " title="Encabezado">H1</button>
          <button data-insert="## " title="Subtítulo">H2</button>
          <button data-insert="[[ " data-suffix=" ]]" title="Wikilink [[ ]]"><b>[[ ]]</b></button>
          <button data-insert="#" title="Tag #"><b>#tag</b></button>
          <button data-insert="- [ ] " title="Lista de Tareas">☑ Tarea</button>
          <button data-insert="> [!NOTE]\n> " title="Callout Note">📝 Callout</button>
          <button data-insert="> [!TIP]\n> " title="Callout Tip">💡 Tip</button>
          <button data-insert="> [!WARNING]\n> " title="Callout Warning">⚠️ Alerta</button>
          <button id="btn-insert-attach" title="Adjuntar Imagen/Archivo">📎 Adjunto</button>
          <input type="file" id="attach-file-input" style="display: none;" />
        </div>

        <!-- Contenedor Principal (Split / Edit / Preview) -->
        <div class="editor-split-container mode-${viewMode}">
          <div class="editor-pane">
            <textarea id="note-content-area" class="note-textarea" placeholder="Escribe en Markdown con [[wikilinks]], #tags y callouts...">${escapeHtml(currentNote.content)}</textarea>
            <!-- Dropdown Autocompletado Omni-Suggest -->
            <div id="omni-suggest" class="omni-suggest hidden"></div>
          </div>
          <div class="preview-pane">
            <div id="note-rendered-html" class="markdown-body"></div>
          </div>
        </div>

        <!-- Inspector Inferior: Backlinks, Menciones No Enlazadas & Outgoing -->
        <div class="editor-inspector">
          <div class="inspector-tabs">
            <button class="insp-tab active" data-insp="backlinks">Backlinks (<span id="backlinks-count">0</span>)</button>
            <button class="insp-tab" data-insp="unlinked">Menciones No Enlazadas (<span id="unlinked-count">0</span>)</button>
            <button class="insp-tab" data-insp="outgoing">Enlaces Salientes</button>
          </div>
          <div class="inspector-content">
            <div id="insp-panel-backlinks" class="insp-panel active"></div>
            <div id="insp-panel-unlinked" class="insp-panel"></div>
            <div id="insp-panel-outgoing" class="insp-panel"></div>
          </div>
        </div>
      </div>
    `;

    setupEditorEvents();
    updateLivePreview();
  }

  function setupEditorEvents() {
    const titleInput = document.getElementById("note-title-input");
    const textarea = document.getElementById("note-content-area");
    const attachInput = document.getElementById("attach-file-input");
    const attachBtn = document.getElementById("btn-insert-attach");

    // Cambio de título con Safe Rename
    titleInput?.addEventListener("change", async (e) => {
      const newTitle = e.target.value.trim();
      if (!newTitle || newTitle === currentNote.title) return;
      try {
        const res = await API.renameNote(currentNote.id, newTitle);
        currentNote.id = res.new_id;
        currentNote.title = res.new_title;
        setSaveStatus("Renombrado ✓");
        Explorer.loadTree();
        Explorer.setActive(res.new_id);
        preloadNotesIndex();
        if (onNoteUpdatedCallback) onNoteUpdatedCallback(currentNote);
      } catch (err) {
        alert(`Error al renombrar: ${err.message}`);
        titleInput.value = currentNote.title;
      }
    });

    // Modos de vista
    container.querySelectorAll(".mode-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        viewMode = btn.dataset.mode;
        container.querySelectorAll(".mode-btn").forEach(b => b.classList.toggle("active", b === btn));
        const splitCont = container.querySelector(".editor-split-container");
        if (splitCont) {
          splitCont.className = `editor-split-container mode-${viewMode}`;
        }
      });
    });

    // Grafo Local
    document.getElementById("btn-local-graph")?.addEventListener("click", () => {
      if (currentNote) {
        // Cambiar a tab de grafo y cargar local graph
        const graphTab = document.querySelector('[data-tab="graph"]');
        if (graphTab) graphTab.click();
        if (window.Graph && Graph.loadLocalGraph) {
          Graph.loadLocalGraph(currentNote.id, 2);
        }
      }
    });

    // Toolbar de formateo
    container.querySelectorAll(".markdown-toolbar button[data-insert]").forEach(btn => {
      btn.addEventListener("click", () => {
        insertAtCursor(textarea, btn.dataset.insert, btn.dataset.suffix || "");
        triggerAutoSave();
      });
    });

    // Adjuntos por archivo
    attachBtn?.addEventListener("click", () => attachInput?.click());
    attachInput?.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        setSaveStatus("Subiendo adjunto...");
        const res = await API.uploadAttachment(file);
        insertAtCursor(textarea, res.embed_markdown, "");
        triggerAutoSave();
        setSaveStatus("Guardado ✓");
      } catch (err) {
        alert(`Error subiendo archivo: ${err.message}`);
      }
    });

    // Drag & Drop de archivos
    textarea?.addEventListener("dragover", (e) => e.preventDefault());
    textarea?.addEventListener("drop", async (e) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        try {
          setSaveStatus("Subiendo archivo...");
          const res = await API.uploadAttachment(file);
          insertAtCursor(textarea, res.embed_markdown, "");
          triggerAutoSave();
          setSaveStatus("Guardado ✓");
        } catch (err) {
          alert(`Error subiendo adjunto: ${err.message}`);
        }
      }
    });

    // Paste de imágenes directo del portapapeles (Ctrl+V)
    textarea?.addEventListener("paste", async (e) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          const blob = items[i].getAsFile();
          e.preventDefault();
          try {
            setSaveStatus("Pegando imagen...");
            const ext = blob.type.split("/")[1] || "png";
            const filename = `paste_${Date.now()}.${ext}`;
            const file = new File([blob], filename, { type: blob.type });
            const res = await API.uploadAttachment(file);
            insertAtCursor(textarea, res.embed_markdown, "");
            triggerAutoSave();
            setSaveStatus("Guardado ✓");
          } catch (err) {
            alert(`Error pegando imagen: ${err.message}`);
          }
          break;
        }
      }
    });

    // Edición y Omni-Suggest
    textarea?.addEventListener("input", () => {
      updateLivePreview();
      handleOmniSuggest(textarea);
      triggerAutoSave();
    });

    // Tabs de inspector
    container.querySelectorAll(".insp-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        const target = tab.dataset.insp;
        container.querySelectorAll(".insp-tab").forEach(t => t.classList.toggle("active", t === tab));
        container.querySelectorAll(".insp-panel").forEach(p => p.classList.toggle("active", p.id === `insp-panel-${target}`));
      });
    });
  }

  function handleOmniSuggest(textarea) {
    const suggestEl = document.getElementById("omni-suggest");
    if (!suggestEl) return;

    const val = textarea.value;
    const cursorPos = textarea.selectionStart;
    const textBefore = val.substring(0, cursorPos);

    // Revisar si está escribiendo [[
    const wikilinkMatch = textBefore.match(/\[\[([^\]]*)$/);
    // Revisar si está escribiendo #
    const tagMatch = textBefore.match(/(?:^|\s)#([a-zA-Z0-9_\-]*)$/);

    if (wikilinkMatch) {
      const query = wikilinkMatch[1].toLowerCase().trim();
      const matches = allNotesList
        .filter(n => n.id !== currentNote.id && n.title.toLowerCase().includes(query))
        .slice(0, 6);

      if (matches.length > 0 || query.length > 0) {
        showSuggestPopup(suggestEl, matches, query, (selectedTitle) => {
          const start = textBefore.lastIndexOf("[[");
          const after = val.substring(cursorPos);
          textarea.value = val.substring(0, start) + `[[${selectedTitle}]]` + after;
          const newPos = start + selectedTitle.length + 4;
          textarea.selectionStart = newPos;
          textarea.selectionEnd = newPos;
          suggestEl.classList.add("hidden");
          textarea.focus();
          triggerAutoSave();
          updateLivePreview();
        });
        return;
      }
    }

    suggestEl.classList.add("hidden");
  }

  function showSuggestPopup(el, matches, query, onSelect) {
    el.innerHTML = "";
    el.classList.remove("hidden");

    matches.forEach((m, idx) => {
      const item = document.createElement("div");
      item.className = `suggest-item ${idx === 0 ? 'selected' : ''}`;
      item.innerHTML = `<span class="sugg-icon">📄</span> <span class="sugg-title">${escapeHtml(m.title)}</span>`;
      item.addEventListener("click", () => onSelect(m.title));
      el.appendChild(item);
    });

    if (query && !matches.some(m => m.title.toLowerCase() === query)) {
      const createItem = document.createElement("div");
      createItem.className = "suggest-item create-new";
      createItem.innerHTML = `<span>➕ Crear nota "<b>${escapeHtml(query)}</b>"</span>`;
      createItem.addEventListener("click", () => onSelect(query));
      el.appendChild(createItem);
    }
  }

  async function updateLivePreview() {
    const textarea = document.getElementById("note-content-area");
    const preview = document.getElementById("note-rendered-html");
    if (!textarea || !preview || !currentNote) return;

    try {
      const rendered = await API.getRendered(currentNote.id);
      preview.innerHTML = rendered.html;

      // Click en wikilinks renderizados
      preview.querySelectorAll(".wikilink").forEach(link => {
        link.addEventListener("click", async (e) => {
          e.preventDefault();
          const targetSlug = link.dataset.target;
          if (targetSlug) {
            open(targetSlug);
            Explorer.setActive(targetSlug);
          }
        });
      });
    } catch (e) {
      preview.innerHTML = `<div class="render-error">Render error: ${escapeHtml(e.message)}</div>`;
    }
  }

  function triggerAutoSave() {
    setSaveStatus("Guardando...");
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      const textarea = document.getElementById("note-content-area");
      if (!textarea || !currentNote) return;
      const content = textarea.value;
      currentNote.content = content;
      try {
        await API.updateNote(currentNote.id, { content });
        setSaveStatus("Guardado ✓");
        await loadBacklinksAndMentions(currentNote.id);
        if (onNoteUpdatedCallback) onNoteUpdatedCallback(currentNote);
      } catch (e) {
        setSaveStatus(`Error guardando: ${e.message}`);
      }
    }, 600);
  }

  function setSaveStatus(msg) {
    const st = document.getElementById("save-status");
    if (st) st.textContent = msg;
  }

  async function loadBacklinksAndMentions(noteId) {
    const backlinksPanel = document.getElementById("insp-panel-backlinks");
    const unlinkedPanel = document.getElementById("insp-panel-unlinked");
    const outgoingPanel = document.getElementById("insp-panel-outgoing");
    const backlinksCount = document.getElementById("backlinks-count");
    const unlinkedCount = document.getElementById("unlinked-count");

    if (!backlinksPanel || !unlinkedPanel) return;

    try {
      const [rendered, unlinkedData] = await Promise.all([
        API.getRendered(noteId),
        API.getUnlinkedMentions(noteId),
      ]);

      // 1. Backlinks explícitos
      const bl = rendered.backlinks || [];
      if (backlinksCount) backlinksCount.textContent = bl.length;
      backlinksPanel.innerHTML = bl.length ? bl.map(b => `
        <div class="mention-card">
          <div class="mention-header">
            <span class="mention-icon">🔗</span>
            <a href="#" class="mention-title" data-target="${escapeAttr(b)}">${escapeHtml(b)}</a>
          </div>
        </div>
      `).join("") : '<div class="muted small">No hay backlinks hacia esta nota.</div>';

      backlinksPanel.querySelectorAll("[data-target]").forEach(a => {
        a.addEventListener("click", (e) => {
          e.preventDefault();
          open(a.dataset.target);
          Explorer.setActive(a.dataset.target);
        });
      });

      // 2. Menciones No Enlazadas (Unlinked Mentions)
      const unlinked = unlinkedData.mentions || [];
      if (unlinkedCount) unlinkedCount.textContent = unlinked.length;
      unlinkedPanel.innerHTML = unlinked.length ? unlinked.map(u => `
        <div class="mention-card unlinked-card">
          <div class="mention-header">
            <span class="mention-icon">💡</span>
            <strong>${escapeHtml(u.source_title)}</strong>
            <button class="btn-link-mention" data-source="${escapeAttr(u.source_id)}" data-target="${escapeAttr(u.match_text)}">🔗 Enlazar</button>
          </div>
          <div class="mention-snippet">${escapeHtml(u.snippet)}</div>
        </div>
      `).join("") : '<div class="muted small">No se encontraron menciones sin enlazar.</div>';

      unlinkedPanel.querySelectorAll(".btn-link-mention").forEach(btn => {
        btn.addEventListener("click", async () => {
          const sourceId = btn.dataset.source;
          const targetTitle = btn.dataset.target;
          try {
            await API.linkMention(noteId, sourceId, targetTitle);
            btn.textContent = "Enlazado ✓";
            btn.disabled = true;
            await loadBacklinksAndMentions(noteId);
            if (onNoteUpdatedCallback) onNoteUpdatedCallback(currentNote);
          } catch (err) {
            alert(`Error enlazando: ${err.message}`);
          }
        });
      });

      // 3. Enlaces Salientes (Outgoing)
      const links = rendered.links || [];
      outgoingPanel.innerHTML = links.length ? links.map(l => `
        <div class="mention-card">
          <span class="mention-icon">↗️</span>
          <a href="#" data-target="${escapeAttr(l)}">${escapeHtml(l)}</a>
        </div>
      `).join("") : '<div class="muted small">Esta nota no enlaza a otras notas.</div>';

      outgoingPanel.querySelectorAll("[data-target]").forEach(a => {
        a.addEventListener("click", (e) => {
          e.preventDefault();
          open(a.dataset.target);
          Explorer.setActive(a.dataset.target);
        });
      });

    } catch (e) {
      console.warn("Error loading backlinks/mentions:", e);
    }
  }

  function insertAtCursor(textarea, prefix, suffix = "") {
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const selected = text.substring(start, end);
    const replacement = `${prefix}${selected}${suffix}`;
    textarea.value = text.substring(0, start) + replacement + text.substring(end);
    const newPos = start + prefix.length + selected.length;
    textarea.selectionStart = newPos;
    textarea.selectionEnd = newPos;
    textarea.focus();
    updateLivePreview();
  }

  function escapeHtml(s) {
    if (!s) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(s) {
    return String(s).replace(/'/g, "\\'").replace(/"/g, "&quot;");
  }

  return {
    init,
    open,
    renderEditor,
    updateLivePreview,
  };
})();

window.Editor = Editor;
