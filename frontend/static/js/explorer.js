// Gestor del File Explorer (Árbol de carpetas y archivos estilo Obsidian)
const Explorer = (() => {
  let treeContainer = null;
  let activeNoteId = null;
  let onSelectNoteCallback = null;
  let treeData = null;

  function init(containerEl, onSelectNote) {
    treeContainer = containerEl;
    onSelectNoteCallback = onSelectNote;
    loadTree();
  }

  async function loadTree() {
    if (!treeContainer) return;
    if (typeof API === 'undefined' || typeof API.getTree !== 'function') {
      console.warn("API.getTree not ready yet, retrying...");
      setTimeout(loadTree, 200);
      return;
    }
    try {
      treeData = await API.getTree();
      renderTree(treeData);
    } catch (e) {
      console.error("Error loading vault tree:", e);
      treeContainer.innerHTML = `<div class="tree-error" style="padding:10px;font-size:12px;color:var(--fg-muted);">Error cargando archivos: ${e.message}<br><small>Si persiste, presiona Ctrl+F5 para limpiar caché.</small></div>`;
    }
  }

  function renderTree(rootNode) {
    treeContainer.innerHTML = "";
    
    // Barra de herramientas superior del explorador
    const toolbar = document.createElement("div");
    toolbar.className = "explorer-toolbar";
    toolbar.innerHTML = `
      <div class="explorer-title">
        <span>VAULT</span>
        <div class="explorer-actions">
          <button id="btn-new-note" title="Nueva Nota (Ctrl+N)">📄</button>
          <button id="btn-new-folder" title="Nueva Carpeta">📁</button>
          <button id="btn-daily-note" title="Nota de Hoy">📅</button>
          <button id="btn-refresh-tree" title="Refrescar">🔄</button>
        </div>
      </div>
      <input type="text" id="explorer-filter" class="explorer-filter" placeholder="Filtrar archivos..." />
    `;
    treeContainer.appendChild(toolbar);

    // Contenedor de nodos
    const listEl = document.createElement("div");
    listEl.className = "tree-list";
    if (rootNode && rootNode.children) {
      rootNode.children.forEach(child => {
        listEl.appendChild(createNodeElement(child));
      });
    }
    treeContainer.appendChild(listEl);

    // Eventos de barra
    document.getElementById("btn-new-note")?.addEventListener("click", promptNewNote);
    document.getElementById("btn-new-folder")?.addEventListener("click", promptNewFolder);
    document.getElementById("btn-daily-note")?.addEventListener("click", openDailyNote);
    document.getElementById("btn-refresh-tree")?.addEventListener("click", loadTree);

    // Filtro en vivo
    document.getElementById("explorer-filter")?.addEventListener("input", (e) => {
      const term = e.target.value.toLowerCase().trim();
      filterTree(term);
    });
  }

  function createNodeElement(item) {
    const el = document.createElement("div");
    el.className = `tree-item tree-${item.type}`;
    el.dataset.path = item.path;

    if (item.type === "directory") {
      el.innerHTML = `
        <div class="tree-label folder-label">
          <span class="folder-arrow">▼</span>
          <span class="folder-icon">📁</span>
          <span class="tree-name">${escapeHtml(item.name)}</span>
        </div>
        <div class="folder-children"></div>
      `;

      const folderChildren = el.querySelector(".folder-children");
      const folderArrow = el.querySelector(".folder-arrow");
      const folderHeader = el.querySelector(".tree-label");

      if (item.children) {
        item.children.forEach(c => folderChildren.appendChild(createNodeElement(c)));
      }

      folderHeader.addEventListener("click", (e) => {
        e.stopPropagation();
        const isCollapsed = folderChildren.classList.toggle("collapsed");
        folderArrow.textContent = isCollapsed ? "▶" : "▼";
      });
    } else {
      // Archivo de nota o adjunto
      const isAttach = item.type === "attachment";
      const icon = isAttach ? "📎" : "📄";
      el.dataset.id = item.id;
      if (item.id === activeNoteId) el.classList.add("active");

      el.innerHTML = `
        <div class="tree-label file-label" title="${escapeHtml(item.path)}">
          <span class="file-icon">${icon}</span>
          <span class="tree-name">${escapeHtml(item.title || item.name)}</span>
          ${!isAttach ? `
            <div class="item-menu-btn" title="Opciones">⋮</div>
          ` : ''}
        </div>
      `;

      const fileLabel = el.querySelector(".file-label");
      fileLabel.addEventListener("click", (e) => {
        e.stopPropagation();
        setActive(item.id);
        if (onSelectNoteCallback) onSelectNoteCallback(item);
      });

      if (!isAttach) {
        fileLabel.addEventListener("contextmenu", (e) => {
          e.preventDefault();
          e.stopPropagation();
          showItemMenu(e, item);
        });
      }

      const menuBtn = el.querySelector(".item-menu-btn");
      if (menuBtn) {
        menuBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          showItemMenu(e, item);
        });
      }
    }

    return el;
  }

  function setActive(noteId) {
    activeNoteId = noteId;
    if (!treeContainer) return;
    treeContainer.querySelectorAll(".tree-file").forEach(el => {
      el.classList.toggle("active", el.dataset.id === noteId);
    });
  }

  function filterTree(term) {
    if (!treeContainer) return;
    const fileItems = treeContainer.querySelectorAll(".tree-file, .tree-attachment");
    fileItems.forEach(el => {
      const name = el.querySelector(".tree-name")?.textContent.toLowerCase() || "";
      const matches = !term || name.includes(term);
      el.style.display = matches ? "" : "none";
    });
  }

  async function promptNewNote() {
    const title = prompt("Título de la nueva nota:");
    if (!title || !title.trim()) return;
    try {
      const note = await API.createNote({
        title: title.trim(),
        content: `# ${title.trim()}\n\n`,
        source: "manual",
      });
      await loadTree();
      setActive(note.id);
      if (onSelectNoteCallback) onSelectNoteCallback(note);
    } catch (e) {
      alert(`Error creando nota: ${e.message}`);
    }
  }

  async function promptNewFolder() {
    const folder = prompt("Nombre de la carpeta (ej. Proyectos o Trabajo/2026):");
    if (!folder || !folder.trim()) return;
    try {
      await API.createFolder(folder.trim());
      await loadTree();
    } catch (e) {
      alert(`Error creando carpeta: ${e.message}`);
    }
  }

  async function openDailyNote() {
    try {
      const res = await API.getDailyNote();
      await loadTree();
      setActive(res.note.id);
      if (onSelectNoteCallback) onSelectNoteCallback(res.note);
    } catch (e) {
      alert(`Error abriendo nota diaria: ${e.message}`);
    }
  }

  function showItemMenu(e, item) {
    const existing = document.getElementById("tree-context-menu");
    if (existing) existing.remove();

    const menu = document.createElement("div");
    menu.id = "tree-context-menu";
    menu.className = "context-menu";
    menu.style.left = `${e.pageX}px`;
    menu.style.top = `${e.pageY}px`;

    menu.innerHTML = `
      <div class="menu-item" id="menu-rename">✏️ Renombrar (Safe Rename)</div>
      <div class="menu-item danger" id="menu-delete">🗑️ Eliminar</div>
    `;
    document.body.appendChild(menu);

    const closeMenu = () => menu.remove();
    setTimeout(() => document.addEventListener("click", closeMenu, { once: true }), 10);

    menu.querySelector("#menu-rename")?.addEventListener("click", async () => {
      const newTitle = prompt("Nuevo título para la nota:", item.title || item.name);
      if (!newTitle || newTitle.trim() === item.title) return;
      try {
        const res = await API.renameNote(item.id, newTitle.trim());
        alert(`Nota renombrada exitosamente. Se actualizaron ${res.updated_links_count} wikilinks en el vault.`);
        await loadTree();
        if (onSelectNoteCallback) onSelectNoteCallback(await API.getNote(res.new_id));
      } catch (err) {
        alert(`Error al renombrar: ${err.message}`);
      }
    });

    menu.querySelector("#menu-delete")?.addEventListener("click", async () => {
      if (!confirm(`¿Eliminar permanentemente la nota "${item.title || item.name}"?`)) return;
      try {
        await API.deleteNote(item.id);
        await loadTree();
        if (onSelectNoteCallback) onSelectNoteCallback(null);
      } catch (err) {
        alert(`Error eliminando nota: ${err.message}`);
      }
    });
  }

  function escapeHtml(s) {
    if (!s) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  return {
    init,
    loadTree,
    setActive,
    openDailyNote,
  };
})();

window.Explorer = Explorer;
