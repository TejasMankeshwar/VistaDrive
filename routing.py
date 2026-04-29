import osmnx as ox
import networkx as nx
import random
from geopy.distance import distance

NEIGHBORHOODS = {
    "Kothrud": (18.5074, 73.8197),
    "Sinhagad Road": (18.4682, 73.8239),
    "Baner": (18.5590, 73.7868),
    "Viman Nagar": (18.5679, 73.9143),
    "Magarpatta": (18.5147, 73.9275)
}

def get_road_graph(center_point, dist=10000):
    """
    Fetch the road graph within `dist` meters of `center_point`.
    Filters for primary, secondary, and tertiary roads.
    """
    # OSMnx custom filter for wide roads
    custom_filter = '["highway"~"primary|secondary|tertiary"]'
    
    # Using graph_from_point with custom filter
    # simplify=True simplifies the graph's topology
    G = ox.graph_from_point(
        center_point, 
        dist=dist, 
        network_type='drive', 
        custom_filter=custom_filter, 
        simplify=True
    )
    
    return G

def generate_loop_waypoints(start_point, target_distance_km):
    """
    Generate 3 additional waypoints (A, B, C) to form a loop 
    of approximately `target_distance_km` length.
    
    start_point: tuple (lat, lon)
    """
    # S -> A -> B -> C -> S forms a square roughly
    # Each segment should be D/4 length
    segment_length = target_distance_km / 4.0
    
    # Pick a random starting angle
    alpha = random.uniform(0, 360)
    
    # Waypoint A: D/4 at Alpha
    pt_a = distance(kilometers=segment_length).destination(start_point, bearing=alpha)
    
    # Waypoint B: D/4 from A at Alpha + 90
    pt_b = distance(kilometers=segment_length).destination((pt_a.latitude, pt_a.longitude), bearing=(alpha + 90) % 360)
    
    # Waypoint C: D/4 from B at Alpha + 180
    pt_c = distance(kilometers=segment_length).destination((pt_b.latitude, pt_b.longitude), bearing=(alpha + 180) % 360)
    
    return [
        start_point,
        (pt_a.latitude, pt_a.longitude),
        (pt_b.latitude, pt_b.longitude),
        (pt_c.latitude, pt_c.longitude)
    ]

def calculate_scenic_route(G, waypoints, vibe="Scenic"):
    """
    Calculate the shortest path connecting the waypoints in the graph G.
    Returns the node sequence for the loop path.
    """
    # Find the nearest network nodes to the waypoints
    nodes = []
    for pt in waypoints:
        node = ox.distance.nearest_nodes(G, pt[1], pt[0]) # nearest_nodes takes (X, Y) which is (lon, lat)
        nodes.append(node)
        
    # We need a loop, so append the start node to the end
    nodes.append(nodes[0])
    
    weight = 'length'
    
    full_path = []
    total_length_m = 0
    
    try:
        for i in range(len(nodes) - 1):
            u = nodes[i]
            v = nodes[i+1]
            segment_path = nx.shortest_path(G, source=u, target=v, weight=weight)
            
            # calculate segment length
            segment_len = 0
            for k in range(len(segment_path) - 1):
                node_u = segment_path[k]
                node_v = segment_path[k+1]
                edge_data = G.get_edge_data(node_u, node_v)
                if edge_data:
                    min_len = min(e.get('length', 0) for e in edge_data.values())
                    segment_len += min_len
                    
            total_length_m += segment_len
            
            if i < len(nodes) - 2:
                full_path.extend(segment_path[:-1])
            else:
                full_path.extend(segment_path)
    except (nx.NetworkXNoPath, Exception) as e:
        print(f"Pathfinding error: {e}")
        return None, 0
        
    return full_path, total_length_m
