import { useNavigate } from 'react-router-dom';
import '../styles/LandingPage.css';
import Navbar from '../components/Navbar';

function PreActivityPage() {
    const navigate = useNavigate();

    const handleContinueToSurvey = () => {
        navigate('/survey');
    };

    return (
        <div className="landing-page">
            <Navbar />
            <div className='landing-page-content'>
                <div className='landing-page-content-text'>
                    <h1>Pre-Activity Survey</h1>
                    <p>
                        Before we begin the main study, please complete this short pre-activity survey.
                        This will help us understand your background and preferences.
                    </p>
                    <p>
                        <b>If you have already completed the survey, please click the button below to continue to the main survey.</b>
                    </p>

                    {/* Placeholder div where the user will paste their Google form iframe */}
                    <div className="google-form-container">
                        {/* Google form iframe will be pasted here */}
                        <iframe
                            src="https://docs.google.com/forms/d/e/1FAIpQLSfwmXpIgMUVa7uMSJf2HeD0FuzIdd1sAh0AlhAkQ43wMeCXnw/viewform?embedded=true"
                            width={640}
                            height={1031}
                            style={{ border: 0, margin: 0 }}
                        >
                            Loading…
                        </iframe>
                    </div>

                    <p>
                        After completing the form above, click the button below to continue to the main survey.
                    </p>
                </div>

                <button onClick={handleContinueToSurvey} className="start-button">
                    Continue to Main Survey
                </button>
            </div>
        </div>
    );
}

export default PreActivityPage; 