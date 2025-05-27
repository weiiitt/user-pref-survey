import React from 'react';
import styles from '../styles/ProgressIndicator.module.css';

interface ProgressIndicatorProps {
  totalQuestions: number;
  currentQuestion: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ totalQuestions, currentQuestion }) => {
  return (
    <div className={styles.progressContainer}>
      {Array.from({ length: totalQuestions }, (_, index) => (
        <div
          key={index}
          className={`${styles.progressCircle} ${index + 1 === currentQuestion ? styles.active : ''}`}
        />
      ))}
    </div>
  );
};

export default ProgressIndicator; 