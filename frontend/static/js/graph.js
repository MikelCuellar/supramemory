// Motor del grafo — D3 force-directed con soporte para Grafo Global, Grafo Local y Controles de Física en Vivo
const Graph = (() => {
  let svg, gRoot, simulation, zoomBehavior;
  let nodesData = [], linksData = [];
  let selectedNode = null;
  let onSelectCallback = null;
  let width = 800, height = 600;
  let particleAnimId = null;

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
      .on('zoom', (event) => {
        gRoot.attr('transform', event.transform);
      });
    svg.call(zoomBehavior);

    svg.on('click', (event) => {
      if (!event.target.closest('.node')) {
        deselect();
      }
    });

    let rt = null;
    window.addEventListener('resize', () => {
      if (rt) clearTimeout(rt);
      rt = setTimeout(() => {
        measure();
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

    updateStatus();
    gRoot.selectAll('*').remove();

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

    // 2. Impulsos Sinápticos
    const particlesData = [];
    linksData.forEach((link, idx) => {
      particlesData.push({
        id: `p-${idx}`,
        link: link,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.005
      });
    });

    const particleSel = gRoot.append('g')
      .attr('class', 'synapses')
      .selectAll('circle')
      .data(particlesData)
      .join('circle')
      .attr('class', 'synapse-particle')
      .attr('r', 2.5)
      .attr('fill', '#00f3ff')
      .attr('filter', 'url(#neural-glow)');

    // Posición inicial orgánica
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
      .attr('r', d => (d.id === localRootId ? 9 : 5) + Math.sqrt(d.degree || 0) * 2.5)
      .attr('stroke-width', d => (d.id === localRootId ? 2.5 : 1.5))
      .attr('filter', 'url(#neural-glow)');

    // Text labels
    nodeGroup.append('text')
      .attr('class', 'node-label')
      .attr('x', d => 6 + Math.sqrt(d.degree || 0) * 2.5 + 4)
      .attr('y', 3)
      .attr('opacity', physicsConfig.showLabels ? 1 : 0)
      .text(d => truncate(d.label, 30));

    // Force simulation
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
      .alphaDecay(0.02)
      .on('tick', () => {
        linkSel
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`);
      });

    // Animación continua e independiente de partículas sinápticas
    if (particleAnimId) cancelAnimationFrame(particleAnimId);
    function stepParticles() {
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
      particleAnimId = requestAnimationFrame(stepParticles);
    }
    if (particlesData.length > 0) {
      stepParticles();
    }
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
    if (onSelectCallback) onSelectCallback(node);
  }

  function deselect() {
    selectedNode = null;
    d3.selectAll('.node').classed('selected', false);
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

    d3.selectAll('.node').classed('dimmed', d => !connected.has(d.id));
    d3.selectAll('.link').classed('dimmed', d => {
      const s = d.source.id || d.source;
      const t = d.target.id || d.target;
      return s !== node.id && t !== node.id;
    });
  }

  function clearHighlight() {
    d3.selectAll('.node').classed('dimmed', false);
    d3.selectAll('.link').classed('dimmed', false);
  }

  function highlightByText(text) {
    if (!text) {
      clearHighlight();
      return;
    }
    const q = text.toLowerCase();
    let firstMatch = null;
    d3.selectAll('.node').each(function(d) {
      const match = d.label.toLowerCase().includes(q) ||
        d.id.toLowerCase().includes(q) ||
        (d.tags && d.tags.some(t => t.toLowerCase().includes(q)));
      d3.select(this).classed('dimmed', !match);
      if (match && !firstMatch) firstMatch = d;
    });

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
    ctrlPanel.innerHTML = `
      <button id="toggle-physics-btn" class="physics-toggle-btn" title="Ajustes de Grafo y Físicas">⚙️</button>
      <div class="physics-content">
        <h4>Ajustes de Grafo</h4>
        <div class="physics-row">
          <label>Modo:</label>
          <div class="btn-group">
            <button id="btn-mode-global" class="btn-mini active">Global</button>
            <button id="btn-mode-local" class="btn-mini">Local</button>
          </div>
        </div>
        <div id="local-depth-row" class="physics-row hidden">
          <label>Profundidad:</label>
          <input type="range" id="slider-depth" min="1" max="4" value="1" />
          <span id="val-depth">1 salto</span>
        </div>
        <div class="physics-row">
          <label>Repulsión:</label>
          <input type="range" id="slider-charge" min="-400" max="-30" value="-140" />
        </div>
        <div class="physics-row">
          <label>Distancia:</label>
          <input type="range" id="slider-dist" min="30" max="250" value="85" />
        </div>
        <div class="physics-row checkbox">
          <label><input type="checkbox" id="chk-orphans" checked /> Mostrar huérfanos</label>
        </div>
        <div class="physics-row checkbox">
          <label><input type="checkbox" id="chk-labels" checked /> Mostrar etiquetas</label>
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
        alert("Selecciona primero una nota para ver su grafo local.");
      }
    });

    document.getElementById('slider-depth')?.addEventListener('input', (e) => {
      const depth = parseInt(e.target.value, 10);
      document.getElementById('val-depth').textContent = `${depth} salto${depth > 1 ? 's' : ''}`;
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
        simulation.force('link', d3.forceLink(linksData).id(d => d.id).distance(physicsConfig.distance));
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
      countEl.textContent = `${nodesData.length} nodos · ${linksData.length} aristas`;
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
