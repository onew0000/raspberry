import RPi.GPIO as GPIO
import time
import math
import threading
import sys
import select
import tty
import termios

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
pwm = GPIO.PWM(17, 1000)  # 1kHz 주파수
pwm.start(0)

# 전역 변수
current_mode = 0
running = True

def get_char():
    """비블로킹 키 입력 받기"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)  # cbreak를 setcbreak로 수정
        if select.select([sys.stdin], [], [], 0.1):
            ch = sys.stdin.read(1)
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def calm_wave():
    """차분한 파형 - 느린 사인파"""
    t = 0
    while current_mode == 1 and running:
        try:
            # 느린 사인파, 부드러운 변화
            brightness = 50 + 40 * math.sin(t * 0.5)  # 10~90% 밝기
            pwm.ChangeDutyCycle(max(0, min(100, brightness)))
            t += 0.1
            time.sleep(0.05)
        except Exception as e:
            print(f"calm_wave 오류: {e}")
            break

def exciting_wave():
    """신나는 파형 - 빠른 복합파"""
    t = 0
    while current_mode == 2 and running:
        try:
            # 빠른 사인파 + 코사인파 조합
            base_wave = math.sin(t * 3)
            accent_wave = 0.3 * math.cos(t * 7)
            brightness = 60 + 35 * (base_wave + accent_wave)
            pwm.ChangeDutyCycle(max(0, min(100, brightness)))
            t += 0.1
            time.sleep(0.02)
        except Exception as e:
            print(f"exciting_wave 오류: {e}")
            break

def sad_wave():
    """우울한 파형 - 불규칙한 저주파"""
    t = 0
    while current_mode == 3 and running:
        try:
            # 낮은 밝기에서 천천히 변화하는 복합파
            slow_wave = math.sin(t * 0.3)
            irregular_wave = 0.2 * math.sin(t * 1.7)
            brightness = 20 + 25 * (slow_wave + irregular_wave)
            pwm.ChangeDutyCycle(max(5, min(50, brightness)))  # 최대 50%까지만
            t += 0.1
            time.sleep(0.08)
        except Exception as e:
            print(f"sad_wave 오류: {e}")
            break

def focus_wave():
    """집중력 있는 파형 - 규칙적인 펄스"""
    t = 0
    while current_mode == 4 and running:
        try:
            # 규칙적인 펄스파 (사각파 형태의 삼각함수)
            base_sin = math.sin(t * 2)
            # 사인파를 이용해 펄스 형태 만들기
            if base_sin > 0.5:
                brightness = 80
            elif base_sin > -0.5:
                brightness = 60
            else:
                brightness = 40
            
            # 부드러운 전환을 위한 추가 사인파
            smooth = 10 * math.sin(t * 8)
            final_brightness = brightness + smooth
            
            pwm.ChangeDutyCycle(max(0, min(100, final_brightness)))
            t += 0.1
            time.sleep(0.03)
        except Exception as e:
            print(f"focus_wave 오류: {e}")
            break

def stop_lighting():
    """조명 끄기"""
    try:
        pwm.ChangeDutyCycle(0)
    except Exception as e:
        print(f"stop_lighting 오류: {e}")

def cleanup():
    """GPIO 정리"""
    try:
        pwm.stop()
        GPIO.cleanup()
    except Exception as e:
        print(f"cleanup 오류: {e}")

def main():
    global current_mode, running
    
    print("=== 감정별 조명 제어 시스템 ===")
    print("1: 차분한 조명 (느린 사인파)")
    print("2: 신나는 조명 (빠른 복합파)")
    print("3: 우울한 조명 (불규칙한 저주파)")
    print("4: 집중 조명 (규칙적인 펄스)")
    print("0: 조명 끄기")
    print("q: 종료")
    print("\n키를 눌러 모드를 선택하세요...")
    
    lighting_thread = None
    
    try:
        while running:
            key = get_char()
            
            if key:
                # 이전 스레드 종료
                if lighting_thread and lighting_thread.is_alive():
                    current_mode = 0
                    lighting_thread.join(timeout=1)
                
                if key == '1':
                    print("차분한 조명 모드 활성화")
                    current_mode = 1
                    lighting_thread = threading.Thread(target=calm_wave)
                    lighting_thread.daemon = True
                    lighting_thread.start()
                    
                elif key == '2':
                    print("신나는 조명 모드 활성화")
                    current_mode = 2
                    lighting_thread = threading.Thread(target=exciting_wave)
                    lighting_thread.daemon = True
                    lighting_thread.start()
                    
                elif key == '3':
                    print("우울한 조명 모드 활성화")
                    current_mode = 3
                    lighting_thread = threading.Thread(target=sad_wave)
                    lighting_thread.daemon = True
                    lighting_thread.start()
                    
                elif key == '4':
                    print("집중 조명 모드 활성화")
                    current_mode = 4
                    lighting_thread = threading.Thread(target=focus_wave)
                    lighting_thread.daemon = True
                    lighting_thread.start()
                    
                elif key == '0':
                    print("조명 끄기")
                    current_mode = 0
                    stop_lighting()
                    
                elif key == 'q' or key == 'Q':
                    print("프로그램을 종료합니다.")
                    running = False
                    break
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    
    finally:
        current_mode = 0
        running = False
        if lighting_thread and lighting_thread.is_alive():
            lighting_thread.join(timeout=1)
        cleanup()

if __name__ == "__main__":
    main() 