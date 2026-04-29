from routing import NEIGHBORHOODS, get_road_graph, generate_loop_waypoints, calculate_scenic_route

print("Testing Kothrud with retries...")
center = NEIGHBORHOODS["Kothrud"]
print(f"Center: {center}")
G = get_road_graph(center, dist=5000)
print(f"Graph nodes: {len(G.nodes)}")

route_nodes = None
target_distance = 10

for attempt in range(5):
    waypoints = generate_loop_waypoints(center, target_distance)
    print(f"Attempt {attempt+1}: waypoints: {waypoints}")
    route_nodes, length = calculate_scenic_route(G, waypoints)
    if route_nodes:
        print(f"Success! Route length: {length}m, Nodes: {len(route_nodes)}")
        break
    else:
        print("Failed to find path. Retrying...")

if not route_nodes:
    print("Failed all attempts.")
