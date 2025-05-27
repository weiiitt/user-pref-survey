import { useEffect, useState } from 'react';
import Survey from '../components/Survey';
import ProgressIndicator from '../components/ProgressIndicator';
import { fetchRandomRoutes, saveRoutePreference } from '../utils/api';
import type { RouteResponse } from '../types/APIResponses';
import '../styles/SurveyPage.css';

interface AnswersState {
	[key: number]: number | null; // Route id
}

interface RouteState {
	[key: number]: RouteResponse[];
}

function SurveyPage() {
	const [questionNumber, setQuestionNumber] = useState(1);
	const [answers, setAnswers] = useState<AnswersState>({});
	const [routes, setRoutes] = useState<RouteState>({});
	const [fetchingRoutes, setFetchingRoutes] = useState(true);
	const totalQuestions = 10;

	const fetchRoutes = async (questionNum: number) => {
		setFetchingRoutes(true);
		try {
			const new_routes = await fetchRandomRoutes();
			setRoutes(prevRoutes => ({
				...prevRoutes,
				[questionNum]: new_routes.routes
			}));
		} catch (error) {
			console.error('Error fetching routes:', error);
		} finally {
			setFetchingRoutes(false);
		}
	}

	// Handler to update the answers state
	const handleAnswerChange = (questionNum: number, answer: number | null) => {
		if (answer) {
			saveRoutePreference(answer, routes[questionNum].map(route => route.route.id));
		}

		setAnswers(prevAnswers => ({
			...prevAnswers,
			[questionNum]: answer,
		}));
	};

	const handleNext = () => {
		// Only fetch routes if they don't exist for the next question
		if (!routes[questionNumber + 1]) {
			fetchRoutes(questionNumber + 1);
		}
		if (questionNumber < totalQuestions) {
			setQuestionNumber(questionNumber + 1);
		}
	};

	const handlePrevious = () => {
		if (questionNumber > 1) {
			setQuestionNumber(questionNumber - 1);
		}
	};

	useEffect(() => {
		if (Object.keys(routes).length === 0) {
			fetchRoutes(questionNumber);
		}
	}, []);

	return (
		<>
			{fetchingRoutes && (
				<div className="loading-overlay">
					<div className="loading-spinner"></div>
					<h2>Generating routes...</h2>
				</div>
			)}
			{/* Pass the current answer and the handler to SurveyPage */}
			<Survey
				questionNumber={questionNumber}
				selectedAnswer={answers[questionNumber] || null}
				routes={routes[questionNumber]}
				onAnswerChange={handleAnswerChange}
			/>
			<div className="question-navigation">
				<button onClick={handlePrevious} disabled={questionNumber === 1}>Previous</button>
				{/* Pass answers to ProgressIndicator if needed for visualization later */}
				<ProgressIndicator
					totalQuestions={totalQuestions}
					currentQuestion={questionNumber}
				// answers={answers} // Uncomment and implement in ProgressIndicator if needed
				/>
				<button onClick={handleNext} disabled={questionNumber === totalQuestions}>Next</button>
			</div>
		</>
	)

}

export default SurveyPage;