import requests
import os
from datetime import datetime

# 1. 텔레그램 정보만 가져오기 (날씨 키는 필요 없음!)
bot_token = os.environ.get('TELEGRAM_TOKEN')
chat_id = os.environ.get('CHAT_ID')

# 서울의 위도, 경도
lat = 37.5665
lon = 126.9780

def get_weather():
    # Open-Meteo API 호출 (키 없이 무료 사용 가능)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia%2FSeoul"
    response = requests.get(url)
    data = response.json()
    
    # 정보 추출
    current = data['current_weather']
    temp = current['temperature'] # 현재 기온
    w_code = current['weathercode'] # 날씨 코드 (WMO 기준)
    
    return temp, w_code

def get_weather_desc(w_code):
    # WMO 날씨 코드를 한글 설명으로 변환
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

def get_umbrella(w_code):
    # 비(51~67), 눈(71~77), 소나기(80~82), 뇌우(95~99) 인 경우
    if w_code >= 50:
        return "\n☂️ 비나 눈 소식이 있어요. 우산을 꼭 챙기세요!"
    return "\n☀️ 우산은 필요 없을 것 같아요."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"텔레그램 전송 실패: {response.text}")

if __name__ == "__main__":
    try:
        print("날씨 정보 요청 중 (Open-Meteo)...")
        temp, w_code = get_weather()
        desc = get_weather_desc(w_code)
        
        print(f"정보 수신 성공: {temp}도, 코드 {w_code}")
        
        outfit = get_outfit(temp)
        umbrella = get_umbrella(w_code)
        
        today_date = datetime.now().strftime("%m월 %d일")
        
        message = f"[{today_date} 아침 날씨 알림]\n\n"
        message += f"📍 서울 기온: {temp}°C\n"
        message += f"☁️ 날씨 상태: {desc}\n\n"
        message += f"👗 옷차림 추천:\n{outfit}\n"
        message += f"{umbrella}"
        
        send_telegram(message)
        print("메시지 전송 완료")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        exit(1)
