import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import '../styles/InterRoundSurveyPage.css';
import Navbar from '../components/Navbar';
import { submitInterRoundSurvey, fetchInterRoundQuestions } from '../utils/api';
import type { InterRoundQuestion } from '../utils/api';

function InterRoundSurveyPage() {
    const navigate = useNavigate();
    const [responses, setResponses] = useState<Record<string, number | string>>({});
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [error, setError] = useState<string>('');
    const [isChecking, setIsChecking] = useState<boolean>(true);
    const [questions, setQuestions] = useState<InterRoundQuestion[]>([]);
    const [scaleMeta, setScaleMeta] = useState<{ minValue: number; maxValue: number; minLabel: string; maxLabel: string } | null>(null);

    // Fetch questions from backend when component mounts
    useEffect(() => {
        const load = async () => {
            setIsChecking(true);
            setError('');
            try {
                const data = await fetchInterRoundQuestions();
                setQuestions(data.questions);
                setScaleMeta(data.scale);
                // Initialize response entries
                const initial: Record<string, number | string> = {};
                data.questions.forEach((q) => {
                    if (q.type === 'scale') initial[q.id] = 0;
                    else initial[q.id] = '';
                });
                setResponses(initial);
            } catch (e) {
                console.error('Error fetching inter-round questions:', e);
                setError('Failed to fetch survey questions.');
            } finally {
                setIsChecking(false);
            }
        };
        load();
    }, []);

    const handleResponseChange = (field: string, value: number | string) => {
        setResponses(prev => ({ ...prev, [field]: value }));
        setError('');
    };

    const isFormValid = () => {
        if (!questions.length) return false;
        for (const q of questions) {
            const val = responses[q.id];
            if (q.type === 'scale') {
                if (typeof val !== 'number' || val < 1 || val > 7) return false;
            } else {
                if (typeof val !== 'string' || val.trim().length === 0) return false;
            }
        }
        return true;
    };

    const handleSubmitSurvey = async () => {
        setError('');
        
        if (!isFormValid()) {
            setError('Please answer all questions before submitting.');
            return;
        }

        setIsSubmitting(true);
        try {
            const result = await submitInterRoundSurvey(responses);
            if (result.all_completed) {
                navigate('/thank-you');
            } else {
                navigate('/survey');
            }
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
                    <p>{scaleMeta?.minLabel ?? 'Not at all'}</p>
                </div>
                {scaleOptions.map(option => (
                    <label key={option.value} className="survey-radio-option">
                        <input
                            type="radio"
                            name={field}
                            value={option.value}
                            checked={Number(responses[field] ?? 0) === option.value}
                            onChange={() => handleResponseChange(field, option.value)}
                            className="survey-radio-input"
                        />
                        {option.value}
                    </label>
                ))}
                <div className="survey-radio-group-right">
                    <p>{scaleMeta?.maxLabel ?? 'Extremely'}</p>
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
                        <p>Fetching survey questions...</p>
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
                        {questions.map((q) => (
                            q.type === 'scale' ? (
                                renderScaleQuestion(q.id, q.label, scaleOptions)
                            ) : (
                                <div key={q.id} className="survey-form-field">
                                    <label className="survey-form-label">{q.label}</label>
                                    {q.hint && (
                                        <p className="survey-form-hint">{q.hint}</p>
                                    )}
                                    <textarea
                                        value={String(responses[q.id] ?? '')}
                                        onChange={(e) => handleResponseChange(q.id, e.target.value)}
                                        className="survey-form-textarea"
                                        placeholder="Please describe the factors you considered..."
                                        rows={4}
                                    />
                                </div>
                            )
                        ))}

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