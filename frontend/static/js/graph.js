// Motor del grafo — D3 force-directed, simple y robusto
const Graph = (() => {
  let svg, gRoot, simulation, zoomBehavior;
  let nodesData = [], linksData = [];
  let selectedNode = null;
  let onSelectCallback = null;
  let width = 800, height = 600;

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

    // Zoom simple: captura wheel del SVG completo
    zoomBehavior = d3.zoom()
      .scaleExtent([0.1, 6])
      .on('zoom', (event) => {
        gRoot.attr('transform', event.transform);
      });
    svg.call(zoomBehavior);

    // Click en el fondo deselecciona
    svg.on('click', (event) => {
      if (!event.target.closest('.node')) {
        deselect();
      }
    });

    // Resize: recentrar
    let rt = null;
    window.addEventListener('resize', () => {
      if (rt) clearTimeout(rt);
      rt = setTimeout(() => {
        const oldW = width, oldH = height;
        measure();
        if (Math.abs(oldW - width) > 1 || Math.abs(oldH - height) > 1) {
          if (simulation) {
            simulation.force('center', d3.forceCenter(width / 2, height / 2));
            simulation.alpha(0.3).restart();
          }
        }
      }, 250);
    });
  }

  function render(graphData) {
    // Re-medir después de un frame, para asegurar que el CSS ya aplicó
    // y el container tiene dimensiones reales.
    requestAnimationFrame(() => {
      measure();
      doRender(graphData);
    });
  }

  function doRender(graphData) {
    // safety check: si el SVG aun no tiene tamaño, reintentar en el siguiente frame
    if (width < 100 || height < 100) {
      console.warn('SVG size too small, retrying:', width, height);
      requestAnimationFrame(() => {
        measure();
        doRender(graphData);
      });
      return;
    }

    nodesData = graphData.nodes.map(n => ({ ...n }));
    linksData = graphData.edges.map(e => ({ ...e }));

    updateStatus();
    gRoot.selectAll('*').remove();

    // SVG Defs para filtro de brillo neural (glow)
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

    // 1. Enlaces (Líneas de conexión sináptica)
    const linkSel = gRoot.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(linksData)
      .join('line')
      .attr('class', d => `link ${d.kind}`)
      .attr('stroke-width', d => Math.max(1.2, Math.sqrt(d.weight || 1) * 1.5))
      .attr('stroke-opacity', 0.5);

    // 2. Partículas de impulso sináptico (impulsos eléctricos viajando entre nodos)
    const particlesData = [];
    linksData.forEach((link, idx) => {
      // 1 o 2 impulsos por conexión
      particlesData.push({
        id: `p-${idx}-1`,
        link: link,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.006
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

    // Posicion inicial: distribuir orgánicamente
    const n = nodesData.length;
    const cols = Math.ceil(Math.sqrt(n));
    const rows = Math.ceil(n / cols);
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

    // 3. Nodos estilo soma neuronal
    const nodeGroup = gRoot.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodesData, d => d.id)
      .join('g')
      .attr('class', d => `node source-${d.source}`)
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

    // Halo palpitante exterior del nodo
    nodeGroup.append('circle')
      .attr('class', 'node-halo')
      .attr('r', d => 8 + Math.sqrt(d.degree || 0) * 3.5)
      .attr('fill', 'currentColor')
      .attr('opacity', 0.15);

    // Núcleo del nodo con brillo neural
    nodeGroup.append('circle')
      .attr('class', 'node-core')
      .attr('r', d => 5 + Math.sqrt(d.degree || 0) * 2.5)
      .attr('stroke-width', 1.5)
      .attr('filter', 'url(#neural-glow)');

    nodeGroup.append('text')
      .attr('class', 'node-label')
      .attr('x', d => 6 + Math.sqrt(d.degree || 0) * 2.5 + 4)
      .attr('y', 3)
      .text(d => truncate(d.label, 30));

    // Force simulation — Física viva orgánica con deriva constante (respiración neural)
    simulation = d3.forceSimulation(nodesData)
      .force('link', d3.forceLink(linksData)
        .id(d => d.id)
        .distance(85)
        .strength(0.4)
      )
      .force('charge', d3.forceManyBody()
        .strength(-140)
        .distanceMax(350)
      )
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide()
        .radius(d => 16 + Math.sqrt(d.degree || 0) * 3)
        .iterations(3)
      )
      .alpha(0.8)
      .alphaDecay(0.015)       // Enfriamiento suave
      .alphaTarget(0.03)       // Mantiene una pequeña energía de flotación constante (vida/deriva)
      .on('tick', () => {
        // Actualizar posiciones de enlaces
        linkSel
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        // Actualizar impulsos sinápticos viajando por las conexiones
        particleSel.each(function(p) {
          p.progress = (p.progress + p.speed) % 1;
          const sx = p.link.source.x, sy = p.link.source.y;
          const tx = p.link.target.x, ty = p.link.target.y;
          if (sx != null && tx != null) {
            d3.select(this)
              .attr('cx', sx + (tx - sx) * p.progress)
              .attr('cy', sy + (ty - sy) * p.progress);
          }
        });

        // Actualizar nodos
        nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`);
      });

    Graph._simulation = simulation;

    // No aplicar zoom reset agresivo. Solo un heat final.
    setTimeout(() => {
      if (simulation) simulation.alpha(0.3).restart();
    }, 1500);
  }

  function truncate(s, n) {
    return s.length > n ? s.slice(0, n - 1) + '…' : s;
  }

  function makeDrag() {
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
      d3.select(this).classed('pinned', true);
      // evitar que el evento se propague al zoom handler del SVG
      event.sourceEvent.stopPropagation();
    }
    function dragged(event, d) {
      // event.x/event.y ya vienen en coordenadas locales del SVG
      // (D3 v7 aplica el transform del zoom automaticamente)
      d.fx = event.x;
      d.fy = event.y;
    }
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      // El nodo queda pinned donde el usuario lo soltó.
      // Doble-click lo libera.
    }
    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }

  function selectNode(d) {
    selectedNode = d;
    gRoot.selectAll('.node').classed('selected', n => n.id === d.id);
    if (onSelectCallback) onSelectCallback(d);
  }

  function deselect() {
    selectedNode = null;
    gRoot.selectAll('.node').classed('selected', false);
    if (onSelectCallback) onSelectCallback(null);
  }

  function highlightConnections(d) {
    const connectedIds = new Set([d.id]);
    linksData.forEach(l => {
      if (l.source.id === d.id) connectedIds.add(l.target.id);
      if (l.target.id === d.id) connectedIds.add(l.source.id);
    });
    gRoot.selectAll('.node').classed('dim', n => !connectedIds.has(n.id));
    gRoot.selectAll('.link').classed('dim', l =>
      l.source.id !== d.id && l.target.id !== d.id
    );
  }

  function clearHighlight() {
    gRoot.selectAll('.node').classed('dim', false);
    gRoot.selectAll('.link').classed('dim', false);
  }

  function updateStatus() {
    document.getElementById('status-count').textContent =
      `${nodesData.length} nodos · ${linksData.length} conexiones`;
  }

  function setSelectedStatus(text) {
    document.getElementById('status-selected').textContent = text;
  }

  function highlightByText(query) {
    gRoot.selectAll('.node').classed('highlight', false);
    if (!query) return;
    const q = query.toLowerCase();
    const matches = nodesData.filter(n =>
      (n.label || '').toLowerCase().includes(q) ||
      (n.tags || []).some(t => t.toLowerCase().includes(q))
    );
    if (matches.length === 0) return;
    gRoot.selectAll('.node').classed('highlight', n =>
      matches.some(m => m.id === n.id)
    );
    if (matches[0]) {
      const m = matches[0];
      const transform = d3.zoomIdentity
        .translate(width / 2 - m.x, height / 2 - m.y)
        .scale(1.5);
      svg.transition().duration(500).call(zoomBehavior.transform, transform);
    }
  }

  function reheat(alpha = 0.3) {
    if (simulation) simulation.alpha(alpha).restart();
  }

  function zoomBy(factor) {
    if (!zoomBehavior) return;
    svg.transition().duration(250).call(zoomBehavior.scaleBy, factor);
  }

  function zoomReset() {
    if (!zoomBehavior) return;
    svg.transition().duration(400).call(zoomBehavior.transform, d3.zoomIdentity);
  }

  return {
    init, selectNode, deselect, render, highlightByText, reheat,
    setSelectedStatus, zoomBy, zoomReset,
    get simulation() { return Graph._simulation; },
  };
})();