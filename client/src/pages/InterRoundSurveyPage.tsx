import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import '../styles/InterRoundSurveyPage.css';
import Navbar from '../components/Navbar';
import { submitInterRoundSurvey } from '../utils/api';

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

    // Component initialization (login is already handled by AuthContext)
    useEffect(() => {
        // Just set the component as ready since authentication is handled by AuthContext
        setIsChecking(false);
    }, []); // Remove navigate from dependencies since we only want this to run once

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

    const renderScaleQuestion = (field: string, question: string, scaleOptions: { value: number }[]) => (
        <div className="survey-form-field">
            <label className="survey-form-label">{question}</label>
            <div className="survey-radio-group">
                <div className="survey-radio-group-left">
                    <p>Not at all</p>
                </div>
                {scaleOptions.map(option => (
                    <label key={option.value} className="survey-radio-option">
                        <input
                            type="radio"
                            name={field}
                            value={option.value}
                            checked={responses[field as keyof typeof responses] === option.value}
                            onChange={() => handleResponseChange(field, option.value)}
                            className="survey-radio-input"
                        />
                        {option.value}
                    </label>
                ))}
                <div className="survey-radio-group-right">
                    <p>Extremely</p>
                </div>
            </div>
        </div>
    );

    const scaleOptions = [
        { value: 1 },
        { value: 2 },
        { value: 3 },
        { value: 4 },
        { value: 5 },
        { value: 6 },
        { value: 7 }
    ];

    // Show loading state while checking status
    if (isChecking) {
        return (
            <div className="page-layout">
                <Navbar />
                <div className='page-content'>
                    <div className='page-content-text'>
                        <h1>Loading...</h1>
                        <p>Checking your progress...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="page-layout">
            <Navbar />
            <div className='page-content'>
                <div className='page-content-text'>
                    <h1>Inter-Round Survey</h1>
                    <p>
                        Please answer the following questions about your experience with the task you just completed.
                        This will help us understand your experience and improve the system.
                    </p>

                    <div className="survey-container container">
                        {renderScaleQuestion(
                            'mental_demand',
                            'How mentally demanding was the task?',
                            scaleOptions
                        )}

                        {renderScaleQuestion(
                            'success_level',
                            'How successful were you in accomplishing what you were asked to do?',
                            scaleOptions
                        )}

                        {renderScaleQuestion(
                            'frustration_level',
                            'How discouraged, irritated, stressed, or annoyed were you?',
                            scaleOptions
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
                            <p className="survey-form-hint">
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