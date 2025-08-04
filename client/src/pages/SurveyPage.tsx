import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchQuestionImages, submitChoice, fetchSurveyConfig, checkPreActivitySurvey } from '../utils/api';
import '../styles/SurveyPage.css';
import Navbar from '../components/Navbar';
import InstructionsPopup from '../components/InstructionsPopup';

interface QuestionData {
	image1: string;
	image2: string;
	test_type: string;
	condition: number;
	question_num: number;
}

function SurveyPage() {
	const navigate = useNavigate();
	const [questionData, setQuestionData] = useState<QuestionData | null>(null);
	const [participantId, setParticipantId] = useState<string>('');
	const [selectedChoice, setSelectedChoice] = useState<number | null>(null);
	const [progress, setProgress] = useState(0);

	const [showInstructions, setShowInstructions] = useState(false);
	const [questionStartTime, setQuestionStartTime] = useState<number | null>(null);
	const [currentTime, setCurrentTime] = useState<number>(0);
	const [isPaused, setIsPaused] = useState(false);
	const [pausedTime, setPausedTime] = useState<number>(0);
	const [lastTestType, setLastTestType] = useState<string | null>(null);
	const [hasShownInstructionsForSession, setHasShownInstructionsForSession] = useState(false);
	const [totalQuestions, setTotalQuestions] = useState(60);
	const [surveyStructure, setSurveyStructure] = useState<{tabletop: Record<number, number>; robot_nav: Record<number, number>}>({tabletop: {}, robot_nav: {}});

	const loadQuestion = async () => {
		try {
			const data = await fetchQuestionImages();
			
			// Check if there's a pending inter-round survey
			if (data.show_inter_round_survey) {
				navigate('/inter-round-survey');
				return;
			}
			
			setQuestionData(data);
			
			// Check if test type changed
			const testTypeChanged = lastTestType !== null && lastTestType !== data.test_type;
			
			setLastTestType(data.test_type);
			
			// Show instructions if test type changed or first time in session
			const willShowInstructions = !hasShownInstructionsForSession || testTypeChanged;
			
			if (willShowInstructions) {
				setShowInstructions(true);
				setHasShownInstructionsForSession(true);
				// Reset timing state - will start when instructions close
				setQuestionStartTime(null);
			} else {
				// Start timing immediately for questions without instructions
				setQuestionStartTime(Date.now());
				setCurrentTime(0);
				setIsPaused(false);
				setPausedTime(0);
			}
			
			// Calculate progress dynamically - only if structure is loaded
			if (Object.keys(surveyStructure.tabletop).length > 0 || Object.keys(surveyStructure.robot_nav).length > 0) {
				let currentProgress = 0;
				if (data.test_type === "tabletop") {
					// Sum questions from completed tabletop conditions + current progress
					const completedTabletop = Object.keys(surveyStructure.tabletop)
						.filter(c => parseInt(c) < data.condition)
						.reduce((sum, c) => sum + surveyStructure.tabletop[parseInt(c)], 0);
					currentProgress = completedTabletop + data.question_num;
				} else {
					// All tabletop + completed robot_nav + current progress
					const tabletopTotal = Object.values(surveyStructure.tabletop).reduce((sum, count) => sum + count, 0);
					const completedRobotNav = Object.keys(surveyStructure.robot_nav)
						.filter(c => parseInt(c) < data.condition)
						.reduce((sum, c) => sum + surveyStructure.robot_nav[parseInt(c)], 0);
					currentProgress = tabletopTotal + completedRobotNav + data.question_num;
				}
				setProgress(currentProgress);
			} else {
				// Fallback calculation while structure is loading
				const fallbackProgress = data.test_type === "tabletop" 
					? data.condition * 10 + data.question_num
					: 30 + data.condition * 10 + data.question_num;
				setProgress(fallbackProgress);
			}
			setSelectedChoice(null);
		} catch (error: any) {
			console.error('Error loading question:', error);
			// Check if it's a user not found or authentication error
			if (error.response?.status === 404 || error.response?.status === 401) {
				window.location.href = '/';
			} else if (error.response?.status === 202) {
				// Inter-round survey pending
				navigate('/inter-round-survey');
			}
		}
	};

	const handleChoiceSelect = async (choice: number) => {
		if (selectedChoice !== null || !questionData || questionStartTime === null || isPaused) return;
		
		setSelectedChoice(choice);
		// Calculate response time
		const responseTime = (Date.now() - questionStartTime) / 1000; // Convert to seconds
		
		try {
			const result = await submitChoice(choice, responseTime);
			
			if (result.completed) {
				// Navigate to thank you page instead of showing alert
				navigate('/thank-you');
				return;
			} else if (result.show_inter_round_survey) {
				// Navigate to inter-round survey
				navigate('/inter-round-survey');
			} else {
				// Wait a moment to show selection, then load next question
				setTimeout(() => {
					loadQuestion();
				}, 1000);
			}
		} catch (error: any) {
			console.error('Error submitting choice:', error);
			// Check if it's a user not found or authentication error
			if (error.response?.status === 404 || error.response?.status === 401) {
				window.location.href = '/';
			}
			setSelectedChoice(null);
		}
	};



	const handleShowInstructions = () => {
		setShowInstructions(true);
	};

	const handleCloseInstructions = () => {
		setShowInstructions(false);
		// Start timing when instructions are closed
		setQuestionStartTime(Date.now());
		setCurrentTime(0);
		setIsPaused(false);
		setPausedTime(0);
	};

	const handlePause = () => {
		if (isPaused) {
			// Resume: adjust start time to account for paused duration
			const pauseDuration = Date.now() - pausedTime;
			setQuestionStartTime(prev => prev ? prev + pauseDuration : Date.now());
			setIsPaused(false);
		} else {
			// Pause: record when we paused
			setPausedTime(Date.now());
			setIsPaused(true);
		}
	};

	useEffect(() => {
		const initializePage = async () => {
			try {
				// Check if pre-activity survey is completed (login is already handled by AuthContext)
				const surveyStatus = await checkPreActivitySurvey();
				if (!surveyStatus.completed) {
					// Pre-activity survey not completed, redirect to pre-activity page
					navigate('/pre-activity');
					return;
				}
				
				// Set participant ID from auth context or session
				// We'll get this from the auth context instead of the API call
				setParticipantId('authenticated'); // Temporary - will be updated by loadQuestion
			} catch (error) {
				console.error('Error checking survey status:', error);
				// Don't redirect on error - let the auth context handle authentication redirects
			}
		};
		
		initializePage();
	}, []); // Remove navigate from dependencies since we only want this to run once

	useEffect(() => {
		// Load first question immediately since we know user is authenticated
		loadQuestion();
	}, []);

	// Timer effect - updates every 100ms when timing is active
	useEffect(() => {
		let interval: NodeJS.Timeout;
		if (questionStartTime !== null && !showInstructions && selectedChoice === null && !isPaused) {
			interval = setInterval(() => {
				setCurrentTime((Date.now() - questionStartTime) / 1000);
			}, 100);
		}
		return () => {
			if (interval) clearInterval(interval);
		};
	}, [questionStartTime, showInstructions, selectedChoice, isPaused]);

	// Reset instructions flag when page loads (user returns to site)
	// Load survey config on mount
	useEffect(() => {
		const loadConfig = async () => {
			try {
				const config = await fetchSurveyConfig();
				setTotalQuestions(config.total_questions);
				setSurveyStructure(config.structure);
			} catch (error) {
				console.error('Error loading survey config:', error);
				// Keep default values on error
			}
		};
		
		setHasShownInstructionsForSession(false);
		loadConfig();
	}, []);




	if (!questionData) {
		return <div>Error loading question data</div>;
	}

	return (
		<div className="survey-container">
			<Navbar onShowInstructions={handleShowInstructions} timer={questionStartTime !== null && !showInstructions ? currentTime : null} onPause={handlePause} isPaused={isPaused} />
			{/* Progress Bar */}
			<div className="progress-section">
				<div className="progress-info">
					<span>{questionData.test_type === "tabletop" ? "Table-top" : "Robot Navigation"} - Condition {questionData.condition + 1}</span>
					<span>{progress} / {totalQuestions}</span>
				</div>
				<div className="progress-bar">
					<div 
						className="progress-fill" 
						style={{ width: `${(progress / totalQuestions) * 100}%` }}
					></div>
				</div>
			</div>

			{/* Question Content */}
			<div className="question-content">
				<h2>Question {questionData.question_num + 1}</h2>
				<p>Click on an image to select your preferred trajectory</p>
				
				<div className={`images-section ${selectedChoice !== null ? 'processing' : ''} ${isPaused ? 'paused' : ''}`}>
					<div 
						className={`image-container ${selectedChoice === 0 ? 'selected' : ''}`}
						onClick={() => handleChoiceSelect(0)}
					>
						<img src={questionData.image1} alt="Route Option 1" />
						<div className="image-label">Option 1</div>
					</div>
					<div 
						className={`image-container ${selectedChoice === 1 ? 'selected' : ''}`}
						onClick={() => handleChoiceSelect(1)}
					>
						<img src={questionData.image2} alt="Route Option 2" />
						<div className="image-label">Option 2</div>
					</div>
				</div>
			</div>
			<InstructionsPopup 
				isVisible={showInstructions}
				onClose={handleCloseInstructions}
				testType={questionData.test_type}
			/>
		</div>
	);

}

export default SurveyPage;