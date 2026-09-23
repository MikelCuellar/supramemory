// Motor del grafo — D3 force-directed brain-like layout
// Features: drag, zoom, pan, click-to-pin, doble-click-release, búsqueda, panel lateral
const Graph = (() => {
  let svg, gRoot, simulation;
  let nodesData = [], linksData = [];
  let selectedNode = null;
  let onSelectCallback = null;

  function init(onSelect) {
    onSelectCallback = onSelect;
    svg = d3.select('#graph-svg');
    gRoot = svg.select('#graph-root');

    // Zoom + pan
    const zoom = d3.zoom()
      .scaleExtent([0.1, 8])
      .filter((event) => {
        // Permitir pan/drag sobre el fondo, no sobre nodos
        if (event.type === 'wheel') return true;
        return !event.target.closest('.node');
      })
      .on('zoom', (event) => {
        gRoot.attr('transform', event.transform);
      });
    svg.call(zoom);

    // Click en el fondo deselecciona
    svg.on('click', (event) => {
      if (event.target === svg.node()) {
        deselect();
      }
    });

    // Resize handler
    window.addEventListener('resize', () => {
      if (simulation) {
        simulation.alpha(0.3).restart();
      }
    });
  }

  function render(graphData) {
    nodesData = graphData.nodes.map(n => ({ ...n }));
    linksData = graphData.edges.map(e => ({ ...e }));

    updateStatus();

    // Limpiar
    gRoot.selectAll('*').remove();

    // Crear grupos
    const linkSel = gRoot.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(linksData)
      .join('line')
      .attr('class', d => `link ${d.kind}`)
      .attr('stroke-width', d => Math.max(1, Math.sqrt(d.weight || 1) * 1.2));

    const nodeGroup = gRoot.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodesData, d => d.id)
      .join('g')
      .attr('class', d => `node source-${d.source}`)
      .call(makeDrag())
      .on('click', (event, d) => {
        event.stopPropagation();
        selectNode(d);
      })
      .on('dblclick', (event, d) => {
        event.stopPropagation();
        // Doble click libera nodo pinned
        d.fx = null;
        d.fy = null;
        d3.select(event.currentTarget).classed('pinned', false);
        if (simulation) simulation.alpha(0.5).restart();
      })
      .on('mouseenter', (event, d) => {
        highlightConnections(d);
      })
      .on('mouseleave', () => {
        clearHighlight();
      });

    nodeGroup.append('circle')
      .attr('r', d => 5 + Math.sqrt(d.degree || 0) * 3)
      .attr('stroke-width', 1.5);

    nodeGroup.append('text')
      .attr('class', 'node-label')
      .attr('x', d => 5 + Math.sqrt(d.degree || 0) * 3 + 4)
      .attr('y', 3)
      .text(d => d.label);

    // Force simulation — brain-like: repulsión fuerte, links cortos
    simulation = d3.forceSimulation(nodesData)
      .force('link', d3.forceLink(linksData)
        .id(d => d.id)
        .distance(70)
        .strength(0.3)
      )
      .force('charge', d3.forceManyBody()
        .strength(-280)            // repulsión fuerte
        .distanceMax(400)
      )
      .force('center', d3.forceCenter(
        window.innerWidth / 2,
        (window.innerHeight - 72) / 2
      ))
      .force('collide', d3.forceCollide()
        .radius(d => 8 + Math.sqrt(d.degree || 0) * 3 + 4)
        .iterations(2)
      )
      .alpha(1)
      .alphaDecay(0.012)
      .on('tick', () => {
        linkSel
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
        nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`);
      });

    // Guardar sim en variable de closure para acceso externo
    Graph._simulation = simulation;
  }

  function makeDrag() {
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
      d3.select(this).classed('pinned', true);
    }
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      // Dejar pinned donde el usuario lo soltó
      // Para liberar: doble click
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
    document.getElementById('status-count').textContent = `${nodesData.length} nodos · ${linksData.length} conexiones`;
  }

  function setSelectedStatus(text) {
    document.getElementById('status-selected').textContent = text;
  }

  function highlightByText(query) {
    gRoot.selectAll('.node').classed('highlight', false);
    if (!query) return;
    const q = query.toLowerCase();
    const matches = nodesData.filter(n =>
      n.label.toLowerCase().includes(q) ||
      (n.tags || []).some(t => t.toLowerCase().includes(q))
    );
    if (matches.length === 0) return;
    gRoot.selectAll('.node').classed('highlight', n =>
      matches.some(m => m.id === n.id)
    );
    // Centrar en el primer match
    if (matches[0]) {
      const m = matches[0];
      const svgNode = svg.node();
      const transform = d3.zoomIdentity
        .translate(window.innerWidth / 2 - m.x, (window.innerHeight - 72) / 2 - m.y)
        .scale(1.5);
      svg.transition().duration(500).call(d3.zoom().transform, transform);
    }
  }

  function reheat(alpha = 0.3) {
    if (simulation) simulation.alpha(alpha).restart();
  }

  return {
    init, selectNode, deselect, render, highlightByText, reheat,
    setSelectedStatus,
    get simulation() { return Graph._simulation; },
  };
})();