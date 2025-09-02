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
	time_taken?: number[];
}

function SurveyPage() {
	const navigate = useNavigate();
	const [questionData, setQuestionData] = useState<QuestionData | null>(null);
	const [selectedChoice, setSelectedChoice] = useState<number | null>(null);
	const [progress, setProgress] = useState(0);
	const [loadError, setLoadError] = useState(false);

	const [showInstructions, setShowInstructions] = useState(false);
	const [questionStartTime, setQuestionStartTime] = useState<number | null>(null);
	const [currentTime, setCurrentTime] = useState<number>(0);
	const [isPaused, setIsPaused] = useState(false);
	const [pausedTime, setPausedTime] = useState<number>(0);
	const [lastTestType, setLastTestType] = useState<string | null>(null);
	const [hasShownInstructionsForSession, setHasShownInstructionsForSession] = useState(false);
	const [totalQuestions, setTotalQuestions] = useState(30);
	const [structure, setStructure] = useState<Record<string, Record<number, number>>>({});

	const loadQuestion = async () => {
		try {
			setLoadError(false);
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
		
			setSelectedChoice(null);

			
		} catch (error: any) {
			console.error('Error loading question:', error);
			// Do not redirect on errors; show inline error state
			if (error.response?.status === 202) {
                // Inter-round survey pending
                navigate('/inter-round-survey');
            }
			setLoadError(true);
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
				// Wait a moment to show selection, then load next question (which will update progress)
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

	// Combined initialization effect - runs once on mount
	useEffect(() => {
		const initializePage = async () => {
			try {
				// Check if pre-activity survey is completed
				const surveyStatus = await checkPreActivitySurvey();
				if (!surveyStatus.completed) {
					navigate('/pre-activity');
					return;
				}
				
				// Load survey config
				const config = await fetchSurveyConfig();
				setTotalQuestions(config.total_questions);
				setStructure(config.structure);
				
				// Reset instructions flag
				setHasShownInstructionsForSession(false);
				
				// Load first question
				loadQuestion();
				
			} catch (error) {
				console.error('Error initializing survey page:', error);
			}
		};
		
		initializePage();
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

	// Calculate progress when structure or questionData updates
	useEffect(() => {
		if (!questionData || !structure.tabletop || !structure.robot_nav) return;

		const conditionNum = questionData.condition;
		const questionNum = questionData.question_num;
		const testType = questionData.test_type;
		
		let currentProgress = 0;
		
		if (testType === "tabletop") {
			// Add questions from completed tabletop conditions
			Object.keys(structure.tabletop).forEach(cond => {
				const condNum = parseInt(cond);
				if (condNum < conditionNum) {
					currentProgress += structure.tabletop[condNum];
				}
			});
			// Add current question progress
			currentProgress += questionNum + 1; // +1 because questionNum is 0-indexed
		} else if (testType === "robot_nav") {
			// Add ALL tabletop questions (completed)
			currentProgress += Object.values(structure.tabletop).reduce((sum, count) => sum + count, 0);
			
			// Add questions from completed robot_nav conditions
			Object.keys(structure.robot_nav).forEach(cond => {
				const condNum = parseInt(cond);
				if (condNum < conditionNum) {
					currentProgress += structure.robot_nav[condNum];
				}
			});
			// Add current question progress
			currentProgress += questionNum + 1; // +1 because questionNum is 0-indexed
		}
		
		setProgress(currentProgress);
	}, [structure, questionData]);



	return (
		<div className="survey-container">
			{!questionData ? (
				loadError ? (
					<div className="question-content">
						<h2>Couldn’t load options</h2>
						<p>Try refreshing the page. If this problem persists, contact Yi Shiuan using the contact info on the landing page.</p>
					</div>
				) : (
					<div>Loading...</div>
				)
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
						
						{loadError ? (
							<div>
								<h3>Couldn’t load options</h3>
								<p>Try refreshing the page. If this problem persists, please contact the principal investigator, Yi-Shiuan Tung, at yi-shiuan.tung@colorado.edu.</p>
							</div>
						) : (
							<div className={`images-section ${selectedChoice !== null ? 'processing' : ''} ${isPaused ? 'paused' : ''}`}>
								<div 
									className={`image-container ${selectedChoice === 0 ? 'selected' : ''}`}
									onClick={() => handleChoiceSelect(0)}
								>
									<img src={questionData.image1} alt="Route Option 1" />
									<div className="image-label">{`Option 1${questionData.time_taken && questionData.time_taken.length > 0 ? `: ${questionData.time_taken[0].toFixed(1)}s` : ''}`}</div>
								</div>
								<div 
									className={`image-container ${selectedChoice === 1 ? 'selected' : ''}`}
									onClick={() => handleChoiceSelect(1)}
								>
									<img src={questionData.image2} alt="Route Option 2" />
									<div className="image-label">{`Option 2${questionData.time_taken && questionData.time_taken.length > 1 ? `: ${questionData.time_taken[1].toFixed(1)}s` : ''}`}</div>
								</div>
							</div>
						)}
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