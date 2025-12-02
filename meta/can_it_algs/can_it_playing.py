import numpy as np

import networkx as nx
import matplotlib.pyplot as plt


# Firstly, let's generate some random PPGs


def random_PPG(V_0_s, V_s, A_s):
    # V_0_s is number of vertices in V_0
    # V_s is total number of vertices
    # A_s is total number of arcs

    # returns arc list, connectivity table, and vertex depth list

    A = [] # [arc index] = [tail vertex index, head vertex index]

    A_table = [] # [tail index][head index] = 0/1 depending on arc existence
    for x in range(V_s):
        A_table.append([])
        for y in range(V_s):
            A_table[x].append(0)

    # Firstly, we make sure that every vertex is reachable from some primal vertex, by building a multi-tree naively

    leaf_vertices = list(range(V_0_s))

    vertex_depth = [0] * V_0_s # distances from closest elements in V_0

    for A_i in range(V_s - V_0_s):
        # pick a random leaf vertex and append a new vertex, which will succeed it.
        cur_leaf_i = np.random.randint(V_0_s)

        new_vertex_index = V_0_s + A_i
        A.append([leaf_vertices[cur_leaf_i], new_vertex_index])
        A_table[leaf_vertices[cur_leaf_i]][new_vertex_index] = 1

        # we note down the depth of the new vertex
        vertex_depth.append(vertex_depth[leaf_vertices[cur_leaf_i]] + 1)

        leaf_vertices[cur_leaf_i] = new_vertex_index # replace the leaf

    # Now we add random arcs until the number of arcs fits

    while(len(A) < A_s):
        # tail can lie wherever, head mustn't be in V_0
        random_tail = np.random.randint(V_s)
        random_head = V_0_s + np.random.randint(V_s - V_0_s)

        # we only add the arc if it doesn't already exist
        if A_table[random_tail][random_head] == 0:
            A.append([random_tail, random_head])
            A_table[random_tail][random_head] = 1

            # we check if vertex depth changes
            vertex_depth[random_head] = min(vertex_depth[random_head], vertex_depth[random_tail] + 1)
    return(A, A_table, vertex_depth)


V_0_s = 3
V_s = 10
A_s = 12

A, A_table, vertex_depth = random_PPG(V_0_s, V_s, A_s)





G = nx.DiGraph()
G.add_nodes_from(list(range(V_s)))
G.add_edges_from(A)

# Extract colors in node order
node_colors = ["red"] * V_0_s + ["blue"] * (V_s - V_0_s)

# Layout
layout_spacing = []
col_occupancy = [0] * (1 + max(vertex_depth))
for v_i in range(V_s):
    layout_spacing.append((vertex_depth[v_i], -col_occupancy[vertex_depth[v_i]] * 2))
    col_occupancy[vertex_depth[v_i]] += 1
pos = layout_spacing


# Draw
fig, ax = plt.subplots()

# Draw nodes
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors)
nx.draw_networkx_labels(G, pos, ax=ax, font_color = "white")

# Draw edges with different curvature depending on (u,v)
for (u, v) in G.edges():
    rad = 0.2 if (u, v) == (0,1) else -0.2
    nx.draw_networkx_edges(
        G, pos, edgelist=[(u,v)], ax=ax,
        connectionstyle=f'arc3,rad={rad}',
        arrows=True
    )
"""nx.draw(
    G, pos,
    with_labels=True,
    node_color=node_colors,
    arrows=True,
    arrowstyle='-|>',
    arrowsize=20
)"""

plt.show()

