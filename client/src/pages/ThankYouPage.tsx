import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/LandingPage.css';
import Navbar from '../components/Navbar';

function ThankYouPage() {
	const navigate = useNavigate();
	const { user, logout } = useAuth();

	useEffect(() => {
		// Check if user is logged in
		if (!user) {
			navigate('/');
		}
	}, [user, navigate]);

	const handleLogout = async () => {
		try {
			await logout();
			navigate('/');
		} catch (error) {
			console.error('Error logging out:', error);
		}
	};

	return (
		<div className="page-layout">
			<Navbar />
			<div className='page-content'>
				<div className='page-content-text'>
					<h1>Thank You!</h1>
					<p>
						<b>You have successfully completed the survey.</b>
					</p>
					<p>
						Thank you for your participation! Your responses have been recorded and will help us improve our understanding of user preferences in navigation systems.
					</p>
					<p>
						You may now close this window or click the button below to return to the start page.
					</p>
				</div>

				<button onClick={handleLogout} className="start-button">
					Return to Start
				</button>
			</div>
		</div>
	);
}

export default ThankYouPage;