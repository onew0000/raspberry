import speech_recognition as sr
import openai
from gpiozero import PWMLED
import time
import math
import threading
from gevent import monkey
monkey.patch_all()
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
import json
import atexit

# GPT API 키 설정
openai.api_key = 'your-openai-api-key'

# GPIO 설정 (라즈베리파이 5용 - gpiozero 기본 핀 팩토리 사용)
try:
    # gpiozero는 기본적으로 RPi.GPIO를 사용하므로 pigpio 없이도 작동
    # 라즈베리파이 5에서는 기본 핀 팩토리를 사용하는 것이 안정적
    
    # LED 핀 설정 (BCM 핀 번호)
    led_pins = [18, 23, 24]  # 빨간색, 초록색, 파란색 LED 핀
    
    # PWMLED 객체 생성 (gpiozero 사용)
    leds = [PWMLED(pin) for pin in led_pins]
    
    print("✅ GPIO 초기화 성공 (gpiozero 기본 핀 팩토리 사용)")
except Exception as e:
    print(f"❌ GPIO 초기화 오류: {e}")
    print("💡 해결 방법:")
    print("1. sudo apt update && sudo apt install python3-gpiozero")
    print("2. pip install gpiozero")
    print("3. 라즈베리파이 설정에서 SPI, I2C, GPIO 활성화")
    exit(1)

# 프로그램 종료 시 GPIO 정리
def cleanup_gpio():
    """프로그램 종료 시 LED 끄고 GPIO 정리"""
    try:
        for led in leds:
            led.off()
        print("🧹 GPIO 정리 완료")
    except:
        pass

atexit.register(cleanup_gpio)

# 음성 인식기 초기화
recognizer = sr.Recognizer()

# LED 상태 추적
led_states = [0.0, 0.0, 0.0]  # 각 LED의 현재 밝기 상태 (0.0-1.0)

# WebSocket 클라이언트 저장소
clients = set()

# 음성 인식 스레드 제어용 플래그
is_recording = False

def update_led_status():
    """LED 상태를 웹 클라이언트에 전송"""
    message = json.dumps({
        'type': 'led_status',
        'data': {
            'red': int(led_states[0] * 100),
            'green': int(led_states[1] * 100),
            'blue': int(led_states[2] * 100)
        }
    })
    for client in list(clients):
        try:
            client.send(message)
        except:
            clients.discard(client)

def recognize_speech():
    """음성 인식 함수"""
    global is_recording
    try:
        with sr.Microphone() as source:
            print("🎙 음성을 말하세요...")
            # 주변 소음 조정
            recognizer.adjust_for_ambient_noise(source, duration=1)
            # 음성 듣기 (타임아웃: 10초, 구문 제한: 5초)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
        
        # Google 음성 인식 API 사용
        query = recognizer.recognize_google(audio, language='ko-KR')
        print(f"🗣 입력된 음성: {query}")
        
        # 웹 클라이언트에 음성 명령 전송
        message = json.dumps({
            'type': 'voice_command',
            'data': {'command': query}
        })
        for client in list(clients):
            try:
                client.send(message)
            except:
                clients.discard(client)
        return query
        
    except sr.WaitTimeoutError:
        print("⏰ 음성 입력 시간 초과")
        return None
    except sr.UnknownValueError:
        print("❗ 음성을 인식하지 못했습니다.")
        return None
    except sr.RequestError as e:
        print(f"❗ Google 음성 인식 서비스 오류: {e}")
        return None
    except Exception as e:
        print(f"❗ 음성 인식 오류: {e}")
        return None
    finally:
        is_recording = False

def query_chatgpt(prompt):
    """ChatGPT API를 사용하여 음성 명령 해석"""
    try:
        system_prompt = (
            "당신은 사용자의 자연스러운 문장을 분석하여 적절한 조명 효과를 추천하는 조명 디자이너입니다. "
            "다음과 같은 상황과 조명 효과를 매칭해주세요:\n"
            "1. 졸리거나 피곤할 때 -> 빨간색 LED를 부드럽게 깜빡이며 점점 어둡게\n"
            "2. 기분이 좋거나 활기찬 상태 -> 초록색 LED를 밝게 켜고 파란색 LED를 부드럽게 깜빡임\n"
            "3. 집중이 필요할 때 -> 빨간색과 초록색 LED를 적당한 밝기로 켜기\n"
            "4. 편안한 휴식이 필요할 때 -> 모든 LED를 부드럽게 깜빡이며 점점 어둡게\n"
            "5. 기분이 우울하거나 슬플 때 -> 파란색 LED만 부드럽게 깜빡이며 점점 밝게\n"
            "6. 모든 LED 끄기 -> 모든 LED를 끄기\n"
            "7. 모든 LED 켜기 -> 모든 LED를 최대 밝기로 켜기\n"
            "응답은 반드시 '효과: [효과번호]' 형식으로 해주세요."
        )
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        return response['choices'][0]['message']['content'].strip()
        
    except Exception as e:
        print(f"❗ ChatGPT API 오류: {e}")
        return "효과: 1"  # 기본값

def sine_wave_blinking(led_index, duration=10, frequency=0.5):
    """삼각함수 기반 LED 깜빡이기"""
    print(f"✨ {led_index+1}번 LED 삼각함수 기반 깜빡이기 시작 ({duration}초)")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        t = time.time() - start_time
        # 사인파를 사용하여 부드러운 깜빡임 효과 (0.0 ~ 1.0)
        brightness = (math.sin(2 * math.pi * frequency * t) + 1) / 2
        leds[led_index].value = brightness
        led_states[led_index] = brightness
        update_led_status()
        time.sleep(0.05)  # 20fps로 업데이트

def gradually_brighten(led_index, duration=5):
    """LED 점점 밝게"""
    print(f"🌅 {led_index+1}번 LED 점점 밝게 ({duration}초)")
    steps = 100
    for i in range(steps + 1):
        brightness = i / steps  # 0.0 ~ 1.0
        leds[led_index].value = brightness
        led_states[led_index] = brightness
        update_led_status()
        time.sleep(duration / steps)

def gradually_dim(led_index, duration=5):
    """LED 점점 어둡게"""
    print(f"🌑 {led_index+1}번 LED 점점 어둡게 ({duration}초)")
    steps = 100
    for i in range(steps, -1, -1):
        brightness = i / steps  # 1.0 ~ 0.0
        leds[led_index].value = brightness
        led_states[led_index] = brightness
        update_led_status()
        time.sleep(duration / steps)

def turn_on_all():
    """모든 LED 켜기"""
    print("💡 모든 LED 켜기")
    for i, led in enumerate(leds):
        led.on()  # 최대 밝기
        led_states[i] = 1.0
    update_led_status()

def turn_off_all():
    """모든 LED 끄기"""
    print("🌑 모든 LED 끄기")
    for i, led in enumerate(leds):
        led.off()
        led_states[i] = 0.0
    update_led_status()

def set_led_brightness(led_index, brightness):
    """특정 LED 밝기 설정"""
    brightness = max(0.0, min(1.0, brightness))  # 0.0-1.0 범위로 제한
    leds[led_index].value = brightness
    led_states[led_index] = brightness
    update_led_status()

def execute_light_effect(effect_number):
    """조명 효과 실행"""
    print(f"🎭 조명 효과 {effect_number}번 실행")
    
    # 기존 효과 중단을 위해 모든 LED 끄기
    turn_off_all()
    time.sleep(0.5)
    
    if effect_number == 1:  # 졸리거나 피곤할 때
        print("😴 졸린 상태에 맞는 부드러운 조명 효과를 시작합니다...")
        sine_wave_blinking(0, duration=5, frequency=0.3)  # 빨간색 LED 부드럽게
        gradually_dim(0, duration=3)
        
    elif effect_number == 2:  # 기분이 좋거나 활기찬 상태
        print("😊 활기찬 분위기의 조명 효과를 시작합니다...")
        set_led_brightness(1, 1.0)  # 초록색 LED 밝게
        sine_wave_blinking(2, duration=10, frequency=0.8)  # 파란색 LED 활발하게 깜빡임
        
    elif effect_number == 3:  # 집중이 필요할 때
        print("💡 집중하기 좋은 조명 효과를 시작합니다...")
        set_led_brightness(0, 0.7)  # 빨간색 LED 적당한 밝기
        set_led_brightness(1, 0.7)  # 초록색 LED 적당한 밝기
        
    elif effect_number == 4:  # 편안한 휴식이 필요할 때
        print("🌙 편안한 휴식을 위한 조명 효과를 시작합니다...")
        # 모든 LED를 순차적으로 부드럽게 깜빡이기
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=sine_wave_blinking, 
                args=(i, 8, 0.2), 
                daemon=True
            )
            threads.append(thread)
            thread.start()
            time.sleep(1)  # 1초씩 지연하여 순차 시작
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
            
        # 모든 LED 점점 어둡게
        dim_threads = []
        for i in range(3):
            thread = threading.Thread(
                target=gradually_dim,
                args=(i, 3),
                daemon=True
            )
            dim_threads.append(thread)
            thread.start()
        
        for thread in dim_threads:
            thread.join()
            
    elif effect_number == 5:  # 기분이 우울하거나 슬플 때
        print("💫 기분 전환이 되는 조명 효과를 시작합니다...")
        sine_wave_blinking(2, duration=5, frequency=0.4)  # 파란색 LED 부드럽게
        gradually_brighten(2, duration=3)
        
    elif effect_number == 6:  # 모든 LED 끄기
        turn_off_all()
        
    elif effect_number == 7:  # 모든 LED 켜기
        turn_on_all()
        
    else:
        print(f"⚠️ 알 수 없는 효과 번호: {effect_number}")

def execute_command(command_text):
    """명령 실행"""
    try:
        if "효과:" in command_text:
            # "효과: [번호]" 형식에서 번호 추출
            parts = command_text.split("효과:")[1].strip().split()
            effect_number = int(parts[0])
            
            # 별도 스레드에서 조명 효과 실행 (blocking 방지)
            threading.Thread(
                target=execute_light_effect, 
                args=(effect_number,), 
                daemon=True
            ).start()
        else:
            print("⚠️ 인식할 수 없는 명령 형식입니다.")
    except (ValueError, IndexError) as e:
        print(f"⚠️ 조명 효과를 실행할 수 없습니다: {e}")

def voice_recognition_thread():
    """음성 인식 스레드"""
    global is_recording
    
    if is_recording:
        print("⚠️ 이미 음성 인식이 진행 중입니다.")
        return
    
    is_recording = True
    try:
        spoken = recognize_speech()
        if spoken:
            print(f"🎯 음성 명령 처리 중: {spoken}")
            response = query_chatgpt(spoken)
            print(f"🤖 GPT 명령 해석: {response}")
            execute_command(response)
        else:
            print("❌ 음성 인식 실패")
    except Exception as e:
        print(f"❗ 음성 인식 스레드 오류: {e}")
    finally:
        is_recording = False

def handle_websocket(ws):
    """WebSocket 연결 처리"""
    clients.add(ws)
    print(f"🔌 새로운 WebSocket 클라이언트 연결됨. 총 {len(clients)}개")
    
    try:
        # 연결 즉시 현재 LED 상태 전송
        update_led_status()
        
        while True:
            message = ws.receive()
            if message is None:
                break
                
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'start_recording':
                    print("🎙 음성 인식 시작 요청")
                    threading.Thread(target=voice_recognition_thread, daemon=True).start()
                    
                elif msg_type == 'manual_control':
                    # 수동 LED 제어
                    led_data = data.get('data', {})
                    for color, value in led_data.items():
                        brightness = float(value) / 100.0  # 0-100을 0.0-1.0으로 변환
                        if color == 'red':
                            set_led_brightness(0, brightness)
                        elif color == 'green':
                            set_led_brightness(1, brightness)
                        elif color == 'blue':
                            set_led_brightness(2, brightness)
                            
                elif msg_type == 'effect_control':
                    # 직접 효과 실행
                    effect_num = data.get('effect', 1)
                    threading.Thread(
                        target=execute_light_effect, 
                        args=(effect_num,), 
                        daemon=True
                    ).start()
                    
            except json.JSONDecodeError:
                print("❗ 잘못된 JSON 메시지")
            except Exception as e:
                print(f"❗ 메시지 처리 오류: {e}")
                
    except Exception as e:
        print(f"❗ WebSocket 오류: {e}")
    finally:
        clients.discard(ws)
        print(f"🔌 WebSocket 클라이언트 연결 해제됨. 남은 클라이언트: {len(clients)}개")

def application(environ, start_response):
    """WSGI 애플리케이션"""
    path = environ.get('PATH_INFO', '/')
    
    if path == '/ws':
        if 'wsgi.websocket' in environ:
            handle_websocket(environ['wsgi.websocket'])
        return []
    
    if path == '/':
        try:
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
            with open('templates/index.html', 'rb') as f:
                return [f.read()]
        except Exception as e:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [f'Error: {str(e)}'.encode('utf-8')]
    
    # 404 Not Found
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found']

if __name__ == '__main__':
    try:
        print("🚀 라즈베리파이 LED 제어 시스템 시작")
        print("💡 LED 핀 설정: 빨강(18), 초록(23), 파랑(24)")
        print("🌐 웹 인터페이스: http://127.0.0.1:5000")
        print("🎙️ 음성 명령 지원")
        print("=" * 50)
        
        server = WSGIServer(('0.0.0.0', 5000), application, handler_class=WebSocketHandler)
        print("✅ 서버가 시작되었습니다. http://0.0.0.0:5000")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 사용자가 종료를 요청했습니다.")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")
    finally:
        cleanup_gpio()
        print("👋 프로그램이 종료되었습니다.")