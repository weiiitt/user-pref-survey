import { useEffect, useState } from 'react';
import { fetchQuestionImages, submitChoice, checkLoginStatus, submitInterRoundSurvey } from '../utils/api';
import '../styles/SurveyPage.css';
import Navbar from '../components/Navbar';

interface QuestionData {
	image1: string;
	image2: string;
	test_type: string;
	condition: number;
	question_num: number;
	question_start_time: number;
}

function SurveyPage() {
	const [questionData, setQuestionData] = useState<QuestionData | null>(null);
	const [participantId, setParticipantId] = useState<string>('');
	const [selectedChoice, setSelectedChoice] = useState<number | null>(null);
	const [progress, setProgress] = useState(0);
	const [showInterRoundSurvey, setShowInterRoundSurvey] = useState(false);
	const totalQuestions = 60; // 2 test types × 3 conditions × 10 questions

	const loadQuestion = async () => {
		try {
			const data = await fetchQuestionImages();
			
			// Check if there's a pending inter-round survey
			if (data.show_inter_round_survey) {
				setShowInterRoundSurvey(true);
				return;
			}
			
			// Override the backend timestamp with current time to handle page refreshes/navigation
			const freshData = {
				...data,
				question_start_time: Date.now() / 1000  // Convert to seconds to match backend
			};
			setQuestionData(freshData);
			
			// Calculate progress: (condition * 10 + question_num) for current test + completed test questions
			const currentProgress = data.test_type === "tabletop" 
				? data.condition * 10 + data.question_num
				: 30 + data.condition * 10 + data.question_num;
			setProgress(currentProgress);
			setSelectedChoice(null);
		} catch (error: any) {
			console.error('Error loading question:', error);
			// Check if it's a user not found or authentication error
			if (error.response?.status === 404 || error.response?.status === 401) {
				window.location.href = '/';
			} else if (error.response?.status === 202) {
				// Inter-round survey pending
				setShowInterRoundSurvey(true);
			}
		}
	};

	const handleChoiceSelect = async (choice: number) => {
		if (selectedChoice !== null || !questionData) return;
		
		setSelectedChoice(choice);
		try {
			const result = await submitChoice(choice, questionData.question_start_time);
			
			if (result.completed) {
				alert('Survey completed! Thank you for participating.');
			} else if (result.show_inter_round_survey) {
				// Show inter-round survey
				setShowInterRoundSurvey(true);
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

	const handleInterRoundSurveyComplete = async () => {
		try {
			await submitInterRoundSurvey();
			setShowInterRoundSurvey(false);
			// Load next question after survey completion
			loadQuestion();
		} catch (error: any) {
			console.error('Error submitting inter-round survey:', error);
			if (error.response?.status === 404 || error.response?.status === 401) {
				window.location.href = '/';
			}
		}
	};

	useEffect(() => {
		const initializePage = async () => {
			try {
				const loginStatus = await checkLoginStatus();
				if (loginStatus.isLoggedIn && loginStatus.participantId) {
					setParticipantId(loginStatus.participantId);
				} else {
					// Redirect to landing page if not logged in
					window.location.href = '/';
				}
			} catch (error) {
				console.error('Error checking login status:', error);
				window.location.href = '/';
			}
		};
		
		initializePage();
	}, []);

	useEffect(() => {
		if (participantId) {
			loadQuestion();
		}
	}, [participantId]);


	if (showInterRoundSurvey) {
		return (
			<div className="landing-page">
				<Navbar />
				<div className='landing-page-content'>
					<div className='landing-page-content-text'>
						<h1>Inter-Round Survey</h1>
						<p>
							<b>After completing the form below, click the button at the bottom to continue to the next set of questions.</b>
						</p>

						<div className="google-form-container">
							<iframe
								src="https://docs.google.com/forms/d/e/1FAIpQLSe-psvsxo3dLWyIt_waPOcTnRh7VAXOopoy8oWjSHGMtvUJbg/viewform?embedded=true"
								width={640}
								height={1816}
								style={{ border: 0, margin: 0 }}
							>
								Loading…
							</iframe>
						</div>

						<p>
							After completing the form above, click the button below to continue to the next set of questions.
						</p>
					</div>

					<button onClick={handleInterRoundSurveyComplete} className="start-button">
						Continue to Next Set
					</button>
				</div>
			</div>
		);
	}

	if (!questionData) {
		return <div>Error loading question data</div>;
	}

	return (
		<div className="survey-container">
			<Navbar  />
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
				
				<div className={`images-section ${selectedChoice !== null ? 'processing' : ''}`}>
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
		</div>
	);

}

export default SurveyPage;