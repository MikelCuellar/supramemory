// Motor del grafo — D3 force-directed con soporte para Grafo Global, Grafo Local y Controles de Física en Vivo
const Graph = (() => {
  let svg, gRoot, simulation, zoomBehavior;
  let nodesData = [], linksData = [];
  let selectedNode = null;
  let onSelectCallback = null;
  let width = 800, height = 600;
  let particleAnimId = null;

  // Umbrales de rendimiento: por encima se dibuja en <canvas> en vez de SVG
  // (ver setupCanvasRender), y las partículas por arista solo en grafos chicos.
  const CANVAS_MIN_NODES = 250;
  const CANVAS_MIN_LINKS = 600;
  const MAX_PARTICLE_EDGES = 300;
  const CANVAS_LABEL_MIN_ZOOM = 1.4;

  // Estado del modo canvas
  let canvas = null, ctx = null, canvasMode = false, drawPending = false;
  let viewTransform = d3.zoomIdentity;
  let hoverNode = null;
  let focusId = null;     // nodo cuyo vecindario se resalta (hover)
  let dimmedIds = null;   // Set de ids atenuados, o null

  // Estado y configuraciones de simulación
  let graphMode = "global"; // "global" | "local"
  let localRootId = null;
  let localDepth = 1;

  let physicsConfig = {
    charge: -140,
    distance: 85,
    strength: 0.4,
    showOrphans: true,
    showLabels: true,
  };

  function measure() {
    if (!svg) return;
    const r = svg.node().getBoundingClientRect();
    width = r.width || 800;
    height = r.height || 600;
  }

  function init(onSelect) {
    onSelectCallback = onSelect;
    svg = d3.select('#graph-svg');
    gRoot = svg.select('#graph-root');
    measure();

    zoomBehavior = d3.zoom()
      .scaleExtent([0.1, 6])
      // En modo canvas no hay elementos .node que detengan el evento: sobre un
      // nodo, el gesto es arrastrarlo (o dblclick para soltarlo), no hacer pan/zoom
      .filter(event => (!event.ctrlKey || event.type === 'wheel') && !event.button
        && !(canvasMode && event.type !== 'wheel' && nodeAtEvent(event)))
      .on('zoom', (event) => {
        gRoot.attr('transform', event.transform);
        viewTransform = event.transform;
        requestDraw();
      });
    svg.call(zoomBehavior);
    setupCanvasInteractions();

    svg.on('click', (event) => {
      if (canvasMode) {
        const d = nodeAtEvent(event);
        if (d) selectNode(d);
        else deselect();
        return;
      }
      if (!event.target.closest('.node')) {
        deselect();
      }
    });

    let rt = null;
    window.addEventListener('resize', () => {
      if (rt) clearTimeout(rt);
      rt = setTimeout(() => {
        measure();
        if (canvasMode && width >= 100 && height >= 100) resizeCanvas();
        if (simulation) {
          simulation.force('center', d3.forceCenter(width / 2, height / 2));
          simulation.alpha(0.3).restart();
        }
      }, 250);
    });

    setupGraphControlsUI();
  }

  function render(graphData) {
    requestAnimationFrame(() => {
      measure();
      doRender(graphData);
    });
  }

  async function loadLocalGraph(rootNodeId, depth = 1) {
    graphMode = "local";
    localRootId = rootNodeId;
    localDepth = depth;
    updateModeIndicator();

    try {
      const data = await API.localGraph(rootNodeId, depth);
      render(data);
      setSelectedStatus(`Grafo Local: ${rootNodeId} (profundidad ${depth})`);
    } catch (e) {
      console.error("Error loading local graph:", e);
    }
  }

  function doRender(graphData) {
    if (width < 100 || height < 100) {
      requestAnimationFrame(() => {
        measure();
        doRender(graphData);
      });
      return;
    }

    let rawNodes = graphData.nodes || [];
    let rawEdges = graphData.edges || [];

    if (!physicsConfig.showOrphans) {
      rawNodes = rawNodes.filter(n => n.degree > 0);
      const activeIds = new Set(rawNodes.map(n => n.id));
      rawEdges = rawEdges.filter(e => activeIds.has(e.source) && activeIds.has(e.target));
    }

    nodesData = rawNodes.map(n => ({ ...n }));
    linksData = rawEdges.map(e => ({ ...e }));
    canvasMode = nodesData.length > CANVAS_MIN_NODES || linksData.length > CANVAS_MIN_LINKS;

    updateStatus();
    // La simulación anterior seguía calculando sobre nodos ya eliminados
    if (simulation) simulation.stop();
    if (particleAnimId) {
      cancelAnimationFrame(particleAnimId);
      particleAnimId = null;
    }
    gRoot.selectAll('*').remove();
    focusId = null;
    dimmedIds = null;
    hoverNode = null;

    placeNodesInGrid();

    const onTick = canvasMode ? setupCanvasRender() : setupSvgRender();

    simulation = d3.forceSimulation(nodesData)
      .force('link', d3.forceLink(linksData)
        .id(d => d.id)
        .distance(physicsConfig.distance)
        .strength(physicsConfig.strength)
      )
      .force('charge', d3.forceManyBody()
        .strength(physicsConfig.charge)
        .distanceMax(400)
      )
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => 16 + Math.sqrt(d.degree || 0) * 3))
      // Grafos grandes: converger en ~130 ticks en vez de ~300
      .alphaDecay(canvasMode ? 0.05 : 0.02)
      .on('tick', onTick);
  }

  // Posición inicial orgánica
  function placeNodesInGrid() {
    const n = nodesData.length;
    const cols = Math.ceil(Math.sqrt(n)) || 1;
    const rows = Math.ceil(n / cols) || 1;
    const cellW = Math.min((width * 0.7) / cols, 130);
    const cellH = Math.min((height * 0.7) / rows, 100);
    const gridW = cols * cellW;
    const gridH = rows * cellH;
    const startX = (width - gridW) / 2 + cellW / 2;
    const startY = (height - gridH) / 2 + cellH / 2;
    nodesData.forEach((nd, i) => {
      const c = i % cols;
      const r = Math.floor(i / cols);
      nd.x = startX + c * cellW + (Math.random() - 0.5) * cellW * 0.5;
      nd.y = startY + r * cellH + (Math.random() - 0.5) * cellH * 0.5;
      nd.vx = 0;
      nd.vy = 0;
    });
  }

  function nodeRadius(d) {
    return (d.id === localRootId ? 9 : 5) + Math.sqrt(d.degree || 0) * 2.5;
  }

  // ---------- Render SVG (grafos chicos: efectos de brillo, pulso y partículas) ----------

  function setupSvgRender() {
    if (canvas) canvas.style.display = 'none';

    // Defs de brillo neural
    const defs = gRoot.append('defs');
    const filter = defs.append('filter')
      .attr('id', 'neural-glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%');
    filter.append('feGaussianBlur')
      .attr('stdDeviation', '3')
      .attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // 1. Aristas
    const linkSel = gRoot.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(linksData)
      .join('line')
      .attr('class', d => `link ${d.kind}`)
      .attr('stroke-width', d => Math.max(1.2, Math.sqrt(d.weight || 1) * 1.5))
      .attr('stroke-opacity', 0.5);

    // 2. Impulsos Sinápticos. Sin filtro SVG: un blur por partícula
    // re-rasterizado en cada frame era el mayor costo de render.
    const particlesData = linksData.length > MAX_PARTICLE_EDGES ? [] : linksData.map((link, idx) => ({
      id: `p-${idx}`,
      link: link,
      progress: Math.random(),
      speed: 0.003 + Math.random() * 0.005
    }));

    const particleSel = gRoot.append('g')
      .attr('class', 'synapses')
      .selectAll('circle')
      .data(particlesData)
      .join('circle')
      .attr('class', 'synapse-particle')
      .attr('r', 2.5)
      .attr('fill', '#00f3ff');

    // 3. Nodos
    const nodeGroup = gRoot.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodesData, d => d.id)
      .join('g')
      .attr('class', d => `node source-${d.source} ${d.id === localRootId ? 'local-root' : ''}`)
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .call(makeDrag())
      .on('click', (event, d) => {
        event.stopPropagation();
        selectNode(d);
      })
      .on('dblclick', (event, d) => {
        event.stopPropagation();
        d.fx = null;
        d.fy = null;
        d3.select(event.currentTarget).classed('pinned', false);
        if (simulation) simulation.alpha(0.3).restart();
      })
      .on('mouseenter', (event, d) => highlightConnections(d))
      .on('mouseleave', () => clearHighlight());

    // Halos
    nodeGroup.append('circle')
      .attr('class', 'node-halo')
      .attr('r', d => (d.id === localRootId ? 14 : 8) + Math.sqrt(d.degree || 0) * 3.5)
      .attr('fill', 'currentColor')
      .attr('opacity', d => (d.id === localRootId ? 0.35 : 0.15));

    // Núcleos
    nodeGroup.append('circle')
      .attr('class', 'node-core')
      .attr('r', nodeRadius)
      .attr('stroke-width', d => (d.id === localRootId ? 2.5 : 1.5))
      .attr('filter', 'url(#neural-glow)');

    // Text labels
    nodeGroup.append('text')
      .attr('class', 'node-label')
      .attr('x', d => 6 + Math.sqrt(d.degree || 0) * 2.5 + 4)
      .attr('y', 3)
      .attr('opacity', physicsConfig.showLabels ? 1 : 0)
      .text(d => truncate(d.label, 30));

    // Animación continua e independiente de partículas sinápticas
    const container = document.getElementById('graph-container');
    function stepParticles() {
      particleAnimId = requestAnimationFrame(stepParticles);
      // Con el grafo oculto (pestaña de editor/docs) no hay nada que pintar
      if (container && container.offsetParent === null) return;
      particleSel
        .attr('cx', d => {
          d.progress += d.speed;
          if (d.progress > 1) d.progress = 0;
          const sx = d.link.source.x || 0, tx = d.link.target.x || 0;
          return sx + (tx - sx) * d.progress;
        })
        .attr('cy', d => {
          const sy = d.link.source.y || 0, ty = d.link.target.y || 0;
          return sy + (ty - sy) * d.progress;
        });
    }
    if (particlesData.length > 0) {
      particleAnimId = requestAnimationFrame(stepParticles);
    }

    return () => {
      linkSel
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`);
    };
  }

  // ---------- Render Canvas (grafos grandes) ----------
  // Con SVG cada tick reescribe miles de atributos del DOM y el navegador repinta
  // todo: con 1500 nodos no pasaba de ~7 FPS. En canvas cada frame es un solo
  // dibujado; el <svg> queda encima, vacío, solo para capturar zoom/pan y eventos.

  function setupCanvasRender() {
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = 'graph-canvas';
      svg.node().parentNode.insertBefore(canvas, svg.node());
      ctx = canvas.getContext('2d');
    }
    canvas.style.display = '';
    resizeCanvas();
    return requestDraw;
  }

  function resizeCanvas() {
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    requestDraw();
  }

  function requestDraw() {
    if (drawPending || !canvasMode) return;
    drawPending = true;
    requestAnimationFrame(drawCanvas);
  }

  function nodeColorVar(d) {
    const src = String(d.source || '');
    return src.startsWith('agent') ? '--c-agent' : `--c-${src}`;
  }

  function drawCanvas() {
    drawPending = false;
    if (!canvasMode || !ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const t = viewTransform;
    const styles = getComputedStyle(document.body);
    const colorCache = new Map();
    const cssColor = (name, fallback) => {
      if (!colorCache.has(name)) colorCache.set(name, styles.getPropertyValue(name).trim());
      return colorCache.get(name) || fallback;
    };

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.translate(t.x, t.y);
    ctx.scale(t.k, t.k);

    // Visible en coordenadas del grafo, para no dibujar etiquetas fuera de pantalla
    const [x0, y0] = t.invert([0, 0]);
    const [x1, y1] = t.invert([width, height]);

    const isLinkDim = l => focusId
      ? l.source.id !== focusId && l.target.id !== focusId
      : !!dimmedIds && (dimmedIds.has(l.source.id) || dimmedIds.has(l.target.id));
    const isNodeDim = d => !!dimmedIds && dimmedIds.has(d.id);

    // 1. Aristas: un único stroke() por tipo y estado
    const groups = new Map();
    for (const l of linksData) {
      const key = `${l.kind}|${isLinkDim(l) ? 1 : 0}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(l);
    }
    // Exactamente 1 px de dispositivo, sin importar el zoom: Chrome dibuja esas
    // líneas por un camino rápido ("hairline"). Con 1.2 px, 5600 aristas bajaban
    // de 60 a ~6 FPS.
    ctx.lineWidth = 1 / (t.k * dpr);
    for (const [key, links] of groups) {
      const [kind, dim] = key.split('|');
      ctx.strokeStyle = cssColor(`--link-${kind}`, cssColor('--link-default', '#4a4a5a'));
      ctx.globalAlpha = dim === '1' ? 0.04 : (kind === 'semantic' ? 0.3 : 0.4);
      ctx.beginPath();
      for (const l of links) {
        ctx.moveTo(l.source.x, l.source.y);
        ctx.lineTo(l.target.x, l.target.y);
      }
      ctx.stroke();
    }

    // 2. Nodos
    for (const d of nodesData) {
      const r = nodeRadius(d);
      if (d.x + r < x0 || d.x - r > x1 || d.y + r < y0 || d.y - r > y1) continue;
      ctx.globalAlpha = isNodeDim(d) ? 0.15 : 1;
      ctx.fillStyle = cssColor(nodeColorVar(d), cssColor('--c-default', '#94a3b8'));
      ctx.beginPath();
      ctx.arc(d.x, d.y, r, 0, 2 * Math.PI);
      ctx.fill();
      const highlighted = d === selectedNode || d === hoverNode || d.id === localRootId;
      if (highlighted || d.fx != null) {
        ctx.lineWidth = highlighted ? 2.5 : 2;
        ctx.strokeStyle = highlighted ? cssColor('--fg', '#e8e8ef') : cssColor('--accent-bright', '#c7ff3a');
        ctx.stroke();
      }
    }

    // 3. Etiquetas: con zoom lejano son ilegibles y caras; solo al acercarse
    // (o la del nodo bajo el cursor / seleccionado)
    ctx.font = "11px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 3;
    ctx.strokeStyle = cssColor('--label-stroke', '#0a0a0f');
    ctx.fillStyle = cssColor('--label-fill', '#ffffff');
    const showAll = physicsConfig.showLabels && t.k >= CANVAS_LABEL_MIN_ZOOM;
    const labelNodes = showAll ? nodesData : [hoverNode, selectedNode].filter(Boolean);
    for (const d of labelNodes) {
      if (d.x < x0 - 200 || d.x > x1 || d.y < y0 || d.y > y1) continue;
      ctx.globalAlpha = isNodeDim(d) ? 0.15 : 1;
      const label = truncate(d.label, 30);
      const lx = d.x + 6 + Math.sqrt(d.degree || 0) * 2.5 + 4;
      ctx.strokeText(label, lx, d.y);
      ctx.fillText(label, lx, d.y);
    }
    ctx.globalAlpha = 1;
  }

  function nodeAtEvent(event) {
    if (!simulation) return null;
    const [px, py] = d3.pointer(event, svg.node());
    const [x, y] = viewTransform.invert([px, py]);
    const d = simulation.find(x, y, 40);
    return d && Math.hypot(d.x - x, d.y - y) <= nodeRadius(d) + 3 ? d : null;
  }

  function setupCanvasInteractions() {
    // Arrastrar nodos (el sujeto lleva coordenadas de pantalla; se invierten con el zoom)
    svg.call(d3.drag()
      .filter(event => canvasMode && !event.button)
      .subject(event => {
        const d = nodeAtEvent(event.sourceEvent);
        return d ? { node: d, x: event.x, y: event.y } : null;
      })
      .on('start', event => {
        if (!event.active && simulation) simulation.alphaTarget(0.3).restart();
        const d = event.subject.node;
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', event => {
        const [x, y] = viewTransform.invert([event.x, event.y]);
        event.subject.node.fx = x;
        event.subject.node.fy = y;
        requestDraw();
      })
      .on('end', event => {
        if (!event.active && simulation) simulation.alphaTarget(0);
      }));

    svg.on('mousemove.canvas', event => {
      if (!canvasMode) return;
      const d = nodeAtEvent(event);
      if (d === hoverNode) return;
      hoverNode = d;
      svg.style('cursor', d ? 'pointer' : null);
      if (d) highlightConnections(d);
      else clearHighlight();
    });

    svg.on('mouseleave.canvas', () => {
      if (!canvasMode || !hoverNode) return;
      hoverNode = null;
      svg.style('cursor', null);
      clearHighlight();
    });

    svg.on('dblclick.canvas', event => {
      if (!canvasMode) return;
      const d = nodeAtEvent(event);
      if (!d) return;
      d.fx = null;
      d.fy = null;
      if (simulation) simulation.alpha(0.3).restart();
    });
  }

  function makeDrag() {
    function dragstarted(event, d) {
      if (!event.active && simulation) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    function dragended(event, d) {
      if (!event.active && simulation) simulation.alphaTarget(0);
      d3.select(this).classed('pinned', true);
    }
    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }

  function selectNode(node) {
    selectedNode = node;
    d3.selectAll('.node').classed('selected', d => d.id === node.id);
    requestDraw();
    if (onSelectCallback) onSelectCallback(node);
  }

  function deselect() {
    selectedNode = null;
    d3.selectAll('.node').classed('selected', false);
    requestDraw();
    if (onSelectCallback) onSelectCallback(null);
  }

  function highlightConnections(node) {
    const connected = new Set([node.id]);
    linksData.forEach(l => {
      const s = l.source.id || l.source;
      const t = l.target.id || l.target;
      if (s === node.id) connected.add(t);
      if (t === node.id) connected.add(s);
    });

    if (canvasMode) {
      focusId = node.id;
      dimmedIds = new Set(nodesData.filter(d => !connected.has(d.id)).map(d => d.id));
      requestDraw();
      return;
    }
    d3.selectAll('.node').classed('dimmed', d => !connected.has(d.id));
    d3.selectAll('.link').classed('dimmed', d => {
      const s = d.source.id || d.source;
      const t = d.target.id || d.target;
      return s !== node.id && t !== node.id;
    });
  }

  function clearHighlight() {
    if (canvasMode) {
      focusId = null;
      dimmedIds = null;
      requestDraw();
      return;
    }
    d3.selectAll('.node').classed('dimmed', false);
    d3.selectAll('.link').classed('dimmed', false);
  }

  function highlightByText(text) {
    if (!text) {
      clearHighlight();
      return;
    }
    const q = text.toLowerCase();
    const matches = d => d.label.toLowerCase().includes(q) ||
      d.id.toLowerCase().includes(q) ||
      (d.tags && d.tags.some(t => t.toLowerCase().includes(q)));
    let firstMatch = null;
    if (canvasMode) {
      focusId = null;
      dimmedIds = new Set();
      nodesData.forEach(d => {
        if (!matches(d)) dimmedIds.add(d.id);
        else if (!firstMatch) firstMatch = d;
      });
      requestDraw();
    } else {
      d3.selectAll('.node').each(function(d) {
        const match = matches(d);
        d3.select(this).classed('dimmed', !match);
        if (match && !firstMatch) firstMatch = d;
      });
    }

    if (firstMatch) {
      centerOn(firstMatch);
    }
  }

  function centerOn(node) {
    if (!zoomBehavior || !svg || node.x == null) return;
    const transform = d3.zoomIdentity
      .translate(width / 2, height / 2)
      .scale(1.3)
      .translate(-node.x, -node.y);
    svg.transition().duration(500).call(zoomBehavior.transform, transform);
  }

  function zoomBy(factor) {
    if (zoomBehavior && svg) svg.transition().duration(300).call(zoomBehavior.scaleBy, factor);
  }

  function zoomReset() {
    if (zoomBehavior && svg) {
      svg.transition().duration(400).call(zoomBehavior.transform, d3.zoomIdentity);
    }
  }

  function setupGraphControlsUI() {
    const graphContainer = document.getElementById('graph-container');
    if (!graphContainer) return;

    // Panel de control de físicas flotante estilo Obsidian
    const ctrlPanel = document.createElement('div');
    ctrlPanel.id = 'graph-physics-panel';
    ctrlPanel.className = 'graph-physics-panel collapsed';
    const titleTxt = window.I18n ? window.I18n.t('graph_physics_title') : 'Ajustes de Grafo';
    const modeTxt = window.I18n ? window.I18n.t('graph_mode') : 'Modo:';
    const globalTxt = window.I18n ? window.I18n.t('graph_mode_global') : 'Global';
    const localTxt = window.I18n ? window.I18n.t('graph_mode_local') : 'Local';
    const depthTxt = window.I18n ? window.I18n.t('graph_depth') : 'Profundidad:';
    const hopTxt = window.I18n ? window.I18n.t('graph_hop') : 'salto';
    const chargeTxt = window.I18n ? window.I18n.t('graph_charge') : 'Repulsión:';
    const distTxt = window.I18n ? window.I18n.t('graph_dist') : 'Distancia:';
    const orphansTxt = window.I18n ? window.I18n.t('graph_orphans') : 'Mostrar huérfanos';
    const labelsTxt = window.I18n ? window.I18n.t('graph_labels') : 'Mostrar etiquetas';

    ctrlPanel.innerHTML = `
      <button id="toggle-physics-btn" class="physics-toggle-btn" data-i18n-title="graph_physics_title" title="${titleTxt}">⚙️</button>
      <div class="physics-content">
        <h4 data-i18n="graph_physics_title">${titleTxt}</h4>
        <div class="physics-row">
          <label data-i18n="graph_mode">${modeTxt}</label>
          <div class="btn-group">
            <button id="btn-mode-global" class="btn-mini active" data-i18n="graph_mode_global">${globalTxt}</button>
            <button id="btn-mode-local" class="btn-mini" data-i18n="graph_mode_local">${localTxt}</button>
          </div>
        </div>
        <div id="local-depth-row" class="physics-row hidden">
          <label data-i18n="graph_depth">${depthTxt}</label>
          <input type="range" id="slider-depth" min="1" max="4" value="1" />
          <span id="val-depth">1 ${hopTxt}</span>
        </div>
        <div class="physics-row">
          <label data-i18n="graph_charge">${chargeTxt}</label>
          <input type="range" id="slider-charge" min="-400" max="-30" value="-140" />
        </div>
        <div class="physics-row">
          <label data-i18n="graph_dist">${distTxt}</label>
          <input type="range" id="slider-dist" min="30" max="250" value="85" />
        </div>
        <div class="physics-row checkbox">
          <label><input type="checkbox" id="chk-orphans" checked /> <span data-i18n="graph_orphans">${orphansTxt}</span></label>
        </div>
        <div class="physics-row checkbox">
          <label><input type="checkbox" id="chk-labels" checked /> <span data-i18n="graph_labels">${labelsTxt}</span></label>
        </div>
      </div>
    `;
    graphContainer.appendChild(ctrlPanel);

    // Eventos
    document.getElementById('toggle-physics-btn')?.addEventListener('click', () => {
      ctrlPanel.classList.toggle('collapsed');
    });

    document.getElementById('btn-mode-global')?.addEventListener('click', () => {
      graphMode = "global";
      document.getElementById('btn-mode-global').classList.add('active');
      document.getElementById('btn-mode-local').classList.remove('active');
      document.getElementById('local-depth-row').classList.add('hidden');
      window.appLoadGraph?.();
    });

    document.getElementById('btn-mode-local')?.addEventListener('click', () => {
      if (selectedNode) {
        loadLocalGraph(selectedNode.id, localDepth);
      } else {
        alert(window.I18n ? window.I18n.t('select_first_local') : "Selecciona primero una nota para ver su grafo local.");
      }
    });

    document.getElementById('slider-depth')?.addEventListener('input', (e) => {
      const depth = parseInt(e.target.value, 10);
      const hopUnit = depth > 1
        ? (window.I18n ? window.I18n.t('graph_hops') : 'saltos')
        : (window.I18n ? window.I18n.t('graph_hop') : 'salto');
      document.getElementById('val-depth').textContent = `${depth} ${hopUnit}`;
      if (localRootId) loadLocalGraph(localRootId, depth);
    });

    document.getElementById('slider-charge')?.addEventListener('input', (e) => {
      physicsConfig.charge = parseInt(e.target.value, 10);
      if (simulation) {
        simulation.force('charge', d3.forceManyBody().strength(physicsConfig.charge).distanceMax(400));
        simulation.alpha(0.3).restart();
      }
    });

    document.getElementById('slider-dist')?.addEventListener('input', (e) => {
      physicsConfig.distance = parseInt(e.target.value, 10);
      if (simulation) {
        simulation.force('link', d3.forceLink(linksData).id(d => d.id)
          .distance(physicsConfig.distance)
          .strength(physicsConfig.strength));
        simulation.alpha(0.3).restart();
      }
    });

    document.getElementById('chk-orphans')?.addEventListener('change', (e) => {
      physicsConfig.showOrphans = e.target.checked;
      if (graphMode === 'local' && localRootId) {
        loadLocalGraph(localRootId, localDepth);
      } else {
        window.appLoadGraph?.();
      }
    });

    document.getElementById('chk-labels')?.addEventListener('change', (e) => {
      physicsConfig.showLabels = e.target.checked;
      d3.selectAll('.node-label').attr('opacity', e.target.checked ? 1 : 0);
      requestDraw();
    });
  }

  function updateModeIndicator() {
    const btnGlobal = document.getElementById('btn-mode-global');
    const btnLocal = document.getElementById('btn-mode-local');
    const depthRow = document.getElementById('local-depth-row');
    if (btnGlobal && btnLocal) {
      btnGlobal.classList.toggle('active', graphMode === 'global');
      btnLocal.classList.toggle('active', graphMode === 'local');
    }
    if (depthRow) depthRow.classList.toggle('hidden', graphMode !== 'local');
  }

  function updateStatus() {
    const countEl = document.getElementById('status-count');
    if (countEl) {
      const txt = window.I18n
        ? window.I18n.t('status_nodes', { count: nodesData.length, links: linksData.length })
        : `${nodesData.length} nodos · ${linksData.length} aristas`;
      countEl.textContent = txt;
    }
  }

  function setSelectedStatus(text) {
    const selEl = document.getElementById('status-selected');
    if (selEl) selEl.textContent = text;
  }

  function truncate(s, max) {
    if (!s) return '';
    return s.length > max ? s.substring(0, max - 1) + '…' : s;
  }

  function reheat(alpha = 0.3) {
    if (simulation) {
      simulation.alpha(alpha).restart();
    }
  }

  if (window.I18n && window.I18n.onLangChange) {
    window.I18n.onLangChange(() => {
      updateStatus();
      if (!selectedNode) {
        setSelectedStatus(window.I18n.t('status_empty'));
      }
    });
  }

  return {
    init,
    render,
    reheat,
    loadLocalGraph,
    selectNode,
    deselect,
    zoomBy,
    zoomReset,
    highlightByText,
    setSelectedStatus,
    getSelected: () => selectedNode,
  };
})();

window.Graph = Graph;
