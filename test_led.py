from gpiozero import PWMLED
import time
import math

# LED 핀 설정
try:
    # 3개의 LED 핀 설정
    leds = [
        PWMLED(18),  # 빨간색 LED
        PWMLED(23),  # 초록색 LED
        PWMLED(24)   # 파란색 LED
    ]
    print("✅ GPIO 초기화 성공")
except Exception as e:
    print(f"❌ GPIO 초기화 오류: {e}")
    exit(1)

def sine_wave_blinking(led_index, duration=5):
    """삼각함수 기반 LED 깜빡이기"""
    print(f"✨ {led_index+1}번 LED 깜빡이기 시작")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        t = time.time() - start_time
        brightness = (math.sin(2 * math.pi * t) + 1) / 2  # 0 ~ 1
        leds[led_index].value = brightness
        time.sleep(0.05)

def test_all_leds():
    """모든 LED 테스트"""
    print("🔴 빨간색 LED 테스트")
    leds[0].on()
    time.sleep(1)
    leds[0].off()
    
    print("🟢 초록색 LED 테스트")
    leds[1].on()
    time.sleep(1)
    leds[1].off()
    
    print("🔵 파란색 LED 테스트")
    leds[2].on()
    time.sleep(1)
    leds[2].off()

def main():
    try:
        print("🎮 LED 테스트 시작")
        
        # 모든 LED 켜기
        print("💡 모든 LED 켜기")
        for led in leds:
            led.on()
        time.sleep(2)
        
        # 모든 LED 끄기
        print("🌑 모든 LED 끄기")
        for led in leds:
            led.off()
        time.sleep(1)
        
        # 각 LED 개별 테스트
        test_all_leds()
        
        # 삼각함수 기반 깜빡임 테스트
        print("\n✨ 삼각함수 기반 깜빡임 테스트")
        for i in range(3):
            sine_wave_blinking(i, duration=3)
            time.sleep(0.5)
        
        print("\n✅ 테스트 완료")
        
    except KeyboardInterrupt:
        print("\n🛑 사용자가 종료를 요청했습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        # 모든 LED 끄기
        for led in leds:
            led.off()
        print("👋 프로그램이 종료되었습니다.")

if __name__ == '__main__':
    main() 