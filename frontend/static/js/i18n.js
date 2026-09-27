// Sistema de Internacionalización (i18n) para Supramemory
// Idiomas soportados: Español (Neutral/México), English, Français, Svenska (Suecia)

const I18n = (() => {
  const STORAGE_KEY = 'supramemory_lang';
  const SUPPORTED_LANGS = ['es', 'en', 'fr', 'sv'];
  const LANG_FLAGS = { es: '🇲🇽', en: '🇺🇸', fr: '🇫🇷', sv: '🇸🇪' };
  const LANG_NAMES = { es: 'Español', en: 'English', fr: 'Français', sv: 'Svenska' };

  let currentLang = localStorage.getItem(STORAGE_KEY) || 'es';
  if (!SUPPORTED_LANGS.includes(currentLang)) {
    currentLang = 'es';
  }

  const listeners = [];

  const TRANSLATIONS = {
    es: {
      brand: "Supramemory",
      tab_graph: "🕸️ Grafo",
      tab_editor: "📝 Editor",
      tab_tokens: "🔑 API Tokens",
      tab_docs: "📚 Docs",
      toggle_sidebar: "Mostrar/Ocultar Explorador de Archivos",
      search_placeholder: "Buscar nodo, etiqueta, texto... (Ctrl+K)",
      filter_all_sources: "Todos los orígenes",
      filter_all_tags: "Todas las etiquetas",
      theme_toggle: "Cambiar tema (claro/oscuro)",
      zoom_in: "Acercar (zoom in)",
      zoom_out: "Alejar (zoom out)",
      zoom_reset: "Restablecer vista",
      legend_title: "Leyenda",
      close: "Cerrar",
      status_nodes: "{count} nodos · {links} aristas",
      status_empty: "Nada seleccionado",
      status_hint: "Clic: seleccionar · Doble clic: fijar/liberar · Rueda: zoom · Arrastrar: mover",
      btn_edit: "✏️ Editar",
      btn_edit_title: "Abrir en Editor Completo",
      panel_loading: "Cargando…",
      tokens_title: "API Tokens",
      tokens_desc: "Tokens para que los agentes de IA accedan al grafo de Supramemory. Cada token tiene nombre, permisos y fecha de expiración opcional.",
      token_create_title: "Crear nuevo token",
      token_name_placeholder: "Nombre del token (ej: Agente Hermes)",
      token_scope_read: "read — endpoints GET",
      token_scope_write: "write — POST/PATCH/DELETE",
      token_scope_admin: "admin — todo + gestión de tokens",
      token_expiry_placeholder: "Expiración (opcional)",
      token_btn_create: "Crear token",
      token_generated_title: "Token generado — guárdalo ahora, no podrás volver a verlo",
      token_btn_copy: "Copiar",
      token_btn_close: "Cerrar",
      tokens_table_title: "Tokens existentes",
      th_name: "Nombre",
      th_scopes: "Permisos (Scopes)",
      th_created: "Creado",
      th_last_used: "Último uso",
      th_expires: "Expira",
      th_status: "Estado",
      th_actions: "Acciones",
      tokens_loading: "Cargando...",
      tokens_empty: "No hay tokens todavía. Crea uno arriba.",
      chk_show_revoked: "Mostrar revocados / eliminados",
      btn_revoke: "Revocar",
      btn_delete: "Borrar",
      confirm_revoke: "¿Revocar el token \"{name}\"? Permanecerá en la base de datos pero no podrá usarse más.",
      confirm_delete: "¿Eliminar el token \"{name}\" permanentemente? Esta acción no se puede deshacer.",
      token_copied_alert: "Token copiado al portapapeles",
      prompt_api_key: "Supramemory requiere una clave de API. Ingrésala aquí:",
      vault_title: "BÓVEDA",
      btn_new_note: "Nueva Nota (Ctrl+N)",
      btn_new_folder: "Nueva Carpeta",
      btn_daily_note: "Nota de Hoy",
      btn_refresh_tree: "Refrescar",
      filter_files: "Filtrar archivos...",
      prompt_new_note: "Título de la nueva nota:",
      prompt_new_folder: "Nombre de la carpeta (ej. Proyectos o Trabajo/2026):",
      prompt_rename_note: "Nuevo título para la nota:",
      confirm_delete_note: "¿Eliminar permanentemente la nota \"{title}\"?",
      menu_rename: "✏️ Renombrar (Safe Rename)",
      menu_delete: "🗑️ Eliminar",
      editor_empty_title: "Selecciona o crea una nota",
      editor_empty_desc: "Usa el explorador a la izquierda o haz clic en cualquier nodo del grafo.",
      btn_open_daily: "📅 Abrir Nota de Hoy",
      editor_title_placeholder: "Título de la nota...",
      editor_sync_status: "Sincronizado",
      editor_saving_status: "Guardando...",
      editor_saved_status: "Guardado ✓",
      editor_renamed_status: "Renombrado ✓",
      btn_local_graph: "🕸️ Grafo Local",
      btn_local_graph_title: "Ver subgrafo centrado en esta nota",
      btn_mode_edit: "Solo Editor",
      btn_mode_split: "Doble Panel (Split)",
      btn_mode_preview: "Solo Vista Previa",
      insp_backlinks: "Backlinks",
      insp_unlinked: "Menciones No Enlazadas",
      insp_outgoing: "Enlaces Salientes",
      btn_link_mention: "🔗 Enlazar",
      btn_linked_mention: "Enlazado ✓",
      no_backlinks: "No hay enlaces hacia esta nota.",
      no_unlinked: "No se encontraron menciones sin enlazar.",
      no_outgoing: "Esta nota no enlaza a otras notas.",
      editor_textarea_placeholder: "Escribe en Markdown con [[wikilinks]], #etiquetas y notas destacadas...",
      graph_physics_title: "Ajustes de Grafo",
      graph_mode: "Modo:",
      graph_mode_global: "Global",
      graph_mode_local: "Local",
      graph_depth: "Profundidad:",
      graph_hop: "salto",
      graph_hops: "saltos",
      graph_charge: "Repulsión:",
      graph_dist: "Distancia:",
      graph_orphans: "Mostrar huérfanos",
      graph_labels: "Mostrar etiquetas",
      select_first_local: "Selecciona primero una nota para ver su grafo local."
    },
    en: {
      brand: "Supramemory",
      tab_graph: "🕸️ Graph",
      tab_editor: "📝 Editor",
      tab_tokens: "🔑 API Tokens",
      tab_docs: "📚 Docs",
      toggle_sidebar: "Toggle File Explorer",
      search_placeholder: "Search node, tag, text... (Ctrl+K)",
      filter_all_sources: "All sources",
      filter_all_tags: "All tags",
      theme_toggle: "Toggle theme (light/dark)",
      zoom_in: "Zoom in",
      zoom_out: "Zoom out",
      zoom_reset: "Reset view",
      legend_title: "Legend",
      close: "Close",
      status_nodes: "{count} nodes · {links} edges",
      status_empty: "Nothing selected",
      status_hint: "Click: select · Double-click: pin/unpin · Wheel: zoom · Drag: pan",
      btn_edit: "✏️ Edit",
      btn_edit_title: "Open in Full Editor",
      panel_loading: "Loading…",
      tokens_title: "API Tokens",
      tokens_desc: "Tokens for AI agents to access the Supramemory graph. Each token has a name, scopes, and optional expiration.",
      token_create_title: "Create new token",
      token_name_placeholder: "Token name (e.g., Hermes Agent)",
      token_scope_read: "read — GET endpoints",
      token_scope_write: "write — POST/PATCH/DELETE",
      token_scope_admin: "admin — all + token management",
      token_expiry_placeholder: "Expiration (optional)",
      token_btn_create: "Create token",
      token_generated_title: "Token generated — save it now, it will not be shown again",
      token_btn_copy: "Copy",
      token_btn_close: "Close",
      tokens_table_title: "Existing tokens",
      th_name: "Name",
      th_scopes: "Scopes",
      th_created: "Created",
      th_last_used: "Last used",
      th_expires: "Expires",
      th_status: "Status",
      th_actions: "Actions",
      tokens_loading: "Loading...",
      tokens_empty: "No tokens yet. Create one above.",
      chk_show_revoked: "Show revoked / deleted",
      btn_revoke: "Revoke",
      btn_delete: "Delete",
      confirm_revoke: "Revoke token \"{name}\"? It will remain in database but cannot be used anymore.",
      confirm_delete: "Permanently delete token \"{name}\"? This action cannot be undone.",
      token_copied_alert: "Token copied to clipboard",
      prompt_api_key: "Supramemory requires an API key. Enter it here:",
      vault_title: "VAULT",
      btn_new_note: "New Note (Ctrl+N)",
      btn_new_folder: "New Folder",
      btn_daily_note: "Today's Note",
      btn_refresh_tree: "Refresh",
      filter_files: "Filter files...",
      prompt_new_note: "Title of the new note:",
      prompt_new_folder: "Folder name (e.g. Projects or Work/2026):",
      prompt_rename_note: "New title for the note:",
      confirm_delete_note: "Permanently delete note \"{title}\"?",
      menu_rename: "✏️ Rename (Safe Rename)",
      menu_delete: "🗑️ Delete",
      editor_empty_title: "Select or create a note",
      editor_empty_desc: "Use the explorer on the left or click any node in the graph.",
      btn_open_daily: "📅 Open Today's Note",
      editor_title_placeholder: "Note title...",
      editor_sync_status: "Synced",
      editor_saving_status: "Saving...",
      editor_saved_status: "Saved ✓",
      editor_renamed_status: "Renamed ✓",
      btn_local_graph: "🕸️ Local Graph",
      btn_local_graph_title: "View subgraph centered on this note",
      btn_mode_edit: "Editor Only",
      btn_mode_split: "Split View",
      btn_mode_preview: "Preview Only",
      insp_backlinks: "Backlinks",
      insp_unlinked: "Unlinked Mentions",
      insp_outgoing: "Outgoing Links",
      btn_link_mention: "🔗 Link",
      btn_linked_mention: "Linked ✓",
      no_backlinks: "No incoming links to this note.",
      no_unlinked: "No unlinked mentions found.",
      no_outgoing: "This note does not link to any other notes.",
      editor_textarea_placeholder: "Write in Markdown with [[wikilinks]], #tags and callouts...",
      graph_physics_title: "Graph Settings",
      graph_mode: "Mode:",
      graph_mode_global: "Global",
      graph_mode_local: "Local",
      graph_depth: "Depth:",
      graph_hop: "hop",
      graph_hops: "hops",
      graph_charge: "Repulsion:",
      graph_dist: "Distance:",
      graph_orphans: "Show orphans",
      graph_labels: "Show labels",
      select_first_local: "Select a note first to view its local graph."
    },
    fr: {
      brand: "Supramemory",
      tab_graph: "🕸️ Graphe",
      tab_editor: "📝 Éditeur",
      tab_tokens: "🔑 Jetons API",
      tab_docs: "📚 Docs",
      toggle_sidebar: "Afficher/Masquer l'explorateur",
      search_placeholder: "Rechercher nœud, tag, texte... (Ctrl+K)",
      filter_all_sources: "Toutes les sources",
      filter_all_tags: "Tous les tags",
      theme_toggle: "Changer de thème (clair/sombre)",
      zoom_in: "Zoomer",
      zoom_out: "Dézoomer",
      zoom_reset: "Réinitialiser la vue",
      legend_title: "Légende",
      close: "Fermer",
      status_nodes: "{count} nœuds · {links} arêtes",
      status_empty: "Rien de sélectionné",
      status_hint: "Clic: sélectionner · Double-clic: épingler · Molette: zoom · Glisser: déplacer",
      btn_edit: "✏️ Modifier",
      btn_edit_title: "Ouvrir dans l'éditeur complet",
      panel_loading: "Chargement…",
      tokens_title: "Jetons API",
      tokens_desc: "Jetons permettant aux agents IA d'accéder au graphe Supramemory. Chaque jeton a un nom, des portées et une expiration optionnelle.",
      token_create_title: "Créer un nouveau jeton",
      token_name_placeholder: "Nom du jeton (ex. Agent Hermès)",
      token_scope_read: "read — points d'accès GET",
      token_scope_write: "write — POST/PATCH/DELETE",
      token_scope_admin: "admin — tout + gestion des jetons",
      token_expiry_placeholder: "Expiration (optionnel)",
      token_btn_create: "Créer le jeton",
      token_generated_title: "Jeton généré — enregistrez-le maintenant, il ne sera plus affiché",
      token_btn_copy: "Copier",
      token_btn_close: "Fermer",
      tokens_table_title: "Jetons existants",
      th_name: "Nom",
      th_scopes: "Portées (Scopes)",
      th_created: "Créé",
      th_last_used: "Dernière utilisation",
      th_expires: "Expire",
      th_status: "Statut",
      th_actions: "Actions",
      tokens_loading: "Chargement...",
      tokens_empty: "Aucun jeton pour le moment. Créez-en un ci-dessus.",
      chk_show_revoked: "Afficher les révoqués / supprimés",
      btn_revoke: "Révoquer",
      btn_delete: "Supprimer",
      confirm_revoke: "Révoquer le jeton « {name} » ? Il restera dans la base mais ne pourra plus être utilisé.",
      confirm_delete: "Supprimer définitivement le jeton « {name} » ? Cette action est irréversible.",
      token_copied_alert: "Jeton copié dans le presse-papiers",
      prompt_api_key: "Supramemory requiert une clé API. Saisissez-la ici :",
      vault_title: "COFFRE",
      btn_new_note: "Nouvelle note (Ctrl+N)",
      btn_new_folder: "Nouveau dossier",
      btn_daily_note: "Note du jour",
      btn_refresh_tree: "Actualiser",
      filter_files: "Filtrer les fichiers...",
      prompt_new_note: "Titre de la nouvelle note :",
      prompt_new_folder: "Nom du dossier (ex. Projets ou Travail/2026) :",
      prompt_rename_note: "Nouveau titre pour la note :",
      confirm_delete_note: "Supprimer définitivement la note « {title} » ?",
      menu_rename: "✏️ Renommer (Safe Rename)",
      menu_delete: "🗑️ Supprimer",
      editor_empty_title: "Sélectionnez ou créez une note",
      editor_empty_desc: "Utilisez l'explorateur à gauche ou cliquez sur un nœud du graphe.",
      btn_open_daily: "📅 Ouvrir la note du jour",
      editor_title_placeholder: "Titre de la note...",
      editor_sync_status: "Synchronisé",
      editor_saving_status: "Enregistrement...",
      editor_saved_status: "Enregistré ✓",
      editor_renamed_status: "Renommé ✓",
      btn_local_graph: "🕸️ Graphe local",
      btn_local_graph_title: "Afficher le sous-graphe centré sur cette note",
      btn_mode_edit: "Éditeur seul",
      btn_mode_split: "Vue partagée",
      btn_mode_preview: "Aperçu seul",
      insp_backlinks: "Rétroliens",
      insp_unlinked: "Mentions non liées",
      insp_outgoing: "Liens sortants",
      btn_link_mention: "🔗 Lier",
      btn_linked_mention: "Lié ✓",
      no_backlinks: "Aucun lien entrant vers cette note.",
      no_unlinked: "Aucune mention non liée trouvée.",
      no_outgoing: "Cette note ne contient aucun lien sortant.",
      editor_textarea_placeholder: "Écrivez en Markdown avec des [[wikiliens]], #tags et blocs d'alerte...",
      graph_physics_title: "Paramètres du graphe",
      graph_mode: "Mode :",
      graph_mode_global: "Global",
      graph_mode_local: "Local",
      graph_depth: "Profondeur :",
      graph_hop: "saut",
      graph_hops: "sauts",
      graph_charge: "Répulsion :",
      graph_dist: "Distance :",
      graph_orphans: "Afficher les orphelins",
      graph_labels: "Afficher les étiquettes",
      select_first_local: "Sélectionnez d'abord une note pour afficher son graphe local."
    },
    sv: {
      brand: "Supramemory",
      tab_graph: "🕸️ Graf",
      tab_editor: "📝 Redigerare",
      tab_tokens: "🔑 API-tokens",
      tab_docs: "📚 Dokumentation",
      toggle_sidebar: "Växla filutforskaren",
      search_placeholder: "Sök nod, tagg, text... (Ctrl+K)",
      filter_all_sources: "Alla källor",
      filter_all_tags: "Alla taggar",
      theme_toggle: "Växla tema (ljust/mörkt)",
      zoom_in: "Zooma in",
      zoom_out: "Zooma ut",
      zoom_reset: "Återställ vy",
      legend_title: "Teckenförklaring",
      close: "Stäng",
      status_nodes: "{count} noder · {links} relationer",
      status_empty: "Inget valt",
      status_hint: "Klicka: välj · Dubbelklicka: fäst/lösgör · Hjul: zooma · Dra: panorera",
      btn_edit: "✏️ Redigera",
      btn_edit_title: "Öppna i full redigerare",
      panel_loading: "Laddar…",
      tokens_title: "API-tokens",
      tokens_desc: "Tokens för AI-agenter att ansluta till Supramemory. Varje token har ett namn, behörigheter och valfri giltighetstid.",
      token_create_title: "Skapa ny token",
      token_name_placeholder: "Tokennamn (t.ex. Hermes Agent)",
      token_scope_read: "read — GET-slutpunkter",
      token_scope_write: "write — POST/PATCH/DELETE",
      token_scope_admin: "admin — allt + tokenhantering",
      token_expiry_placeholder: "Giltig till (valfritt)",
      token_btn_create: "Skapa token",
      token_generated_title: "Token skapad — spara den nu, den kommer inte att visas igen",
      token_btn_copy: "Kopiera",
      token_btn_close: "Stäng",
      tokens_table_title: "Befintliga tokens",
      th_name: "Namn",
      th_scopes: "Behörigheter (Scopes)",
      th_created: "Skapad",
      th_last_used: "Senast använd",
      th_expires: "Upphör",
      th_status: "Status",
      th_actions: "Åtgärder",
      tokens_loading: "Laddar...",
      tokens_empty: "Inga tokens än. Skapa en ovan.",
      chk_show_revoked: "Visa återkallade / borttagna",
      btn_revoke: "Återkalla",
      btn_delete: "Ta bort",
      confirm_revoke: "Återkalla token \"{name}\"? Den finns kvar i databasen men kan inte längre användas.",
      confirm_delete: "Ta bort token \"{name}\" permanent? Denna åtgärd kan inte ångras.",
      token_copied_alert: "Token kopierad till urklipp",
      prompt_api_key: "Supramemory kräver en API-nyckel. Ange den här:",
      vault_title: "VALV",
      btn_new_note: "Ny anteckning (Ctrl+N)",
      btn_new_folder: "Ny mapp",
      btn_daily_note: "Dagens anteckning",
      btn_refresh_tree: "Uppdatera",
      filter_files: "Filtrera filer...",
      prompt_new_note: "Titel på den nya anteckningen:",
      prompt_new_folder: "Mappnamn (t.ex. Projekt eller Arbete/2026):",
      prompt_rename_note: "Ny titel för anteckningen:",
      confirm_delete_note: "Ta bort anteckningen \"{title}\" permanent?",
      menu_rename: "✏️ Byt namn (Safe Rename)",
      menu_delete: "🗑️ Ta bort",
      editor_empty_title: "Välj eller skapa en anteckning",
      editor_empty_desc: "Använd utforskaren till vänster eller klicka på valfri nod i grafen.",
      btn_open_daily: "📅 Öppna dagens anteckning",
      editor_title_placeholder: "Anteckningstitel...",
      editor_sync_status: "Synkroniserad",
      editor_saving_status: "Sparar...",
      editor_saved_status: "Sparad ✓",
      editor_renamed_status: "Omdöpt ✓",
      btn_local_graph: "🕸️ Lokal graf",
      btn_local_graph_title: "Visa delgraf centrerad på denna anteckning",
      btn_mode_edit: "Endast redigerare",
      btn_mode_split: "Delad vy",
      btn_mode_preview: "Endast förhandsvisning",
      insp_backlinks: "Bakåtlänkar",
      insp_unlinked: "Olänkade omnämnanden",
      insp_outgoing: "Utgående länkar",
      btn_link_mention: "🔗 Länka",
      btn_linked_mention: "Länkad ✓",
      no_backlinks: "Inga inkommande länkar till denna anteckning.",
      no_unlinked: "Inga olänkade omnämnanden hittades.",
      no_outgoing: "Denna anteckning har inga utgående länkar.",
      editor_textarea_placeholder: "Skriv i Markdown med [[wikilänkar]], #taggar och callouts...",
      graph_physics_title: "Grafinställningar",
      graph_mode: "Läge:",
      graph_mode_global: "Global",
      graph_mode_local: "Lokal",
      graph_depth: "Djup:",
      graph_hop: "hopp",
      graph_hops: "hopp",
      graph_charge: "Frånstötning:",
      graph_dist: "Avstånd:",
      graph_orphans: "Visa föräldralösa",
      graph_labels: "Visa etiketter",
      select_first_local: "Välj en anteckning först för att se dess lokala graf."
    }
  };

  function t(key, params = {}) {
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.es;
    let str = dict[key] || TRANSLATIONS.es[key] || key;
    for (const [k, v] of Object.entries(params)) {
      str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
    return str;
  }

  function getLang() {
    return currentLang;
  }

  function setLang(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) return;
    currentLang = lang;
    localStorage.setItem(STORAGE_KEY, lang);
    applyToDOM();
    listeners.forEach(fn => fn(lang));
  }

  function onLangChange(fn) {
    if (typeof fn === 'function') listeners.push(fn);
  }

  function applyToDOM() {
    // Actualizar indicador del botón en topbar
    const flagEl = document.getElementById('current-lang-flag');
    const codeEl = document.getElementById('current-lang-code');
    if (flagEl) flagEl.textContent = LANG_FLAGS[currentLang];
    if (codeEl) codeEl.textContent = currentLang.toUpperCase();

    // Actualizar textos con data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const text = t(key);
      if (text) el.textContent = text;
    });

    // Actualizar placeholders con data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.dataset.i18nPlaceholder;
      const text = t(key);
      if (text) el.setAttribute('placeholder', text);
    });

    // Actualizar titles con data-i18n-title
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.dataset.i18nTitle;
      const text = t(key);
      if (text) el.setAttribute('title', text);
    });
  }

  function initUI() {
    applyToDOM();

    const langBtn = document.getElementById('lang-btn');
    const langDropdown = document.getElementById('lang-dropdown');

    if (langBtn && langDropdown) {
      langBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        langDropdown.classList.toggle('hidden');
      });

      document.querySelectorAll('.lang-option').forEach(opt => {
        opt.addEventListener('click', () => {
          const lang = opt.dataset.lang;
          setLang(lang);
          langDropdown.classList.add('hidden');
        });
      });

      document.addEventListener('click', (e) => {
        if (!e.target.closest('.lang-selector')) {
          langDropdown.classList.add('hidden');
        }
      });
    }
  }

  return {
    t,
    getLang,
    setLang,
    onLangChange,
    applyToDOM,
    initUI,
    LANG_FLAGS,
    LANG_NAMES,
    SUPPORTED_LANGS,
  };
})();

window.I18n = I18n;
