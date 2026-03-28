import type { AccidentRecord } from './accidents';

export interface RouteNode {
  lat: number;
  lon: number;
  risk: number;
}

export interface RouteResult {
  safest_route: RouteNode[];
  shortest_route: RouteNode[];
  safe_score: number;
  short_score: number;
}

function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth radius in km
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dlat = toRad(lat2 - lat1);
  const dlon = toRad(lon2 - lon1);
  const a =
    Math.sin(dlat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dlon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

interface GraphNode {
  id: string;
  lat: number;
  lon: number;
  risk: number;
}

interface Edge {
  to: string;
  safeCost: number;
  shortCost: number;
}

export function getSafestRoute(
  startLat: number,
  startLon: number,
  endLat: number,
  endLon: number,
  records: AccidentRecord[]
): RouteResult {
  // Build node list
  const nodes: GraphNode[] = [{ id: 'start', lat: startLat, lon: startLon, risk: 0 }];

  for (const r of records) {
    nodes.push({
      id: String(r.id),
      lat: r.latitude,
      lon: r.longitude,
      risk: r.risk
    });
  }
  nodes.push({ id: 'end', lat: endLat, lon: endLon, risk: 0 });

  // Build adjacency list
  const adj: Map<string, Edge[]> = new Map();
  for (const n of nodes) adj.set(n.id, []);

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const ni = nodes[i];
      const nj = nodes[j];
      const d = haversine(ni.lat, ni.lon, nj.lat, nj.lon);
      const isEndpoint = ni.id === 'start' || ni.id === 'end' || nj.id === 'start' || nj.id === 'end';
      if (d < 5.0 || isEndpoint) {
        const avgRisk = (ni.risk + nj.risk) / 2;
        const safeCost = d + avgRisk * 0.1;
        const shortCost = d;
        adj.get(ni.id)!.push({ to: nj.id, safeCost, shortCost });
        adj.get(nj.id)!.push({ to: ni.id, safeCost, shortCost });
      }
    }
  }

  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  function dijkstra(useSafe: boolean): { path: string[]; cost: number } {
    // Min-heap via sorted array for simplicity (data sets are small enough)
    type QItem = [number, string, string[]];
    const pq: QItem[] = [[0, 'start', []]];
    const visited = new Set<string>();

    while (pq.length > 0) {
      pq.sort((a, b) => a[0] - b[0]);
      const [currCost, currId, path] = pq.shift()!;

      if (visited.has(currId)) continue;
      visited.add(currId);
      const newPath = [...path, currId];

      if (currId === 'end') return { path: newPath, cost: currCost };

      for (const edge of adj.get(currId) ?? []) {
        if (!visited.has(edge.to)) {
          const c = useSafe ? edge.safeCost : edge.shortCost;
          pq.push([currCost + c, edge.to, newPath]);
        }
      }
    }
    return { path: [], cost: Infinity };
  }

  const { path: safePath, cost: safeScore } = dijkstra(true);
  const { path: shortPath, cost: shortScore } = dijkstra(false);

  const toNodes = (path: string[]): RouteNode[] =>
    path.map(id => {
      const n = nodeMap.get(id)!;
      return { lat: n.lat, lon: n.lon, risk: n.risk };
    });

  return {
    safest_route: toNodes(safePath),
    shortest_route: toNodes(shortPath),
    safe_score: safeScore,
    short_score: shortScore
  };
}
