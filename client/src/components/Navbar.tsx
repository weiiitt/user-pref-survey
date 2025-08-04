import { useNavigate } from 'react-router-dom';
import '../styles/Navbar.css';
import { useAuth } from '../contexts/AuthContext';
import { FaPause, FaPlay } from 'react-icons/fa';

interface NavbarProps {
    onShowInstructions?: () => void;
    timer?: number | null;
    onPause?: () => void;
    isPaused?: boolean;
}

export default function Navbar({ onShowInstructions, timer, onPause, isPaused }: NavbarProps) {
    const navigate = useNavigate();
    const { participantId, logout } = useAuth();

    const handleLogout = async () => {
        try {
            await logout();
            navigate('/');
        } catch (error) {
            console.error('Error logging out:', error);
        }
    };

    return (
        <nav className="navbar">
            <div className="navbar-content">
                <div className="participant-info">
                    <span className="participant-label">Participant ID:</span>
                    <span className="participant-id">{participantId || 'Loading...'}</span>
                    {timer !== null && timer !== undefined && (
                        <div className="timer-info">
                            <span className="timer-value">
                                {Math.floor(timer / 60).toString().padStart(2, '0')}:
                                {Math.floor(timer % 60).toString().padStart(2, '0')}
                            </span>
                            {onPause && (
                                <button onClick={onPause} className="pause-icon-button" title={isPaused ? 'Resume' : 'Pause'}>
                                    {isPaused ? <FaPlay /> : <FaPause />}
                                </button>
                            )}
                        </div>
                    )}
                </div>
                <div className="navbar-buttons">
                    {onShowInstructions && (
                        <button onClick={onShowInstructions} className="instructions-button">
                            Instructions
                        </button>
                    )}
                    <button onClick={handleLogout} className="logout-button">
                        Log Out
                    </button>
                </div>
            </div>
        </nav>
    );
} 