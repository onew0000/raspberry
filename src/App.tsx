import React, { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { LEDStatus } from './types';
import LightStatus from './components/LightStatus';
import VoiceCommand from './components/VoiceCommand';
import './App.css';

function App() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [ledStatus, setLedStatus] = useState<LEDStatus>({
    red: 0,
    green: 0,
    blue: 0
  });
  const [lastCommand, setLastCommand] = useState<string>('');
  const [isRecording, setIsRecording] = useState<boolean>(false);

  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    newSocket.on('led_status', (data: LEDStatus) => {
      setLedStatus(data);
    });

    newSocket.on('voice_command', (data: { command: string }) => {
      setLastCommand(data.command);
      setIsRecording(false);
    });

    return () => {
      newSocket.close();
    };
  }, []);

  const handleStartRecording = () => {
    if (socket) {
      socket.emit('start_recording');
      setIsRecording(true);
    }
  };

  return (
    <div className="container">
      <h1 className="app-title">삼각함수기반 조명 제어 시스템</h1>
      <div className="row">
        <div className="col-md-6">
          <LightStatus ledStatus={ledStatus} />
        </div>
        <div className="col-md-6">
          <VoiceCommand
            onStartRecording={handleStartRecording}
            lastCommand={lastCommand}
            isRecording={isRecording}
          />
        </div>
      </div>
    </div>
  );
}

export default App; 