from __future__ import annotations
import networkx as nx
import numpy as np
from .network import WSNNetwork


def hierarchical_path(net: WSNNetwork, src: int, chs: list[int], assignment: np.ndarray, risk: np.ndarray, router: str) -> list[int | None]:
    if not net.alive[src] or not chs:
        return []
    ch = int(assignment[src])
    if ch < 0:
        return []
    path: list[int | None] = [src]
    if src != ch:
        if net.distance(src, ch) > net.radio_range:
            return []
        path.append(ch)
    bg = net.backbone_graph(chs, risk, router)
    sink = net.n
    if ch not in bg or not nx.has_path(bg, ch, sink):
        return []
    bp = nx.shortest_path(bg, ch, sink, weight="weight")
    for node in bp[1:]:
        path.append(None if node == sink else int(node))
    return path

