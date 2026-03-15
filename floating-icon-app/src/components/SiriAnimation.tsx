import React from 'react';
import './SiriAnimation.css';

interface SiriAnimationProps {
    isListening: boolean;
}

const SiriAnimation: React.FC<SiriAnimationProps> = ({ isListening }) => {
    return (
        <div className={`siri-container ${isListening ? 'listening' : ''}`}>
            <div className="siri-blob"></div>
            <div className="siri-blob"></div>
            <div className="siri-blob"></div>
        </div>
    );
};

export default SiriAnimation;
