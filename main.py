import requests
import os
import time
from datetime import datetime, timedelta, timezone

# 1. 텔레그램 정보 가져오기
bot_token = os.environ.get('TELEGRAM_TOKEN')
chat_ids_raw = os.environ.get('CHAT_ID')

# ID가 하나든 여러 개든(쉼표) 알아서 처리
if chat_ids_raw:
    chat_ids = chat_ids_raw.split(',')
else:
    chat_ids = []

# 서울의 위도, 경도
lat = 37.5665
lon = 126.9780

# ---------------------------------------------------------
# [대기 기능] 목표 시간까지 기다리는 함수
# ---------------------------------------------------------
def wait_until_target_time(target_hour, target_minute):
    # 한국 시간(KST) 기준
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    
    # 오늘의 목표 시간 (아침 6시 30분 00초)
    target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    # 현재 시간이 목표 시간보다 전이면 (예: 6시 05분 -> 6시 30분까지 대기)
    if now < target_time:
        wait_seconds = (target_time - now).total_seconds()
        print(f"⏰ 현재 시간(KST): {now.strftime('%H:%M:%S')}")
        print(f"🎯 목표 시간(KST): {target_time.strftime('%H:%M:%S')}")
        print(f"⏳ 약 {wait_seconds / 60:.1f}분 동안 대기합니다...")
        
        time.sleep(wait_seconds)
        print("🚀 대기 종료! 메시지를 전송합니다.")
    else:
        print("⚠️ 이미 목표 시간이 지났습니다. 즉시 실행합니다.")

# ---------------------------------------------------------
# 날씨 및 메시지 로직
# ---------------------------------------------------------
def get_weather():
    # Open-Meteo (무료, 키 불필요)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FSeoul"
    response = requests.get(url)
    data = response.json()
    
    current = data['current_weather']
    temp_now = current['temperature']
    w_code = current['weathercode']
    
    daily = data['daily']
    temp_max = daily['temperature_2m_max'][0]
    temp_min = daily['temperature_2m_min'][0]
    
    return temp_now, temp_min, temp_max, w_code

def get_weather_desc(w_code):
    if w_code == 0: return "맑음 ☀️"
    elif 1 <= w_code <= 3: return "구름 조금/흐림 ☁️"
    elif 45 <= w_code <= 48: return "안개 🌫️"
    elif 51 <= w_code <= 67: return "비/이슬비 🌧️"
    elif 71 <= w_code <= 77: return "눈 ❄️"
    elif 80 <= w_code <= 82: return "소나기 ☔"
    elif 85 <= w_code <= 86: return "눈보라 ☃️"
    elif 95 <= w_code <= 99: return "뇌우(천둥번개) ⚡"
    else: return "정보 없음"

def get_outfit(temp):
    if temp >= 30:
        return "🔥 찜통더위! 민소매, 반바지, 린넨 옷 추천. 손풍기 필수!"
    elif 21 <= temp < 30:
        return "☀️ 덥습니다. 반팔, 얇은 셔츠, 반바지 추천."
    elif 16 <= temp < 21:
        return "🌤 활동하기 좋아요. 얇은 가디건, 긴팔, 면바지 추천."
    elif 10 <= temp < 16:
        return "🍂 선선해요. 얇은 니트, 맨투맨, 가디건 챙기세요."
    elif 5 <= temp < 10:
        return "🧥 쌀쌀합니다. 자켓, 야상, 스타킹, 도톰한 바지 입으세요."
    elif -3 <= temp < 5:
        return "🥶 춥습니다. 코트, 히트텍, 니트, 레깅스 추천."
    else:
        return "❄️ 한파 주의! 패딩, 목도리, 장갑 등 최대한 따뜻하게 입으세요."

def get_umbrella(w_code):
    if w_code >= 50:
        return "\n☂️ 비나 눈 소식이 있어요. 우산을 꼭 챙기세요!"
    return "\n☀️ 우산은 필요 없을 것 같아요."

def send_telegram(message):
    for chat_id in chat_ids:
        clean_id = chat_id.strip()
        if not clean_id: continue
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': clean_id,
            'text': message
        }
        requests.post(url, json=payload)

if __name__ == "__main__":
    try:
        # 1. 6시 30분이 될 때까지 대기
        wait_until_target_time(6, 30)

        # 2. 날씨 정보 가져오기
        temp_now, temp_min, temp_max, w_code = get_weather()
        desc = get_weather_desc(w_code)
        outfit = get_outfit(temp_now)
        umbrella = get_umbrella(w_code)
        
        # 3. 메시지 만들기
        today_date = datetime.now(timezone(timedelta(hours=9))).strftime("%m월 %d일")
        
        message = f"[{today_date} 아침 날씨 알림]\n\n"
        message += f"📍 서울 현재: {temp_now}°C\n"
        message += f"📉 최저: {temp_min}°C / 📈 최고: {temp_max}°C\n"
        message += f"☁️ 날씨 상태: {desc}\n\n"
        message += f"👗 옷차림 추천:\n{outfit}\n"
        message += f"{umbrella}"
        
        # 4. 전송
        send_telegram(message)
        print("메시지 전송 완료")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        exit(1)
