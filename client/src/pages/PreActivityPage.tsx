import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import '../styles/LandingPage.css';
import Navbar from '../components/Navbar';
import { submitPreActivitySurvey, checkPreActivitySurvey, checkLoginStatus } from '../utils/api';

function PreActivityPage() {
    const navigate = useNavigate();
    const [age, setAge] = useState<string>('');
    const [sex, setSex] = useState<string>('');
    const [otherSex, setOtherSex] = useState<string>('');
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [error, setError] = useState<string>('');
    const [isChecking, setIsChecking] = useState<boolean>(true);

    // Check login status and survey completion on page load
    useEffect(() => {
        const checkStatus = async () => {
            try {
                // First check if user is logged in
                const loginStatus = await checkLoginStatus();
                if (!loginStatus.isLoggedIn) {
                    navigate('/');
                    return;
                }

                // Then check if pre-activity survey is already completed
                const surveyStatus = await checkPreActivitySurvey();
                if (surveyStatus.completed) {
                    // Already completed, redirect to survey page
                    navigate('/survey');
                    return;
                }

                // Pre-fill form if partial data exists
                if (surveyStatus.age) {
                    setAge(surveyStatus.age.toString());
                }
                if (surveyStatus.sex) {
                    const predefinedOptions = ['Male', 'Female', 'Non-binary', 'Prefer not to say'];
                    if (predefinedOptions.includes(surveyStatus.sex)) {
                        setSex(surveyStatus.sex);
                    } else {
                        setSex('Other');
                        setOtherSex(surveyStatus.sex);
                    }
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

    const handleSubmitSurvey = async () => {
        setError('');
        
        // Validate form
        if (!age.trim() || !sex.trim()) {
            setError('Please fill in all fields');
            return;
        }

        if (sex === 'Other' && !otherSex.trim()) {
            setError('Please specify your sex/gender');
            return;
        }

        const ageNum = parseInt(age.trim());
        if (isNaN(ageNum) || ageNum < 1 || ageNum > 120) {
            setError('Please enter a valid age between 1 and 120');
            return;
        }

        setIsSubmitting(true);
        try {
            const sexValue = sex === 'Other' ? otherSex.trim() : sex.trim();
            await submitPreActivitySurvey(ageNum, sexValue);
            navigate('/survey');
        } catch (error) {
            console.error('Error submitting survey:', error);
            setError('Failed to submit survey. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

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
                    <h1>Pre-Activity Survey</h1>
                    <p>
                        Before we begin the main study, please complete this short pre-activity survey.
                        This will help us understand your background and preferences.
                    </p>

                    <div className="survey-container container">
                        <div className="survey-form-field">
                            <label className="survey-form-label">
                                Age:
                            </label>
                            <input
                                type="number"
                                value={age}
                                onChange={(e) => setAge(e.target.value)}
                                className="survey-form-input"
                                placeholder="Enter your age"
                                min="1"
                                max="120"
                            />
                        </div>

                        <div className="survey-form-field">
                            <label className="survey-form-label">
                                Sex:
                            </label>
                            <select
                                value={sex}
                                onChange={(e) => {
                                    setSex(e.target.value);
                                    if (e.target.value !== 'Other') {
                                        setOtherSex('');
                                    }
                                }}
                                className="survey-form-select"
                            >
                                <option value="">Select...</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Prefer not to say">Prefer not to say</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>

                        {sex === 'Other' && (
                            <div className="survey-form-field">
                                <label className="survey-form-label">
                                    Please specify:
                                </label>
                                <input
                                    type="text"
                                    value={otherSex}
                                    onChange={(e) => setOtherSex(e.target.value)}
                                    className="survey-form-input"
                                    placeholder="Please specify your sex/gender"
                                />
                            </div>
                        )}

                        {error && <div className="login-error">{error}</div>}
                    </div>
                </div>

                <button 
                    onClick={handleSubmitSurvey} 
                    className="start-button"
                    disabled={isSubmitting || !age.trim() || !sex.trim() || (sex === 'Other' && !otherSex.trim())}
                >
                    {isSubmitting ? 'Submitting...' : 'Submit and Continue to Survey'}
                </button>
            </div>
        </div>
    );
}

export default PreActivityPage; 