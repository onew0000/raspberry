import React from 'react';
import { VoiceCommandProps } from '../types';

const VoiceCommand: React.FC<VoiceCommandProps> = ({
  onStartRecording,
  lastCommand,
  isRecording,
}) => {
  return (
    <div className="card">
      <div className="card-header">
        <h5 className="card-title">음성 명령</h5>
      </div>
      <div className="card-body">
        <div className="voice-command">
          <button
            id="startRecording"
            className="btn btn-primary"
            onClick={onStartRecording}
            disabled={isRecording}
          >
            {isRecording ? (
              <>
                <i className="fas fa-microphone-alt"></i> 음성 인식 중...
              </>
            ) : (
              <>
                <i className="fas fa-microphone"></i> 음성 명령 시작
              </>
            )}
          </button>
          {isRecording && (
            <div className="alert alert-info">
              <i className="fas fa-info-circle"></i> 음성을 입력해주세요...
            </div>
          )}
          <div className="last-command">
            <h6>마지막 명령</h6>
            <p>{lastCommand || '아직 명령이 없습니다.'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceCommand; 