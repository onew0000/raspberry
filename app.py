import speech_recognition as sr
import openai
from gpiozero import PWMLED
from gpiozero.pins.pigpio import PiGPIOFactory
import time
import math
from gevent import monkey
monkey.patch_all()
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketServer
import json

# GPT API 키 설정
openai.api_key = 'your-openai-api-key'

# GPIO 설정 (라즈베리파이 5용)
try:
    # pigpio 팩토리 설정
    factory = PiGPIOFactory()
    
    # 3개의 LED 핀 설정
    leds = [
        PWMLED(18, pin_factory=factory),  # 빨간색 LED
        PWMLED(23, pin_factory=factory),  # 초록색 LED
        PWMLED(24, pin_factory=factory)   # 파란색 LED
    ]
    print("GPIO 초기화 성공")
except Exception as e:
    print(f"GPIO 초기화 오류: {e}")
    exit(1)

# 음성 인식기 초기화
recognizer = sr.Recognizer()

# LED 상태 추적
led_states = [0, 0, 0]  # 각 LED의 현재 밝기 상태 (0-1)

# WebSocket 클라이언트 저장소
clients = set()

def update_led_status():
    """LED 상태를 웹 클라이언트에 전송"""
    message = json.dumps({
        'type': 'led_status',
        'data': {
            'red': led_states[0] * 100,
            'green': led_states[1] * 100,
            'blue': led_states[2] * 100
        }
    })
    for client in clients:
        try:
            client.send(message)
        except:
            clients.remove(client)

def recognize_speech():
    with sr.Microphone() as source:
        print("🎙 음성을 말하세요...")
        audio = recognizer.listen(source)
    try:
        query = recognizer.recognize_google(audio, language='ko-KR')
        print(f" 입력된 음성: {query}")
        message = json.dumps({
            'type': 'voice_command',
            'data': {'command': query}
        })
        for client in clients:
            try:
                client.send(message)
            except:
                clients.remove(client)
        return query
    except sr.UnknownValueError:
        print("❗ 음성을 인식하지 못했습니다.")
        return None

def query_chatgpt(prompt):
    system_prompt = (
        "당신은 사용자의 자연스러운 문장을 분석하여 적절한 조명 효과를 추천하는 조명 디자이너입니다. "
        "다음과 같은 상황과 조명 효과를 매칭해주세요:\n"
        "1. 졸리거나 피곤할 때 -> 빨간색 LED를 부드럽게 깜빡이며 점점 어둡게\n"
        "2. 기분이 좋거나 활기찬 상태 -> 초록색 LED를 밝게 켜고 파란색 LED를 부드럽게 깜빡임\n"
        "3. 집중이 필요할 때 -> 빨간색과 초록색 LED를 적당한 밝기로 켜기\n"
        "4. 편안한 휴식이 필요할 때 -> 모든 LED를 부드럽게 깜빡이며 점점 어둡게\n"
        "5. 기분이 우울하거나 슬플 때 -> 파란색 LED만 부드럽게 깜빡이며 점점 밝게\n"
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
    print(f" {led_index+1}번 LED 삼각함수 기반 깜빡이기 시작")
    start_time = time.time()
    while time.time() - start_time < duration:
        t = time.time() - start_time
        brightness = (math.sin(2 * math.pi * t) + 1) * 0.5  # 0 ~ 1
        leds[led_index].value = brightness
        led_states[led_index] = brightness
        update_led_status()
        time.sleep(0.05)

def gradually_brighten(led_index, duration=5):
    print(f" {led_index+1}번 LED 점점 밝게")
    for i in range(101):
        brightness = i / 100
        leds[led_index].value = brightness
        led_states[led_index] = brightness
        update_led_status()
        time.sleep(duration / 100)

def gradually_dim(led_index, duration=5):
    print(f"🌑 {led_index+1}번 LED 점점 어둡게")
    for i in range(100, -1, -1):
        brightness = i / 100
        leds[led_index].value = brightness
        led_states[led_index] = brightness
        update_led_status()
        time.sleep(duration / 100)

def turn_on_all():
    print("💡 모든 LED 켜기")
    for i, led in enumerate(leds):
        led.value = 1
        led_states[i] = 1
    update_led_status()

def turn_off_all():
    print("🌑 모든 LED 끄기")
    for i, led in enumerate(leds):
        led.value = 0
        led_states[i] = 0
    update_led_status()

def execute_light_effect(effect_number):
    if effect_number == 1:  # 졸리거나 피곤할 때
        print("😴 졸린 상태에 맞는 부드러운 조명 효과를 시작합니다...")
        sine_wave_blinking(0, duration=5)
        gradually_dim(0, duration=3)
    elif effect_number == 2:  # 기분이 좋거나 활기찬 상태
        print("😊 활기찬 분위기의 조명 효과를 시작합니다...")
        leds[1].value = 1  # 초록색 LED 밝게
        led_states[1] = 1
        update_led_status()
        sine_wave_blinking(2, duration=10)  # 파란색 LED 깜빡임
    elif effect_number == 3:  # 집중이 필요할 때
        print("💡 집중하기 좋은 조명 효과를 시작합니다...")
        leds[0].value = 0.7  # 빨간색 LED 적당한 밝기
        leds[1].value = 0.7  # 초록색 LED 적당한 밝기
        led_states[0] = 0.7
        led_states[1] = 0.7
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

def handle_websocket(ws):
    """WebSocket 연결 처리"""
    clients.add(ws)
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
            data = json.loads(message)
            if data.get('type') == 'start_recording':
                import threading
                threading.Thread(target=voice_recognition_thread).start()
    except:
        pass
    finally:
        clients.remove(ws)

def application(environ, start_response):
    """WSGI 애플리케이션"""
    if environ.get('PATH_INFO') == '/ws':
        handle_websocket(environ['wsgi.websocket'])
        return []
    
    if environ.get('PATH_INFO') == '/':
        start_response('200 OK', [('Content-Type', 'text/html')])
        with open('templates/index.html', 'rb') as f:
            return [f.read()]
    
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found']

if __name__ == '__main__':
    try:
        server = WSGIServer(('127.0.0.1', 5000), application, handler_class=WebSocketHandler)
        print("서버가 시작되었습니다. http://127.0.0.1:5000")
        server.serve_forever()
    except KeyboardInterrupt:
        print("🛑 종료")
    finally:
        for led in leds:
            led.close()
