import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SurveyPage from './pages/SurveyPage'
import LandingPage from './pages/LandingPage'
import PreActivityPage from './pages/PreActivityPage'
import InterRoundSurveyPage from './pages/InterRoundSurveyPage'
import ThankYouPage from './pages/ThankYouPage'
import './styles/App.css'
import { AuthProvider, useAuth } from './contexts/AuthContext'


function AppRoutes() {
	const { user, isLoading, login } = useAuth();

	if (isLoading) {
		return <div>Loading...</div>;
	}

	return (
		<Router basename="/user-pref-survey">
			<Routes>
				<Route
					path="/"
					element={
						user ? (
							<Navigate to="/pre-activity" replace />
						) : (
							<LandingPage onLoginSuccess={login} />
						)
					}
				/>
				<Route
					path="/pre-activity"
					element={
						user ? (
							<PreActivityPage />
						) : (
							<Navigate to="/" replace />
						)
					}
				/>
				<Route
					path="/survey"
					element={
						user ? (
							<SurveyPage user={user} />
						) : (
							<Navigate to="/" replace />
						)
					}
				/>
				<Route
					path="/inter-round-survey"
					element={
						user ? (
							<InterRoundSurveyPage />
						) : (
							<Navigate to="/" replace />
						)
					}
				/>
				<Route
					path="/thank-you"
					element={
						user ? (
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
