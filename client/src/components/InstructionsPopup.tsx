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
							<p>[Robot navigation instructions - you can fill this in]</p>
							<p>This is where you'll add the specific instructions for the robot navigation task.</p>
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