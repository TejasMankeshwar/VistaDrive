from routing import NEIGHBORHOODS, get_road_graph, generate_loop_waypoints, calculate_scenic_route, generate_kml, generate_google_maps_url

print("Testing KML and URL generation...")
center = NEIGHBORHOODS["Kothrud"]
G = get_road_graph(center, dist=5000)

for attempt in range(5):
    waypoints = generate_loop_waypoints(center, 10)
    route_nodes, length = calculate_scenic_route(G, waypoints)
    if route_nodes:
        kml = generate_kml(G, route_nodes)
        url = generate_google_maps_url(waypoints)
        print("KML length:", len(kml))
        print("URL:", url)
        break
