export interface LEDStatus {
  red: number;
  green: number;
  blue: number;
}

export interface VoiceCommand {
  command: string;
}

export interface LEDProps {
  brightness: number;
}

export interface LightStatusProps {
  ledStatus: LEDStatus;
}

export interface VoiceCommandProps {
  onStartRecording: () => void;
  lastCommand: string;
  isRecording: boolean;
} 