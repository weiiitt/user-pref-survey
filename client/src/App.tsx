import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SurveyPage from './pages/SurveyPage'
import LandingPage from './pages/LandingPage'
import PreActivityPage from './pages/PreActivityPage'
import InterRoundSurveyPage from './pages/InterRoundSurveyPage'
import ThankYouPage from './pages/ThankYouPage'
import './styles/App.css'
import { AuthProvider, useAuth } from './contexts/AuthContext'

function AppRoutes() {
	const { isLoggedIn, isLoading, login } = useAuth();

	if (isLoading) {
		return <div>Loading...</div>;
	}

	return (
		<Router basename="/user-pref-survey">
			<Routes>
				<Route
					path="/"
					element={
						isLoggedIn ? (
							<Navigate to="/pre-activity" replace />
						) : (
							<LandingPage onLoginSuccess={login} />
						)
					}
				/>
				<Route
					path="/pre-activity"
					element={
						isLoggedIn ? (
							<PreActivityPage />
						) : (
							<Navigate to="/" replace />
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
					path="/inter-round-survey"
					element={
						isLoggedIn ? (
							<InterRoundSurveyPage />
						) : (
							<Navigate to="/" replace />
						)
					}
				/>
				<Route
					path="/thank-you"
					element={
						isLoggedIn ? (
							<ThankYouPage />
						) : (
							<Navigate to="/" replace />
						)
					}
				/>
			</Routes>
		</Router>
	)
}

function App() {
	return (
		<AuthProvider>
			<AppRoutes />
		</AuthProvider>
	)
}

export default App
