import streamlit as st
import folium
from streamlit_folium import st_folium
import osmnx as ox
from streamlit_geolocation import streamlit_geolocation

# Local imports
from routing import (NEIGHBORHOODS, get_road_graph, generate_loop_waypoints, 
                     calculate_scenic_route, generate_kml, generate_google_maps_url)

st.set_page_config(page_title="VistaDrive", layout="wide")

st.title("VistaDrive: Scenic Route Generator")
st.markdown("Generate long-drive loops within city limits, prioritizing wide and paved roads.")

# --- Sidebar UI ---
with st.sidebar:
    st.header("Route Settings")
    
    location_type = st.radio("Start Location", ["Current Location (GPS)", "Pre-defined Neighborhood"])
    
    selected_neighborhood = None
    if location_type == "Current Location (GPS)":
        st.markdown("Click below to fetch your current location:")
        loc = streamlit_geolocation()
    else:
        selected_neighborhood = st.selectbox(
            "Starting Neighborhood",
            options=list(NEIGHBORHOODS.keys())
        )
        loc = None
    
    target_distance = st.slider(
        "Target Distance (km)",
        min_value=10,
        max_value=100,
        value=30,
        step=5
    )
    
    vibe = st.selectbox(
        "Vibe",
        options=["Scenic", "Open Road", "Night Drive"]
    )
    
    generate_btn = st.button("Generate Route", type="primary")

# Cache the graph fetching to avoid redundant downloads
@st.cache_resource(show_spinner=False)
def fetch_graph(center_point, dist):
    return get_road_graph(center_point, dist)

if generate_btn:
    if location_type == "Current Location (GPS)":
        if loc and loc.get('latitude') is not None and loc.get('longitude') is not None:
            center_point = (loc['latitude'], loc['longitude'])
            loc_name = "your location"
        else:
            st.error("Please allow location access and click the GPS button before generating the route.")
            st.stop()
    else:
        center_point = NEIGHBORHOODS[selected_neighborhood]
        loc_name = selected_neighborhood
    
    # Calculate required graph radius based on target distance
    # The loop roughly spans D/4 from the center, but diagonal can be larger.
    # Safe radius: D * 1000 / 2 meters
    graph_radius = max(10000, int((target_distance * 1000) / 2))
    
    with st.spinner(f"Fetching road network around {loc_name}... (Radius: {graph_radius}m)"):
        try:
            G = fetch_graph(center_point, dist=graph_radius)
        except Exception as e:
            st.error(f"Error fetching graph: {e}")
            st.stop()
            
    with st.spinner("Generating waypoints and pathfinding..."):
        route_nodes = None
        total_length_m = 0
        
        # Retry up to 5 times with different random angles
        for attempt in range(5):
            waypoints = generate_loop_waypoints(center_point, target_distance)
            route_nodes, total_length_m = calculate_scenic_route(G, waypoints, vibe)
            
            # Validation: if path found and length is roughly > 70% of target, we accept it
            if route_nodes and total_length_m > (target_distance * 1000 * 0.7):
                break
            else:
                route_nodes = None # reset and retry
        
        if not route_nodes:
            st.error("Could not find a valid loop path after multiple attempts. Try a different distance or neighborhood.")
        else:
            total_km = total_length_m / 1000.0
            estimated_time_hours = total_km / 40.0 # 40 km/h avg speed
            
            # --- Metrics ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Distance", f"{total_km:.2f} km")
            # Convert time to hours and minutes
            hrs = int(estimated_time_hours)
            mins = int((estimated_time_hours - hrs) * 60)
            col2.metric("Estimated Time", f"{hrs}h {mins}m")
            # Mock scenic percentage for MVP
            scenic_pct = 75 if vibe == "Scenic" else (60 if vibe == "Open Road" else 50)
            col3.metric("Scenic Percentage", f"{scenic_pct}%")
            
            # --- Map ---
            route_map = folium.Map(location=center_point, zoom_start=12)
            
            # --- Android Export ---
            st.subheader("Export to Android")
            exp_col1, exp_col2 = st.columns(2)
            
            # KML Download
            kml_data = generate_kml(G, route_nodes)
            exp_col1.download_button(
                label="📥 Download Route (.kml)",
                data=kml_data,
                file_name="vistadrive_route.kml",
                mime="application/vnd.google-earth.kml+xml",
                help="Download this file and open it in Google Earth or Google My Maps on your Android phone."
            )
            
            # Google Maps URL
            gmaps_url = generate_google_maps_url(waypoints)
            exp_col2.link_button(
                "🗺️ Open in Google Maps", 
                url=gmaps_url,
                help="Opens Google Maps directions with the main waypoints. Note: Google may alter the exact streets between waypoints."
            )
            
            st.markdown("---")
            
            # Plot the start point
            folium.Marker(
                location=center_point,
                popup="Start/End",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(route_map)
            
            # Optionally plot other waypoints
            for i, wp in enumerate(waypoints[1:], 1):
                folium.CircleMarker(
                    location=wp,
                    radius=5,
                    color="blue",
                    fill=True,
                    popup=f"Waypoint {i}"
                ).add_to(route_map)
                
            # Plot the route manually extracting node coordinates to be safe across OSMnx versions
            route_coords = []
            for node_id in route_nodes:
                lat = G.nodes[node_id]['y']
                lon = G.nodes[node_id]['x']
                route_coords.append([lat, lon])
                
            folium.PolyLine(
                route_coords,
                color="blue",
                weight=5,
                opacity=0.8
            ).add_to(route_map)
            
            # Display map
            st_folium(route_map, width=1000, height=600, returned_objects=[])
else:
    st.info("Select your preferences in the sidebar and click 'Generate Route'.")
