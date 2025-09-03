import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { registerUser, fetchUniqueParticipantId, loginUser } from '../utils/api';
import '../styles/LandingPage.css';

function LandingPage({ onLoginSuccess }: { onLoginSuccess: (id: string) => void }) {
    const navigate = useNavigate();
    const [participantId, setParticipantId] = useState<string>('');
    const [showLogin, setShowLogin] = useState<boolean>(false);
    const [loginId, setLoginId] = useState<string>('');
    const [loginError, setLoginError] = useState<string>('');
    const [isGeneratingId, setIsGeneratingId] = useState<boolean>(true);
    const [isRegistering, setIsRegistering] = useState<boolean>(false);

    useEffect(() => {
        // Fetch a prospective unique participant ID when the component mounts
        const fetchId = async () => {
            try {
                const newId = await fetchUniqueParticipantId();
                setParticipantId(newId);
            } catch (error) {
                console.error('Error fetching unique participant ID:', error);
                // Fallback to local generation if server fails
                const fallbackId = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
                setParticipantId(fallbackId);
            } finally {
                setIsGeneratingId(false);
            }
        };
        fetchId();
    }, []);

    const handleStartSurvey = async () => {
        setIsRegistering(true);
        try {
            await registerUser(participantId); // Use the prospective ID shown to user
            onLoginSuccess(participantId);
            navigate('/pre-activity');
        } catch (error) {
            console.error('Error registering:', error);
            alert('Registration failed. Please try again.');
        } finally {
            setIsRegistering(false);
        }
    };

    const handleLogin = async () => {
        if (!loginId || loginId.length !== 4 || !loginId.match(/^\d{4}$/)) {
            setLoginError('Please enter a valid 4-digit participant ID.');
            return;
        }

        try {
            await loginUser(loginId);
            onLoginSuccess(loginId);
            navigate('/pre-activity');
        } catch (error) {
            console.error('Error logging in:', error);
            setLoginError('Participant ID not found. Please check your ID or start a new survey.');
        }
    };

    return (
        <div className="landing-page">
            <div className='landing-page-content'>
                <div className='landing-page-content-text'>
                    <h1>Learning Human Preferences for Robot Navigation and Object Handling</h1>
                    <h2>Permission to Take Part in a Human Research Study</h2>
                    <div className="section-content">
                        <p>
                        <b>IRB Protocol Number: 25-0429</b>
                        </p>
                        <p>
                        <b>Investigator: Alessandro Roncone, Bradley Hayes</b>
                        </p>
                        <p>
                        You are invited to take part in a research study about how people prefer robots to behave in common tasks such as navigation and object handling. The purpose of this study is to understand how humans make decisions when comparing robot actions, so we can improve robot learning algorithms.
                        </p>
                        <p>
                        Your participation in this research is entirely voluntary. You may choose to stop participating at any time. The study will take approximately <b>25 to 35 minutes</b>, and up to <b>50 individuals</b> will participate.
                        </p>
                        <p>
                        This study will be conducted entirely online.
                        </p>
                        <p>
                        <b>Here is what you will do:</b>
                        </p>    
                        <ol>
                            <li>You will see a series of robot trajectories on your screen. In each image, the robot performs a task—either navigating through different terrains or carrying a cup of coffee over various objects. The robot's trajectory is indicated by the arrow on the image.</li>
                            <li>You will be asked to <b>choose between two robot trajectories</b> in each round based on which behavior you prefer. There will be approximately <b>4 rounds of 10 comparisons</b> in each task.</li>
                            <li>After each task, you will answer a short <b>questionnaire</b> about how you made your decisions and how well the robot learned your preferences.</li>
                        </ol>
                        <p>
                        The total duration of the study is approximately <b>25-35 minutes</b>.
                        </p>
                        <p>
                        You will be compensated $7.50 through <b>Prolific</b> once you complete the study and your responses are approved.
                        </p>
                        <p>
                        We will not collect any personal information about you during the study. Your responses will be associated only with your confidential <b>Prolific ID</b>, which is used solely for compensation purposes.
                        </p>
                        <p>
                        All study data will be stored securely on a password-protected, university-managed server and accessed only by the research team. The results of this study may be published in scientific journals or presented at conferences, but no identifying information will be disclosed. Your confidential Prolific ID will be disassociated from your responses once payment has been approved and completed. After this removal, your de-identified information (e.g. responses from the study) may be used for future research studies or shared with other investigators for future research without additional informed consent from you or your legally authorized representative.
                        </p>
                        <p><b>By clicking into the study, you are agreeing to volunteer for this study.</b></p>
                    </div>
                    <h2>Questions</h2>
                    <div className="section-content">
                        <p>
                        If you have questions about the research, you may contact the Principal Investigator, Yi-Shiuan Tung, at <a href="mailto:yi-shiuan.tung@colorado.edu">yi-shiuan.tung@colorado.edu</a>.
                        </p>
                        <p>
                        If you have concerns or complaints about the research you can contact the CU Boulder IRB at (303) 735-3702 or <a href="mailto:irbadmin@colorado.edu">irbadmin@colorado.edu</a> if:
                        </p>
                        <ul>
                            <li>Your questions, concerns, or complaints are not being answered by the research team.</li>
                            <li>You cannot reach the research team.</li>
                            <li>You want to talk to someone besides the research team.</li>
                            <li>You have questions about your rights as a research subject.</li>
                            <li>You want to get information or provide input about this research.</li>
                        </ul>
                    </div>
                    
                    {!showLogin ? (
                        <>
                            <div className="participant-id-section">
                                <h3>Your Participant ID</h3>
                                <div className="participant-id-display">
                                    {isGeneratingId ? (
                                        <em>Generating unique ID...</em>
                                    ) : (
                                        <strong>{participantId}</strong>
                                    )}
                                </div>
                                <p><em>Please save this ID. If you need to pause and return to the study later, you can use this ID to log back in.</em></p>
                            </div>
                            
                            <div className="returning-user-section">
                                <p>Returning to continue your study? 
                                    <button 
                                        onClick={() => setShowLogin(true)} 
                                        className="login-link-button"
                                    >
                                        Click here to log in
                                    </button>
                                </p>
                            </div>
                        </>
                    ) : (
                        <div className="login-section">
                            <h3>Continue Your Study</h3>
                            <p>Enter your 4-digit participant ID:</p>
                            <input
                                type="text"
                                value={loginId}
                                onChange={(e) => {
                                    setLoginId(e.target.value);
                                    setLoginError('');
                                }}
                                maxLength={4}
                                placeholder="Enter 4-digit ID"
                                className="login-input"
                            />
                            {loginError && <p className="login-error">{loginError}</p>}
                            <div className="login-buttons">
                                <button onClick={handleLogin} className="login-button">
                                    Continue Study
                                </button>
                                <button 
                                    onClick={() => {
                                        setShowLogin(false);
                                        setLoginId('');
                                        setLoginError('');
                                    }} 
                                    className="cancel-button"
                                >
                                    Back to New Study
                                </button>
                            </div>
                        </div>
                    )}
                </div>
                
                {!showLogin && (
                    <button 
                        onClick={handleStartSurvey} 
                        className="start-button"
                        disabled={isGeneratingId || isRegistering}
                    >
                        {isGeneratingId ? 'Generating ID...' : isRegistering ? 'Starting Survey...' : 'Start Survey'}
                    </button>
                )}
            </div>
        </div>
    )
}

export default LandingPage;