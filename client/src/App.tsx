import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SurveyPage from './pages/SurveyPage'
import LandingPage from './pages/LandingPage'
import './styles/App.css'
import { useEffect, useState } from 'react'
import { checkLoginStatus } from './utils/api'
import HistoryPage from './pages/History';


function App() {
	const [isLoggedIn, setIsLoggedIn] = useState(false);
	const [isLoading, setIsLoading] = useState(true);

	useEffect(() => {
		const checkLogin = async () => {
			try {
				const loggedIn = await checkLoginStatus();
				setIsLoggedIn(loggedIn);
			} catch (error) {
				console.error('Error checking login status:', error);
				setIsLoggedIn(false);
			} finally {
				setIsLoading(false);
			}
		};
		checkLogin();
	}, []);

	if (isLoading) {
		return <div>Loading...</div>;
	}

	return (
		<Router>
			<Routes>
				<Route
					path="/"
					element={
						isLoggedIn ? (
							<Navigate to="/survey" replace />
						) : (
							<LandingPage onLoginSuccess={() => setIsLoggedIn(true)} />
						)
					}
				/>
				<Route
					path="/survey"
					element={
						isLoggedIn ? (
							<SurveyPage />
						) : (
							<Navigate to="/" replace />
						)
					}
				/>
				<Route
					path="/history"
					element={
						isLoggedIn ? (
							<HistoryPage />
						) : (
							<Navigate to="/" replace />
						)
					}
				/>
			</Routes>
		</Router>
	)
}

export default App
