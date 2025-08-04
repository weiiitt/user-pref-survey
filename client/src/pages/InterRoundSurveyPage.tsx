import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import '../styles/LandingPage.css';
import Navbar from '../components/Navbar';
import { submitInterRoundSurvey, checkLoginStatus } from '../utils/api';

function InterRoundSurveyPage() {
    const navigate = useNavigate();
    const [responses, setResponses] = useState({
        mental_demand: 0,
        success_level: 0,
        frustration_level: 0,
        trajectory_choice_ease: 0,
        difference_clarity: 0,
        preference_learning: 0,
        decision_factors: ''
    });
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [error, setError] = useState<string>('');
    const [isChecking, setIsChecking] = useState<boolean>(true);

    // Check login status on page load
    useEffect(() => {
        const checkStatus = async () => {
            try {
                // Check if user is logged in
                const loginStatus = await checkLoginStatus();
                if (!loginStatus.isLoggedIn) {
                    navigate('/');
                    return;
                }
            } catch (error) {
                console.error('Error checking status:', error);
                navigate('/');
            } finally {
                setIsChecking(false);
            }
        };

        checkStatus();
    }, [navigate]);

    const handleResponseChange = (field: string, value: number | string) => {
        setResponses(prev => ({ ...prev, [field]: value }));
        setError('');
    };

    const isFormValid = () => {
        return (
            responses.mental_demand > 0 &&
            responses.success_level > 0 &&
            responses.frustration_level > 0 &&
            responses.trajectory_choice_ease > 0 &&
            responses.difference_clarity > 0 &&
            responses.preference_learning > 0 &&
            responses.decision_factors.trim().length > 0
        );
    };

    const handleSubmitSurvey = async () => {
        setError('');
        
        if (!isFormValid()) {
            setError('Please answer all questions before submitting.');
            return;
        }

        setIsSubmitting(true);
        try {
            await submitInterRoundSurvey(responses);
            navigate('/survey');
        } catch (error) {
            console.error('Error submitting survey:', error);
            setError('Failed to submit survey. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const renderScaleQuestion = (field: string, question: string, scaleOptions: { value: number; label: string }[]) => (
        <div className="survey-form-field">
            <label className="survey-form-label">{question}</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
                {scaleOptions.map(option => (
                    <label key={option.value} style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        cursor: 'pointer',
                        fontSize: '1rem',
                        fontWeight: 'normal'
                    }}>
                        <input
                            type="radio"
                            name={field}
                            value={option.value}
                            checked={responses[field as keyof typeof responses] === option.value}
                            onChange={() => handleResponseChange(field, option.value)}
                            style={{ marginRight: '10px', transform: 'scale(1.2)', accentColor: 'var(--button-color)' }}
                        />
                        {option.label}
                    </label>
                ))}
            </div>
        </div>
    );

    const scaleOptions = [
        { value: 1, label: '1 - Strongly Disagree' },
        { value: 2, label: '2 - Disagree' },
        { value: 3, label: '3 - Neutral' },
        { value: 4, label: '4 - Agree' },
        { value: 5, label: '5 - Strongly Agree' }
    ];

    const demandScaleOptions = [
        { value: 1, label: '1 - Very Low' },
        { value: 2, label: '2 - Low' },
        { value: 3, label: '3 - Moderate' },
        { value: 4, label: '4 - High' },
        { value: 5, label: '5 - Very High' }
    ];

    const successScaleOptions = [
        { value: 1, label: '1 - Not at all' },
        { value: 2, label: '2 - Slightly' },
        { value: 3, label: '3 - Moderately' },
        { value: 4, label: '4 - Very much' },
        { value: 5, label: '5 - Extremely' }
    ];

    // Show loading state while checking status
    if (isChecking) {
        return (
            <div className="landing-page">
                <Navbar />
                <div className='landing-page-content'>
                    <div className='landing-page-content-text'>
                        <h1>Loading...</h1>
                        <p>Checking your progress...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="landing-page">
            <Navbar />
            <div className='landing-page-content'>
                <div className='landing-page-content-text'>
                    <h1>Inter-Round Survey</h1>
                    <p>
                        Please answer the following questions about your experience with the task you just completed.
                        This will help us understand your experience and improve the system.
                    </p>

                    <div className="survey-container container">
                        {renderScaleQuestion(
                            'mental_demand',
                            'How mentally demanding was the task?',
                            demandScaleOptions
                        )}

                        {renderScaleQuestion(
                            'success_level',
                            'How successful were you in accomplishing what you were asked to do?',
                            successScaleOptions
                        )}

                        {renderScaleQuestion(
                            'frustration_level',
                            'How discouraged, irritated, stressed, and annoyed were you?',
                            demandScaleOptions
                        )}

                        {renderScaleQuestion(
                            'trajectory_choice_ease',
                            'It was easy to choose between the trajectories the robot showed me.',
                            scaleOptions
                        )}

                        {renderScaleQuestion(
                            'difference_clarity',
                            'It was easy to tell the difference between the options presented.',
                            scaleOptions
                        )}

                        {renderScaleQuestion(
                            'preference_learning',
                            'Through these questions, the robot was able to learn my preferences.',
                            scaleOptions
                        )}

                        <div className="survey-form-field">
                            <label className="survey-form-label">
                                What factors did you consider when choosing between the two robot trajectories?
                            </label>
                            <p style={{ 
                                fontSize: '0.9rem', 
                                color: 'var(--text-color)', 
                                opacity: 0.8, 
                                marginBottom: '10px' 
                            }}>
                                Please describe in your own words. For example, you might mention safety, efficiency, 
                                terrain type, object avoidance, or any other criteria you used.
                            </p>
                            <textarea
                                value={responses.decision_factors}
                                onChange={(e) => handleResponseChange('decision_factors', e.target.value)}
                                className="survey-form-textarea"
                                placeholder="Please describe the factors you considered..."
                                rows={4}
                            />
                        </div>

                        {error && <div className="login-error">{error}</div>}
                    </div>
                </div>

                <button 
                    onClick={handleSubmitSurvey} 
                    className="start-button"
                    disabled={isSubmitting || !isFormValid()}
                >
                    {isSubmitting ? 'Submitting...' : 'Submit and Continue to Survey'}
                </button>
            </div>
        </div>
    );
}

export default InterRoundSurveyPage;