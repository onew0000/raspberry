import speech_recognition as sr
import openai
import RPi.GPIO as GPIO
import time
import math
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# GPT API 키 설정
openai.api_key = 'your-openai-api-key'

# GPIO 설정
LED_PINS = [18, 23, 24]  # 3개의 LED 핀 번호
GPIO.setmode(GPIO.BCM)
pwms = []

# 각 LED에 대한 PWM 설정
for pin in LED_PINS:
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, 100)  # 100Hz 주기
    pwm.start(0)
    pwms.append(pwm)

# 음성 인식기 초기화
recognizer = sr.Recognizer()

# LED 상태 추적
led_states = [0, 0, 0]  # 각 LED의 현재 밝기 상태 (0-100)

def update_led_status():
    """LED 상태를 웹 클라이언트에 전송"""
    socketio.emit('led_status', {
        'led1': led_states[0],
        'led2': led_states[1],
        'led3': led_states[2]
    })

def recognize_speech():
    with sr.Microphone() as source:
        print("🎙 음성을 말하세요...")
        audio = recognizer.listen(source)
    try:
        query = recognizer.recognize_google(audio, language='ko-KR')
        print(f"📥 입력된 음성: {query}")
        socketio.emit('voice_command', {'command': query})
        return query
    except sr.UnknownValueError:
        print("❗ 음성을 인식하지 못했습니다.")
        return None

def query_chatgpt(prompt):
    system_prompt = (
        "당신은 사용자의 자연스러운 문장을 분석하여 적절한 조명 효과를 추천하는 조명 디자이너입니다. "
        "다음과 같은 상황과 조명 효과를 매칭해주세요:\n"
        "1. 졸리거나 피곤할 때 -> 1번 LED를 부드럽게 깜빡이며 점점 어둡게\n"
        "2. 기분이 좋거나 활기찬 상태 -> 2번 LED를 밝게 켜고 3번 LED를 부드럽게 깜빡임\n"
        "3. 집중이 필요할 때 -> 1번과 2번 LED를 적당한 밝기로 켜기\n"
        "4. 편안한 휴식이 필요할 때 -> 모든 LED를 부드럽게 깜빡이며 점점 어둡게\n"
        "5. 기분이 우울하거나 슬플 때 -> 3번 LED만 부드럽게 깜빡이며 점점 밝게\n"
        "응답은 반드시 '효과: [효과번호]' 형식으로 해주세요."
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

def sine_wave_blinking(led_index, duration=10):
    print(f"🔄 {led_index+1}번 LED 삼각함수 기반 깜빡이기 시작")
    start_time = time.time()
    while time.time() - start_time < duration:
        t = time.time() - start_time
        brightness = (math.sin(2 * math.pi * t) + 1) * 50  # 0 ~ 100
        pwms[led_index].ChangeDutyCycle(brightness)
        led_states[led_index] = brightness
        update_led_status()
        time.sleep(0.05)

def gradually_brighten(led_index, duration=5):
    print(f"🔆 {led_index+1}번 LED 점점 밝게")
    for i in range(100):
        pwms[led_index].ChangeDutyCycle(i)
        led_states[led_index] = i
        update_led_status()
        time.sleep(duration / 100)

def gradually_dim(led_index, duration=5):
    print(f"🌑 {led_index+1}번 LED 점점 어둡게")
    for i in range(100, -1, -1):
        pwms[led_index].ChangeDutyCycle(i)
        led_states[led_index] = i
        update_led_status()
        time.sleep(duration / 100)

def turn_on_all():
    print("💡 모든 LED 켜기")
    for i, pwm in enumerate(pwms):
        pwm.ChangeDutyCycle(100)
        led_states[i] = 100
    update_led_status()

def turn_off_all():
    print("🌑 모든 LED 끄기")
    for i, pwm in enumerate(pwms):
        pwm.ChangeDutyCycle(0)
        led_states[i] = 0
    update_led_status()

def execute_light_effect(effect_number):
    if effect_number == 1:  # 졸리거나 피곤할 때
        print("😴 졸린 상태에 맞는 부드러운 조명 효과를 시작합니다...")
        sine_wave_blinking(0, duration=5)
        gradually_dim(0, duration=3)
    elif effect_number == 2:  # 기분이 좋거나 활기찬 상태
        print("😊 활기찬 분위기의 조명 효과를 시작합니다...")
        pwms[1].ChangeDutyCycle(100)  # 2번 LED 밝게
        led_states[1] = 100
        update_led_status()
        sine_wave_blinking(2, duration=10)  # 3번 LED 깜빡임
    elif effect_number == 3:  # 집중이 필요할 때
        print("💡 집중하기 좋은 조명 효과를 시작합니다...")
        pwms[0].ChangeDutyCycle(70)  # 1번 LED 적당한 밝기
        pwms[1].ChangeDutyCycle(70)  # 2번 LED 적당한 밝기
        led_states[0] = 70
        led_states[1] = 70
        update_led_status()
    elif effect_number == 4:  # 편안한 휴식이 필요할 때
        print("🌙 편안한 휴식을 위한 조명 효과를 시작합니다...")
        for i in range(3):
            sine_wave_blinking(i, duration=8)
        for i in range(3):
            gradually_dim(i, duration=3)
    elif effect_number == 5:  # 기분이 우울하거나 슬플 때
        print("💫 기분 전환이 되는 조명 효과를 시작합니다...")
        sine_wave_blinking(2, duration=5)
        gradually_brighten(2, duration=3)

def execute_command(command_text):
    try:
        # "효과: [번호]" 형식에서 번호만 추출
        effect_number = int(command_text.split("효과:")[1].strip())
        execute_light_effect(effect_number)
    except (ValueError, IndexError):
        print("⚠️ 조명 효과를 실행할 수 없습니다.")

def voice_recognition_thread():
    while True:
        spoken = recognize_speech()
        if spoken:
            response = query_chatgpt(spoken)
            print(f"🤖 GPT 명령 해석: {response}")
            execute_command(response)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_recording')
def handle_start_recording():
    threading.Thread(target=voice_recognition_thread).start()

if __name__ == '__main__':
    try:
        socketio.run(app, host='127.0.0.1', port=5000, debug=True)
    except KeyboardInterrupt:
        print("🛑 종료")
    finally:
        for pwm in pwms:
            pwm.stop()
        GPIO.cleanup()

