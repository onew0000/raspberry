import React from 'react';
import { LightStatusProps } from '../types';
import LED from './LED';

const LightStatus: React.FC<LightStatusProps> = ({ ledStatus }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h5 className="card-title">조명 상태</h5>
      </div>
      <div className="card-body">
        <div className="light-status">
          <div className="light-item">
            <LED brightness={ledStatus.red} />
            <div className="light-label">빨간색</div>
            <div className="brightness-value">{ledStatus.red}%</div>
          </div>
          <div className="light-item">
            <LED brightness={ledStatus.green} />
            <div className="light-label">초록색</div>
            <div className="brightness-value">{ledStatus.green}%</div>
          </div>
          <div className="light-item">
            <LED brightness={ledStatus.blue} />
            <div className="light-label">파란색</div>
            <div className="brightness-value">{ledStatus.blue}%</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LightStatus; 