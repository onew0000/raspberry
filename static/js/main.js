document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const startRecordingBtn = document.getElementById('startRecording');
    const recordingStatus = document.getElementById('recordingStatus');
    const commandText = document.getElementById('commandText');

    // LED 상태 업데이트 함수
    function updateLEDStatus(ledNumber, brightness) {
        const statusElement = document.getElementById(`led${ledNumber}-status`);
        const brightnessElement = document.getElementById(`led${ledNumber}-brightness`);
        
        if (brightness > 0) {
            statusElement.classList.add('active');
        } else {
            statusElement.classList.remove('active');
        }
        
        brightnessElement.textContent = `${Math.round(brightness)}%`;
    }

    // 소켓 이벤트 리스너
    socket.on('led_status', function(data) {
        updateLEDStatus(1, data.led1);
        updateLEDStatus(2, data.led2);
        updateLEDStatus(3, data.led3);
    });

    socket.on('voice_command', function(data) {
        commandText.textContent = data.command;
        recordingStatus.classList.add('d-none');
    });

    // 음성 명령 시작 버튼 클릭 이벤트
    startRecordingBtn.addEventListener('click', function() {
        recordingStatus.classList.remove('d-none');
        socket.emit('start_recording');
    });
}); 