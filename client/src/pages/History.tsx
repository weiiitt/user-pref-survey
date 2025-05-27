import { useEffect, useState } from 'react';
import { fetchPreviousAnswers } from '../utils/api';
import type { PreviousAnswer } from '../types/APIResponses';
import MapDisplay from '../components/MapDisplay';

import surveyStyles from '../styles/Survey.module.css';
import type { RouteResponse } from '../types/APIResponses';
import "../styles/History.css"

function HistoryPage() {
    const [answers, setAnswers] = useState<PreviousAnswer[]>([]);

    useEffect(() => {
        const loadPreviousAnswers = async () => {
            try {
                const response = await fetchPreviousAnswers();
                setAnswers(response.previous_answers);
            } catch (error) {
                console.error("Error fetching history:", error);
            }
        };

        loadPreviousAnswers();
    }, []);

    if (answers.length === 0) {
        return <div>No history found.</div>;
    }

    return (
        <div className="history-page">
            <h1>Your Previous Choices</h1>
            {answers.map((answer, index) => {
                // Original presented routes from the server might not exactly match RouteResponse type
                // We need to transform them if necessary, especially for MapDisplay
                const presentedDetailsA = answer.presented_routes_details?.[0];
                const presentedDetailsB = answer.presented_routes_details?.[1];

                if (!presentedDetailsA || !presentedDetailsB) {
                    return (
                        <div key={answer.preference_id} className="history-item">
                            <h2>Answer {answers.length - index} (Data incomplete)</h2>
                            <p>Could not display this answer as route data is missing.</p>
                        </div>
                    );
                }

                // Transform to RouteResponse for MapDisplay and consistent access
                // Assuming presentedDetailsX has all the fields of RouteResponse.route directly,
                // and also source/destination if needed (though MapDisplay only needs route.coordinates)
                const routeAForDisplay: RouteResponse = {
                    route: {
                        id: presentedDetailsA.id, // Add id here
                        coordinates: presentedDetailsA.coordinates,
                        distance: presentedDetailsA.distance,
                        elevationGain: presentedDetailsA.elevationGain,
                        avgGrade: presentedDetailsA.avgGrade,
                        leftTurns: presentedDetailsA.leftTurns,
                        rightTurns: presentedDetailsA.rightTurns,
                        travelTime: presentedDetailsA.travelTime,
                    },
                    // Source and destination might not be directly available in presented_routes_details
                    // in the same structure. For MapDisplay, only route.coordinates is critical.
                    // If source/destination are needed for other parts of display, adjust accordingly.
                    source: presentedDetailsA.source_coordinates ? { id: presentedDetailsA.source_node_id || 'unknown', coordinates: presentedDetailsA.source_coordinates } : { id: 'unknown', coordinates: [0, 0] }, // Provide defaults
                    destination: presentedDetailsA.destination_coordinates ? { id: presentedDetailsA.destination_node_id || 'unknown', coordinates: presentedDetailsA.destination_coordinates } : { id: 'unknown', coordinates: [0, 0] }, // Provide defaults
                };

                const routeBForDisplay: RouteResponse = {
                    route: {
                        id: presentedDetailsB.id, // Add id here
                        coordinates: presentedDetailsB.coordinates,
                        distance: presentedDetailsB.distance,
                        elevationGain: presentedDetailsB.elevationGain,
                        avgGrade: presentedDetailsB.avgGrade,
                        leftTurns: presentedDetailsB.leftTurns,
                        rightTurns: presentedDetailsB.rightTurns,
                        travelTime: presentedDetailsB.travelTime,
                    },
                    source: presentedDetailsB.source_coordinates ? { id: presentedDetailsB.source_node_id || 'unknown', coordinates: presentedDetailsB.source_coordinates } : { id: 'unknown', coordinates: [0, 0] }, // Provide defaults
                    destination: presentedDetailsB.destination_coordinates ? { id: presentedDetailsB.destination_node_id || 'unknown', coordinates: presentedDetailsB.destination_coordinates } : { id: 'unknown', coordinates: [0, 0] }, // Provide defaults
                };

                return (
                    <div key={answer.preference_id} className="history-item">
                        <h2>Answer {answers.length - index} (Taken on: {answer.created_at ? new Date(answer.created_at).toLocaleDateString() : 'N/A'})</h2>
                        <div className="history-item-content">
                            <div className="history-item-map">
                                <MapDisplay routes={[routeAForDisplay, routeBForDisplay]} hoveredRoute={null} />
                            </div>
                            <div className="history-item-routes">
                                <div
                                    className={`${surveyStyles.surveyOptionsInfoItem} ${surveyStyles.surveyOptionRouteA} ${answer.selected_generated_route_id === presentedDetailsA.id ? surveyStyles.selectedRouteCard : ''}`}
                                >
                                    <h3>Blue Route {answer.selected_generated_route_id === presentedDetailsA.id ? "(Selected)" : ""}</h3>
                                    <ul>
                                        <li>Distance: {presentedDetailsA.distance.toFixed(2)} meters</li>
                                        <li>Average Grade: {presentedDetailsA.avgGrade.toFixed(2)}%</li>
                                        <li>Total Turns: {presentedDetailsA.leftTurns + presentedDetailsA.rightTurns}</li>
                                        <li>Travel Time: {presentedDetailsA.travelTime.toFixed(2)} seconds</li>
                                    </ul>
                                </div>
                                <div
                                    className={`${surveyStyles.surveyOptionsInfoItem} ${surveyStyles.surveyOptionRouteB} ${answer.selected_generated_route_id === presentedDetailsB.id ? surveyStyles.selectedRouteCard : ''}`}
                                >
                                    <h3>Red Route {answer.selected_generated_route_id === presentedDetailsB.id ? "(Selected)" : ""}</h3>
                                    <ul>
                                        <li>Distance: {presentedDetailsB.distance.toFixed(2)} meters</li>
                                        <li>Average Grade: {presentedDetailsB.avgGrade.toFixed(2)}%</li>
                                        <li>Total Turns: {presentedDetailsB.leftTurns + presentedDetailsB.rightTurns}</li>
                                        <li>Travel Time: {presentedDetailsB.travelTime.toFixed(2)} seconds</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

export default HistoryPage;
