import styles from '../styles/Survey.module.css'
import type { RouteResponse } from '../types/APIResponses';
import MapDisplay from './MapDisplay'
import { useEffect, useState } from 'react';

interface SurveyProps { 
    questionNumber: number;
    selectedAnswer: number | null;
    routes: RouteResponse[] | undefined;
    onAnswerChange: (questionNum: number, answer: number | null) => void;
}

function Survey({ questionNumber, selectedAnswer, routes, onAnswerChange }: SurveyProps) {
    const [hoveredRoute, setHoveredRoute] = useState<string | null>(null);

    const handleOptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onAnswerChange(questionNumber, parseInt(e.target.value));
    };

    useEffect(() => {
        console.log(hoveredRoute);
    }, [hoveredRoute]);

    return (
        <div className={styles.surveyPage}>
            <div className={styles.surveyHeader}>
                <h1>Question {questionNumber}</h1>
            </div>
            <div className={styles.surveyContainer}>
                <div className={styles.surveyContent}>
                   {routes && <MapDisplay routes={routes} hoveredRoute={hoveredRoute} />}
                </div>
                <div className={styles.surveyOptions}>
                    <div className={styles.surveyOptionsInfo}>
                        <div 
                            className={`${styles.surveyOptionsInfoItem} ${styles.surveyOptionRouteA}`}
                            onMouseEnter={() => setHoveredRoute('option1')}
                            onMouseLeave={() => setHoveredRoute(null)}
                        >
                            <h3>Blue Route</h3>
                            <ul>
                                <li>Distance: {routes?.[0].route.distance.toFixed(2)} meters</li>
                                <li>Average Grade: {routes?.[0].route.avgGrade.toFixed(2)}%</li>
                                <li>Total Turns: {routes?.[0] && routes?.[0].route.leftTurns + routes?.[0].route.rightTurns}</li>
                                <li>Travel Time: {routes?.[0].route.travelTime.toFixed(2)} seconds</li>
                            </ul>
                        </div>
                        <div 
                            className={`${styles.surveyOptionsInfoItem} ${styles.surveyOptionRouteB}`}
                            onMouseEnter={() => setHoveredRoute('option2')}
                            onMouseLeave={() => setHoveredRoute(null)}
                        >
                            <h3>Red Route</h3>
                            <ul>
                                <li>Distance: {routes?.[1].route.distance.toFixed(2)} meters</li>
                                <li>Positive Grade: {routes?.[1].route.positiveGrade.toFixed(2)}%</li>
                                <li>Negative Grade: {routes?.[1].route.negativeGrade.toFixed(2)}%</li>
                                <li>Total Turns: {routes?.[1] && routes?.[1].route.leftTurns + routes?.[1].route.rightTurns}</li>
                                <li>Travel Time: {routes?.[1].route.travelTime.toFixed(2)} seconds</li>
                            </ul>
                        </div>
                    </div>
                    <div className={styles.surveySelection}>
                        <h3>Please select a route:</h3>
                        <div className={styles.radioGroup}>
                            <label>
                                <input 
                                    type="radio" 
                                    name="surveyOption" 
                                    value={routes?.[0].route.id} 
                                    checked={selectedAnswer === routes?.[0].route.id}
                                    onChange={handleOptionChange}
                                />
                                Blue Route
                            </label>
                            <label>
                                <input 
                                    type="radio" 
                                    name="surveyOption" 
                                    value={routes?.[1].route.id} 
                                    checked={selectedAnswer === routes?.[1].route.id}
                                    onChange={handleOptionChange}
                                />
                                Red Route
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Survey;