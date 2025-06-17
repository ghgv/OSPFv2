import heapq
from collections import defaultdict

def compute_spf(graph, origin):
    dist = defaultdict(lambda: float('inf'))
    prev = {}
    visited = set()
    dist[origin] = 0
    heap = [(0, origin, None)]
    routing_table = {}
    while heap:
        cost, node, first_hop = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node != origin:
            if first_hop is None:
                first_hop = node
            routing_table[node] = {
                'cost': cost,
                'next_hop': first_hop
            }
        for neighbor, weight in graph.get(node, []):
            if neighbor in visited:
                continue
            alt = cost + weight
            if alt < dist[neighbor]:
                dist[neighbor] = alt
                prev[neighbor] = node
                hop = first_hop if first_hop else neighbor
                heapq.heappush(heap, (alt, neighbor, hop))
    return routing_table