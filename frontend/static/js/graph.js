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

    const linkSel = gRoot.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(linksData)
      .join('line')
      .attr('class', d => `link ${d.kind}`)
      .attr('stroke-width', d => Math.max(0.5, Math.sqrt(d.weight || 1) * 0.8))
      .attr('stroke-opacity', 0.4);

    // Posicion inicial: distribuir en grilla centrada
    const n = nodesData.length;
    const cols = Math.ceil(Math.sqrt(n));
    const rows = Math.ceil(n / cols);
    const cellW = Math.min((width * 0.7) / cols, 140);
    const cellH = Math.min((height * 0.7) / rows, 100);
    const gridW = cols * cellW;
    const gridH = rows * cellH;
    const startX = (width - gridW) / 2 + cellW / 2;
    const startY = (height - gridH) / 2 + cellH / 2;
    console.log('Grid layout:', { n, cols, rows, cellW, cellH, startX, startY, width, height });
    nodesData.forEach((nd, i) => {
      const c = i % cols;
      const r = Math.floor(i / cols);
      nd.x = startX + c * cellW + (Math.random() - 0.5) * cellW * 0.3;
      nd.y = startY + r * cellH + (Math.random() - 0.5) * cellH * 0.3;
      nd.vx = 0;
      nd.vy = 0;
    });

    const nodeGroup = gRoot.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodesData, d => d.id)
      .join('g')
      .attr('class', d => `node source-${d.source}`)
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .on('click', (event, d) => {
        event.stopPropagation();
        selectNode(d);
      })
      .on('mouseenter', (event, d) => highlightConnections(d))
      .on('mouseleave', () => clearHighlight());

    nodeGroup.append('circle')
      .attr('r', d => 4 + Math.sqrt(d.degree || 0) * 2.5)
      .attr('stroke-width', 1.2);

    nodeGroup.append('text')
      .attr('class', 'node-label')
      .attr('x', d => 4 + Math.sqrt(d.degree || 0) * 2.5 + 3)
      .attr('y', 3)
      .text(d => truncate(d.label, 30));

    // Force simulation
    simulation = d3.forceSimulation(nodesData)
      .force('link', d3.forceLink(linksData)
        .id(d => d.id)
        .distance(50)
        .strength(0.4)
      )
      .force('charge', d3.forceManyBody()
        .strength(-120)
        .distanceMax(250)
      )
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide()
        .radius(d => 8 + Math.sqrt(d.degree || 0) * 2.5)
        .iterations(2)
      )
      .alpha(1)
      .alphaDecay(0.025)
      .on('tick', () => {
        linkSel
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
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