import { useNavigate } from 'react-router-dom';
import '../styles/Navbar.css';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
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
                </div>
                <button onClick={handleLogout} className="logout-button">
                    Log Out
                </button>
            </div>
        </nav>
    );
} 