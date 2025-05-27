export interface RouteResponse {
    // Main route data
    route: {
      id: number;
      response_id: number;
      coordinates: [number, number][]; // Array of [lat, lng] pairs
      distance: number;               // Total distance in meters
      elevationGain: number;          // Total elevation gain in meters
      avgGrade: number;               // Average absolute grade of the route
      leftTurns: number;              // Number of left turns
      rightTurns: number;             // Number of right turns
      travelTime: number;             // Total travel time in seconds
    };
    
    // Source and destination details
    source: {
      coordinates: [number, number];
    };
    
    destination: {
      coordinates: [number, number];
    };
}

export interface HistoryRouteDetail {
  id: number;
  route_guid: string;
  coordinates: [number, number][];
  distance: number;
  elevationGain: number;
  avgGrade: number;
  leftTurns: number;
  rightTurns: number;
  travelTime: number;
  source_node_id?: string;
  source_coordinates?: [number, number];
  destination_node_id?: string;
  destination_coordinates?: [number, number];
}

export interface PreviousAnswer {
  preference_id: number;
  user_uuid: string;
  selected_generated_route_id: number;
  selected_route_details: HistoryRouteDetail | null;
  presented_routes_ids: number[];
  presented_routes_details: HistoryRouteDetail[];
  created_at: string | null;
}