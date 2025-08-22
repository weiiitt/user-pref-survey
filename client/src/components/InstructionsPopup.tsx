import '../styles/InstructionsPopup.css';

interface InstructionsPopupProps {
	isVisible: boolean;
	onClose: () => void;
	testType: string;
}

export default function InstructionsPopup({ isVisible, onClose, testType }: InstructionsPopupProps) {
	if (!isVisible) return null;

	const isTabletop = testType === "tabletop";

	return (
		<div className="popup-overlay" onClick={onClose}>
			<div className="popup-content" onClick={(e) => e.stopPropagation()}>
				<div className="popup-header">
					<h2>{isTabletop ? "Table-top Task Instructions" : "Robot Navigation Task Instructions"}</h2>
					<button className="close-button" onClick={onClose}>×</button>
				</div>
				<div className="popup-body">
					{isTabletop ? (
						<div>
							<p>The robot is bringing you a full coffee cup across the table. You'll see two trajectory options - choose your preferred one.</p>
							<p>Arrows represent 3D paths - if they go over objects, the robot will hover above them.</p>
							<p>Your goal is to teach the robot to avoid hovering over electronics (laptop, mouse, camera, headphones). The robot learns from your choices, even if the options aren't perfect.</p>
							<p>Clicking on the image will select your preferred trajectory.</p>
						</div>
					) : (
						<div>
							<p>For this task you will be deciding the best path for a food delivery robot. You'll see two trajectory options - choose your preferred one.</p>
							<p>Your goal is to teach the robot to reach its destination quickly. Crossing main roads (asphalt) may take more time and be riskier due to cars, while some surfaces (like grass) might be slower or bumpier. We will assume the robot can safely and quickly navigate through the other surfaces.</p>
							<p>These are the surfaces the robot might encounter:</p>
							<div className="material-grid">
								<div className="material-item">
									<img src="https://i.imgur.com/rU8H04D.jpeg" alt="Grass" className="material-image" />
									<div className="material-label">Grass</div>
								</div>
								<div className="material-item">
									<img src="https://i.imgur.com/5da33pJ.jpeg" alt="Concrete" className="material-image" />
									<div className="material-label">Concrete</div>
								</div>
								<div className="material-item">
									<img src="https://i.imgur.com/Zt98bZp.jpeg" alt="Paved" className="material-image" />
									<div className="material-label">Paved</div>
								</div>
								<div className="material-item">
									<img src="https://i.imgur.com/X0eCloD.jpeg" alt="Asphalt" className="material-image" />
									<div className="material-label">Asphalt</div>
								</div>
							</div>
						</div>
					)}
				</div>
				<div className="popup-footer">
					<button onClick={onClose} className="close-popup-button">
						Continue
					</button>
				</div>
			</div>
		</div>
	);
}