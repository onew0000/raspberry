import RPi.GPIO as GPIO
import time
import math

# GPIO 핀 설정
LED_PINS = {
    'red': 18,
    'green': 23,
    'blue': 24
}

def setup_gpio():
    """GPIO 초기화"""
    try:
        # BCM 모드 사용
        GPIO.setmode(GPIO.BCM)
        
        # 모든 LED 핀을 출력으로 설정
        for pin in LED_PINS.values():
            GPIO.setup(pin, GPIO.OUT)
            # PWM 객체 생성 (주파수: 100Hz)
            GPIO.PWM(pin, 100)
        
        print("✅ GPIO 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ GPIO 초기화 오류: {e}")
        return False

def cleanup_gpio():
    """GPIO 정리"""
    GPIO.cleanup()
    print("🧹 GPIO 정리 완료")

def set_led_brightness(pin, brightness):
    """LED 밝기 설정 (0-100)"""
    try:
        pwm = GPIO.PWM(pin, 100)
        pwm.start(brightness)
        time.sleep(0.1)
        pwm.stop()
    except Exception as e:
        print(f"❌ LED 제어 오류: {e}")

def test_led(pin, color):
    """개별 LED 테스트"""
    print(f"💡 {color} LED 테스트")
    set_led_brightness(pin, 100)  # 켜기
    time.sleep(1)
    set_led_brightness(pin, 0)    # 끄기
    time.sleep(0.5)

def sine_wave_blinking(pin, duration=5):
    """삼각함수 기반 LED 깜빡이기"""
    print(f"✨ LED 깜빡이기 시작")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        t = time.time() - start_time
        brightness = (math.sin(2 * math.pi * t) + 1) * 50  # 0-100 범위로 변환
        set_led_brightness(pin, brightness)
        time.sleep(0.05)

def main():
    if not setup_gpio():
        return
    
    try:
        print("🎮 LED 테스트 시작")
        
        # 각 LED 개별 테스트
        for color, pin in LED_PINS.items():
            test_led(pin, color)
        
        # 삼각함수 기반 깜빡임 테스트
        print("\n✨ 삼각함수 기반 깜빡임 테스트")
        for pin in LED_PINS.values():
            sine_wave_blinking(pin, duration=3)
            time.sleep(0.5)
        
        print("\n✅ 테스트 완료")
        
    except KeyboardInterrupt:
        print("\n🛑 사용자가 종료를 요청했습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        cleanup_gpio()
        print("👋 프로그램이 종료되었습니다.")

if __name__ == '__main__':
    main() 