import React from 'react';
import { LEDProps } from '../types';

const LED: React.FC<LEDProps> = ({ brightness }) => {
  return (
    <div 
      className="light-indicator"
      style={{
        opacity: brightness / 100,
        boxShadow: `0 0 20px rgba(255, 255, 255, ${brightness / 100})`
      }}
    />
  );
};

export default LED; 