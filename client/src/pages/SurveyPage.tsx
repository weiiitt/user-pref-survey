import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchQuestionImages, submitChoice, fetchSurveyConfig, checkPreActivitySurvey, fetchUserProgress } from '../utils/api';
import '../styles/SurveyPage.css';
import Navbar from '../components/Navbar';
import InstructionsPopup from '../components/InstructionsPopup';
import type { User } from '../contexts/AuthContext';

interface QuestionData {
	image1: string;
	image2: string;
	test_type: string;
	condition: number;
	question_num: number;
}

interface SurveyPageProps {
  user: User;
}

function SurveyPage({ user }: SurveyPageProps) {
	const navigate = useNavigate();
	const [questionData, setQuestionData] = useState<QuestionData | null>(null);
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
	

	const loadQuestion = async () => {
		try {
			const data = await fetchQuestionImages();
			
			// Check if there's a pending inter-round survey
			if (data.show_inter_round_survey) {
				navigate('/inter-round-survey');
				return;
			}
			
			// Set question data first
			setQuestionData(data);
			
			// Then update progress based on the new data
			if (totalQuestions > 0) {
				fetchUserProgress().then(progressData => {
					const currentProgress = Math.round(progressData.percent_answered * totalQuestions);
					setProgress(currentProgress);
				});
			}

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
			
			setSelectedChoice(null);
		} catch (error: any) {
			console.error('Error loading question:', error);
			// Check if it's a user not found or authentication error
			if (error.response?.status === 404 || error.response?.status === 401) {
				navigate('/');
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
				// 1. Check pre-activity survey status
				const surveyStatus = await checkPreActivitySurvey();
				if (!surveyStatus.completed) {
					navigate('/pre-activity');
					return;
				}

				// 2. Load survey configuration
				const config = await fetchSurveyConfig();
				setTotalQuestions(config.total_questions);
				
				setHasShownInstructionsForSession(false);

				// 3. Load the first question
				await loadQuestion();

			} catch (error) {
				console.error('Error initializing survey page:', error);
				// Handle critical errors, e.g., redirect to an error page or show a message
			}
		};
		
		initializePage();
	}, [user]); // Re-initialize if user changes, though this shouldn't happen on this page

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



	return (
		<div className="survey-container">
			{!questionData ? (
				<div>Loading... (if this persists, please refresh the page)</div>
			) : (
				<>
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
				</>
			)}
		</div>
	);

}

export default SurveyPage;