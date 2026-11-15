import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
KST = timezone(timedelta(hours=9))

# GitHub Secrets에 등록된 기존 값을 그대로 사용합니다.
bot_token = (os.environ.get("TELEGRAM_TOKEN") or "").strip()
chat_ids_raw = os.environ.get("CHAT_ID") or ""

# 쉼표로 구분한 여러 수신자를 지원합니다.
# 중복된 ID는 한 번만 사용합니다.
chat_ids = list(
    dict.fromkeys(
        chat_id.strip()
        for chat_id in chat_ids_raw.split(",")
        if chat_id.strip()
    )
)

# 서울 위도와 경도
lat = 37.5665
lon = 126.9780


# ---------------------------------------------------------
# 로그 출력
# ---------------------------------------------------------
def log(message):
    # 오류 메시지에 토큰이 포함되더라도 로그에서는 가립니다.
    text = str(message)

    if bot_token:
        text = text.replace(bot_token, "[TOKEN_HIDDEN]")

    print(text, flush=True)


# ---------------------------------------------------------
# 필수 설정 확인
# ---------------------------------------------------------
def validate_settings():
    if not bot_token:
        raise RuntimeError(
            "TELEGRAM_TOKEN이 없습니다. "
            "GitHub 저장소의 Secrets 설정을 확인하세요."
        )

    if not chat_ids:
        raise RuntimeError(
            "CHAT_ID가 없습니다. "
            "GitHub 저장소의 Secrets 설정을 확인하세요."
        )


# ---------------------------------------------------------
# 한국 시간 기준 목표 시각까지 대기
# ---------------------------------------------------------
def wait_until_target_time(target_hour, target_minute):
    now = datetime.now(KST)

    target_time = now.replace(
        hour=target_hour,
        minute=target_minute,
        second=0,
        microsecond=0,
    )

    log(f"🕒 현재 한국 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    if now < target_time:
        wait_seconds = (target_time - now).total_seconds()

        log(f"🎯 목표 시간: {target_time.strftime('%H:%M:%S')}")
        log(f"⏳ 약 {wait_seconds / 60:.1f}분 동안 대기합니다.")

        time.sleep(wait_seconds)

        log("🚀 대기 종료! 날씨 정보를 가져옵니다.")
    else:
        log("⚠️ 이미 목표 시간이 지났습니다. 즉시 실행합니다.")


# ---------------------------------------------------------
# 날씨 정보 가져오기
# 통신 실패 또는 서버 오류 시 최대 4회 시도
# ---------------------------------------------------------
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Asia/Seoul",
        "forecast_days": 1,
    }

    max_attempts = 4
    retry_delays = [10, 20, 40]

    for attempt in range(1, max_attempts + 1):
        try:
            log(f"🌤 날씨 정보 요청 중... ({attempt}/{max_attempts})")

            response = requests.get(
                url,
                params=params,
                timeout=(10, 30),
            )

            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                raise ValueError(
                    f"날씨 API 오류: {data.get('reason', '원인 미상')}"
                )

            current = data["current_weather"]
            daily = data["daily"]

            temp_now = current["temperature"]
            w_code = current["weathercode"]
            temp_min = daily["temperature_2m_min"][0]
            temp_max = daily["temperature_2m_max"][0]

            if any(
                value is None
                for value in (temp_now, temp_min, temp_max, w_code)
            ):
                raise ValueError("날씨 응답에 누락된 값이 있습니다.")

            log("✅ 날씨 정보 수신 완료")

            return temp_now, temp_min, temp_max, w_code

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code

            # 일반적인 요청 오류는 재시도하지 않습니다.
            # 다만 HTTP 429(요청 제한)는 잠시 기다렸다 재시도합니다.
            if status < 500 and status != 429:
                raise RuntimeError(
                    f"날씨 API HTTP {status} 오류입니다. "
                    "요청 조건이나 API 이용 제한을 확인해야 합니다."
                ) from None

            error_message = f"날씨 API HTTP {status} 오류"

        except (
            requests.exceptions.RequestException,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as e:
            error_message = f"{type(e).__name__}: {e}"

        log(f"⚠️ 날씨 조회 실패: {error_message}")

        if attempt < max_attempts:
            delay = retry_delays[attempt - 1]

            log(f"🔄 {delay}초 후 다시 시도합니다.")
            time.sleep(delay)
        else:
            raise RuntimeError(
                f"날씨 정보를 {max_attempts}번 요청했지만 실패했습니다. "
                f"마지막 오류: {error_message}"
            ) from None


# ---------------------------------------------------------
# 날씨 상태 설명
# ---------------------------------------------------------
def get_weather_desc(w_code):
    if w_code == 0:
        return "맑음 ☀️"
    elif w_code in (1, 2, 3):
        return "구름 조금/흐림 ☁️"
    elif w_code in (45, 48):
        return "안개 🌫️"
    elif w_code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67):
        return "비/이슬비 🌧️"
    elif w_code in (71, 73, 75, 77):
        return "눈 ❄️"
    elif w_code in (80, 81, 82):
        return "소나기 ☔"
    elif w_code in (85, 86):
        return "눈 소나기 ☃️"
    elif w_code in (95, 96, 99):
        return "뇌우(천둥번개) ⚡"
    else:
        return "정보 없음"


# ---------------------------------------------------------
# 현재 기온 기준 옷차림 추천
# ---------------------------------------------------------
def get_outfit(temp):
    if temp >= 30:
        return "🔥 찜통더위! 민소매, 반바지, 린넨 옷 추천. 손풍기 필수!"
    elif temp >= 21:
        return "☀️ 덥습니다. 반팔, 얇은 셔츠, 반바지 추천."
    elif temp >= 16:
        return "🌤 활동하기 좋아요. 얇은 가디건, 긴팔, 면바지 추천."
    elif temp >= 10:
        return "🍂 선선해요. 얇은 니트, 맨투맨, 가디건 챙기세요."
    elif temp >= 5:
        return "🧥 쌀쌀합니다. 자켓, 야상, 스타킹, 도톰한 바지 입으세요."
    elif temp >= -3:
        return "🥶 춥습니다. 코트, 히트텍, 니트, 레깅스 추천."
    else:
        return "❄️ 한파 주의! 패딩, 목도리, 장갑 등 최대한 따뜻하게 입으세요."


# ---------------------------------------------------------
# 현재 날씨 상태 기준 우산 안내
# 하루 전체 강수 예보를 의미하는 것은 아닙니다.
# ---------------------------------------------------------
def get_umbrella(w_code):
    precipitation_codes = {
        51, 53, 55, 56, 57,
        61, 63, 65, 66, 67,
        71, 73, 75, 77,
        80, 81, 82,
        85, 86,
        95, 96, 99,
    }

    if w_code in precipitation_codes:
        return "☂️ 현재 비나 눈이 오는 날씨입니다. 우산을 챙기세요!"

    return "🌂 현재 강수 상태는 아닙니다. 외출 전 시간대별 예보도 확인하세요."


# ---------------------------------------------------------
# 텔레그램 전송
# 수신자가 여러 명이면 각각 전송합니다.
# 중복 발송을 피하기 위해 전송을 자동 재시도하지 않습니다.
# ---------------------------------------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    failed_count = 0

    for index, chat_id in enumerate(chat_ids, start=1):
        try:
            log(f"📨 텔레그램 전송 중... ({index}/{len(chat_ids)})")

            response = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                },
                timeout=(10, 30),
            )

            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                raise RuntimeError(
                    result.get("description", "텔레그램 전송 실패")
                )

            log(f"✅ 텔레그램 전송 성공 ({index}/{len(chat_ids)})")

        except (
            requests.exceptions.RequestException,
            ValueError,
            RuntimeError,
        ) as e:
            failed_count += 1

            log(
                f"❌ 텔레그램 전송 실패 또는 결과 확인 불가 "
                f"({index}/{len(chat_ids)}): {e}"
            )

    if failed_count:
        raise RuntimeError(
            f"수신 대상 {len(chat_ids)}곳 중 "
            f"{failed_count}곳의 전송이 실패했거나 확인되지 않았습니다. "
            "응답만 받지 못한 경우 실제로는 전송됐을 수 있습니다."
        )


# ---------------------------------------------------------
# 실행
# ---------------------------------------------------------
def main():
    validate_settings()

    # 한국 시간 오전 6시 30분 전이면 기다립니다.
    # 이미 지난 경우 즉시 실행합니다.
    wait_until_target_time(6, 30)

    temp_now, temp_min, temp_max, w_code = get_weather()

    desc = get_weather_desc(w_code)
    outfit = get_outfit(temp_now)
    umbrella = get_umbrella(w_code)

    today_date = datetime.now(KST).strftime("%m월 %d일")

    message = (
        f"[{today_date} 아침 날씨 알림]\n\n"
        f"📍 서울 현재: {temp_now}°C\n"
        f"📉 최저: {temp_min}°C / 📈 최고: {temp_max}°C\n"
        f"☁️ 현재 날씨: {desc}\n\n"
        f"👗 옷차림 추천:\n{outfit}\n\n"
        f"{umbrella}"
    )

    send_telegram(message)

    log("🎉 모든 수신자에게 메시지 전송 완료")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ 실행 실패: {e}")
        sys.exit(1)
