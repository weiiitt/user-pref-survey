import RobotVideo from '../assets/robot-video.mp4';
import { Accordion } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../utils/api';
import '../styles/Accordian.scss';
import '../styles/LandingPage.css';

function LandingPage({ onLoginSuccess }: { onLoginSuccess: () => void }) {
    const navigate = useNavigate();

    const handleStartSurvey = async () => {
        try {
            await registerUser();
            onLoginSuccess();
            navigate('/survey');
        } catch (error) {
            console.error('Error registering:', error);
        }
    };

    return (
        <div className="landing-page">
            <div className="landing-page-video">
                <video src={RobotVideo} autoPlay loop muted />
                <div className='landing-page-video-attribution'>
                    Video source:&nbsp;<a href="https://www.youtube.com/shorts/PzD4574qhUE">WPI on Youtube</a>
                </div>
            </div>
            <div className='landing-page-content'>
                <div className='landing-page-content-text'>
                    <h1>User Preference Study for Navigation</h1>
                    <Accordion defaultActiveKey="1" flush>
                        <Accordion.Item eventKey="0">
                            <Accordion.Header>Project Overview</Accordion.Header>
                            <Accordion.Body>
                                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
                                eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
                                minim veniam, quis nostrud exercitation ullamco laboris nisi ut
                                aliquip ex ea commodo consequat. Duis aute irure dolor in
                                reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
                                pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
                                culpa qui officia deserunt mollit anim id est laborum.
                            </Accordion.Body>
                        </Accordion.Item>
                        <Accordion.Item eventKey="1">
                            <Accordion.Header>User Objectives</Accordion.Header>
                            <Accordion.Body>
                                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
                                eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
                                minim veniam, quis nostrud exercitation ullamco laboris nisi ut
                                aliquip ex ea commodo consequat. Duis aute irure dolor in
                                reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
                                pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
                                culpa qui officia deserunt mollit anim id est laborum.
                            </Accordion.Body>
                        </Accordion.Item>
                    </Accordion>
                </div>
                <button onClick={handleStartSurvey} className="start-button">
                    Start Survey
                </button>
            </div>
        </div>
    )
}

export default LandingPage;