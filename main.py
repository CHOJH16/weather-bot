import requests
import os
from datetime import datetime

# 1. 깃허브 시크릿에서 정보 가져오기
bot_token = os.environ.get('TELEGRAM_TOKEN')
chat_id = os.environ.get('CHAT_ID')
weather_key = os.environ.get('WEATHER_KEY')

# 서울의 위도, 경도 (OpenWeatherMap 기준)
lat = 37.5665
lon = 126.9780

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_key}&units=metric&lang=kr"
    response = requests.get(url)
    data = response.json()
    
    # 정보 추출
    temp = data['main']['temp'] # 현재 기온
    weather_desc = data['weather'][0]['description'] # 날씨 설명 (맑음, 구름 등)
    weather_id = data['weather'][0]['id'] # 날씨 상태 코드 (비, 눈 등 확인용)
    
    return temp, weather_desc, weather_id

def get_outfit(temp):
    # 당신의 입맛에 맞게 온도를 조절하려면 여기 숫자를 바꾸세요!
    if temp >= 30:
        return "🔥 찜통더위! 민소매, 반바지, 린넨 옷 추천. 손풍기 필수!"
    elif 25 <= temp < 30:
        return "☀️ 덥습니다. 반팔, 얇은 셔츠, 반바지 추천."
    elif 15 <= temp < 25:
        return "🌤 활동하기 좋아요. 얇은 가디건, 긴팔, 면바지 추천."
    elif 8 <= temp < 15:
        return "🍂 선선해요. 얇은 니트, 맨투맨, 가디건 챙기세요."
    elif 2 <= temp < 8:
        return "🧥 쌀쌀합니다. 자켓, 야상, 스타킹, 도톰한 바지 입으세요."
    elif -3 <= temp < 2:
        return "🥶 춥습니다. 코트, 히트텍, 니트, 레깅스 추천."
    else:
        return "❄️ 한파 주의! 패딩, 목도리, 장갑 등 최대한 따뜻하게 입으세요."

def get_umbrella(weather_id):
    # 날씨 코드가 2xx(뇌우), 3xx(이슬비), 5xx(비), 6xx(눈) 인 경우
    if 200 <= weather_id < 700:
        return "\n☂️ 비나 눈 소식이 있어요. 우산을 꼭 챙기세요!"
    return "\n☀️ 우산은 필요 없을 것 같아요."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    try:
        temp, desc, w_id = get_weather()
        outfit = get_outfit(temp)
        umbrella = get_umbrella(w_id)
        
        today_date = datetime.now().strftime("%m월 %d일")
        
        message = f"[{today_date} 아침 날씨 알림]\n\n"
        message += f"📍 서울 기온: {temp}°C\n"
        message += f"☁️ 날씨 상태: {desc}\n\n"
        message += f"👗 옷차림 추천:\n{outfit}\n"
        message += f"{umbrella}"
        
        send_telegram(message)
        print("메시지 전송 완료")
        
    except Exception as e:
        print(f"에러 발생: {e}")
