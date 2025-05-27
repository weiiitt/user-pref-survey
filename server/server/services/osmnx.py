import osmnx as ox
import random
import networkx as nx
import heapq
import pandas as pd
import numpy as np

class OSMnxService:
    def __init__(self, x, y, dist=600, batch_size=16, pause=1.0, verbose=False):
        self.x = x
        self.y = y
        self.dist = dist
        self.batch_size = batch_size
        self.pause = pause
        self.verbose = verbose
        self.graph = ox.graph_from_point((self.x, self.y), dist=self.dist, network_type='walk')
        # self._add_elevation_data()
        self._add_travel_times()
        
    def _add_elevation_data(self):
        """Add elevation data to the graph."""
        node_points = pd.Series({n: f"{d['y']:.6f},{d['x']:.6f}" for n, d in self.graph.nodes(data=True)})
        n_calls = int(np.ceil(len(node_points) / self.batch_size))
        domain = "https://api.open-elevation.com"
        url_base = "https://api.open-elevation.com/api/v1/lookup?locations={}"

        if self.verbose:
            print(f"Requesting node elevations from {domain!r} in {n_calls} request(s)")
            print("Number of nodes: ", len(node_points))

        results = []
        for i in range(0, len(node_points), self.batch_size):
            chunk = node_points.iloc[i : i + self.batch_size]
            locations = "|".join(chunk)
            url = url_base.format(locations)

            try:
                # Pass the pause parameter to _elevation_request
                response_json = ox.elevation._elevation_request(url, pause=self.pause)
            except Exception as e:
                print(f"Error with request {url}: {e}")
                break
                
            if "results" in response_json and len(response_json["results"]) > 0:
                results.extend(response_json["results"])
            else:
                print(f"Warning: No results or unexpected response for chunk {i//self.batch_size + 1}: {response_json}")
                pass

            if self.verbose and (i // self.batch_size) % 10 == 0:
                print(f"Batch {i//self.batch_size + 1}/{n_calls} processed, {len(results)} results so far")

        # Sanity check that all our vectors have the same number of elements
        if not (len(results) == len(node_points)):
            err_msg = (f"Graph has {len(self.graph.nodes):,} nodes ({len(node_points)} points sent) "
                    f"but received {len(results):,} results from {domain!r}.")
            # If response_json is from the last call, it might be useful for debugging.
            # Consider logging the full list of URLs or problematic chunks if this error occurs.
            # err_msg += f"\nLast response (may not be the only problematic one): {response_json}"
            raise Exception(err_msg)

        # Add elevation as an attribute to the nodes
        # Ensure nodes in df_elev are aligned with nodes in graph for direct assignment
        df_elev = pd.DataFrame(index=node_points.index)
        df_elev["elevation"] = [result["elevation"] for result in results] # Assumes results are in order
        
        nx.set_node_attributes(self.graph, name="elevation", values=df_elev["elevation"].to_dict())
        if self.verbose:
            print(f"Added 'elevation' attribute from {domain!r} to all {len(self.graph.nodes())} nodes.")
        
        # Add edge grades and absolute edge grades
        graph_with_grades = ox.elevation.add_edge_grades(self.graph)
        if self.verbose:
            print("Added 'grade' and 'grade_abs' attributes to edges.")
            
        self.graph = graph_with_grades
        
    def _add_travel_times(self):
        # impute speed on all edges missing data
        self.graph = ox.add_edge_speeds(self.graph, fallback=5)

        # calculate travel time (seconds) for all edges
        self.graph = ox.add_edge_travel_times(self.graph)
        
    def _calculate_bearing(self, lat1, lon1, lat2, lon2):
        """
        Calculate the bearing between two lat/lon coordinates.
        """
        d_lon = np.radians(lon2 - lon1)
        lat1, lat2 = np.radians(lat1), np.radians(lat2)

        x = np.sin(d_lon) * np.cos(lat2)
        y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(d_lon)
        bearing = np.degrees(np.arctan2(x, y))
        return (bearing + 360) % 360  # Normalize to 0-360 degrees
    
        
    def _A_star(self, start, end, heuristic_fn, edge_weight_fn):
        """
        Implementation of A* algorithm to find the shortest path between two nodes.
        
        Args:
            graph: NetworkX graph
            start: Starting node
            end: Destination node
            heuristic_fn: Function that estimates distance from node to goal
            edge_weight_fn: Function that returns the weight of an edge
        
        Returns:
            List of nodes representing the shortest path
        """
        # Priority queue for open nodes
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        # For node n, came_from[n] is the node immediately preceding it on the path
        came_from = {}
        
        # For node n, g_score[n] is the cost of the cheapest path from start to n
        g_score = {node: float('inf') for node in self.graph.nodes()}
        g_score[start] = 0
        
        # For node n, f_score[n] = g_score[n] + heuristic(n)
        f_score = {node: float('inf') for node in self.graph.nodes()}
        f_score[start] = heuristic_fn(self.graph, start, end)
        
        # Nodes that have been visited
        closed_set = set()
        
        while open_set:
            # Get node with lowest f_score
            current_f_score, current = heapq.heappop(open_set)
            
            if current == end:
                # Reconstruct path
                path_nodes = [current]
                path_edges = []
                
                while current in came_from:
                    prev_node, edge_key = came_from[current]
                    path_nodes.append(prev_node)
                    path_edges.append((prev_node, current, edge_key))
                    current = prev_node
                    
                # Return reversed path
                return path_nodes[::-1], path_edges[::-1]
            
            closed_set.add(current)
            
            # Check all neighbors
            for neighbor in self.graph.neighbors(current):
                if neighbor in closed_set:
                    continue
                
                # Calculate tentative g_score
                min_edge_weight = float('inf')
                for edge_key in self.graph.get_edge_data(current, neighbor):
                    edge_weight = edge_weight_fn(self.graph, current, neighbor, edge_key)
                    if edge_weight < min_edge_weight:
                        min_edge_weight = edge_weight
                tentative_g_score = g_score[current] + min_edge_weight
                
                if tentative_g_score < g_score[neighbor]:
                    # This path is better than any previous one
                    
                    # Find the best edge to use (the one that gave us this tentative_g_score)
                    best_edge_key = None
                    best_edge_weight = float('inf')
                    
                    for edge_key in self.graph.get_edge_data(current, neighbor):
                        edge_weight = edge_weight_fn(self.graph, current, neighbor, edge_key)
                        if edge_weight < best_edge_weight:
                            best_edge_weight = edge_weight
                            best_edge_key = edge_key
                    
                    # Store both the previous node and the specific edge used
                    came_from[neighbor] = (current, best_edge_key)
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + heuristic_fn(self.graph, neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        # No path found
        return None

    def _heuristic_distance(self, node, goal):
        """
        Heuristic function that estimates the distance from node to goal.
        In this case, using Euclidean distance between the nodes.
        
        Args:
            graph: NetworkX graph
            node: Current node
            goal: Goal node
            
        Returns:
            Estimated distance to goal
        """
        # Get node coordinates
        node_y = self.graph.nodes[node]['y']
        node_x = self.graph.nodes[node]['x']
        goal_y = self.graph.nodes[goal]['y']
        goal_x = self.graph.nodes[goal]['x']
        
        # Calculate Euclidean distance
        return ((node_y - goal_y) ** 2 + (node_x - goal_x) ** 2) ** 0.5

    def _edge_weight_elevation(self, u, v, edge_key=None, elevation_weight=1.0):
        """
        Function to calculate edge weight considering both distance and elevation change.
        
        Args:
            graph: NetworkX graph
            u: Source node
            v: Target node
            edge_key: Specific edge key (for multigraph support)
            elevation_weight: Factor to control importance of elevation change
            
        Returns:
            Combined weight of the edge
        """
        if edge_key is not None:
            # Get specific edge
            edge_data = self.graph.get_edge_data(u, v)[edge_key]
            length = edge_data.get('length', 0)
        else:
            # Find minimum length edge (default behavior)
            min_length = float('inf')
            for edge_data in self.graph.get_edge_data(u, v).values():
                if edge_data.get('length', float('inf')) < min_length:
                    min_length = edge_data.get('length')
            length = min_length
        
        # Calculate elevation values
        elevation_u = self.graph.nodes[u].get('elevation', 0)
        elevation_v = self.graph.nodes[v].get('elevation', 0)
        # print(elevation_u, elevation_v)
        
        # Calculate grade (elevation change / distance)
        elevation_change = elevation_v - elevation_u
        grade = abs(elevation_change / length) if length > 0 else 0
        
        # Combined weight: distance + (elevation_weight * grade)
        return length + (elevation_weight * grade)
        
    def get_graph(self):
        """Get the graph with elevation data."""
        return self.graph
    
    def count_turns(self, path):
        """
        Count the number of left and right turns in a path.
        :param path: A list of node IDs representing a path
        :return: (tuple) Number of left and right turns
        """
        left_turns = 0
        right_turns = 0

        # Loop through consecutive nodes in the path
        for i in range(len(path) - 2):
            # Get the coordinates of the three consecutive nodes
            node1, node2, node3 = path[i], path[i+1], path[i+2]
            x1, y1 = self.graph.nodes[node1]['x'], self.graph.nodes[node1]['y']
            x2, y2 = self.graph.nodes[node2]['x'], self.graph.nodes[node2]['y']
            x3, y3 = self.graph.nodes[node3]['x'], self.graph.nodes[node3]['y']

            # Calculate bearings for the two edges
            bearing1 = self._calculate_bearing(y1, x1, y2, x2)
            bearing2 = self._calculate_bearing(y2, x2, y3, x3)

            # Compute the change in bearings
            angle_change = (bearing2 - bearing1 + 360) % 360
            if 240 < angle_change < 300:  # Right turn
                right_turns += 1
            elif 60 < angle_change < 120: # Left turn
                left_turns += 1

        return left_turns, right_turns
    
    def get_random_source_destination(self):
        """Get a random source and destination node from the graph."""
        origin = random.choice(list(self.graph.nodes()))
        destination = random.choice(list(self.graph.nodes()))
        return origin, destination
    
    def get_two_shortest_paths(self, origin, destination):
        """Get the two shortest paths between two nodes."""
        # First path - shortest by length
        route1 = nx.shortest_path(self.graph, origin, destination, weight='length')

        # Second path - add penalty to edges in the first path
        G_temp = self.graph.copy()
        for u, v in zip(route1[:-1], route1[1:]):
            # Find the edge with minimum length
            min_length = float('inf')
            for edge_data in self.graph.get_edge_data(u, v).values():
                if edge_data.get('length', float('inf')) < min_length:
                    min_length = edge_data.get('length')
            
            # Add penalty to all edges between these nodes
            for k in G_temp.get_edge_data(u, v):
                G_temp[u][v][k]['length'] *= 1.5  # 50% penalty

        # Find second path with penalties
        route2 = nx.shortest_path(G_temp, origin, destination, weight='length')
        
        return route1, route2
    
    
osmnx_service = OSMnxService(40.008279, -105.268985, dist=500)