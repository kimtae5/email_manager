import datetime
import email
from email.header import decode_header
import imaplib
import os
import google.genai as genai
import requests

# 1. 메일 가져오기 함수 (IMAP)
def fetch_recent_emails(imap_server, user, password, folder="INBOX"):
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(user, password)
        mail.select(folder)

        # 지난 24시간 동안 수신된 메일 조회
        date_str = (
            datetime.date.today() - datetime.timedelta(days=1)
        ).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{date_str}")')

        email_list = []
        for num in messages[0].split()[-10:]:  # 최근 최대 10개만 추출
            _, data = mail.fetch(num, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 제목 디코딩
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            sender = msg.get("From")
            email_list.append(f"[-발신자]: {sender}\n[-제목]: {subject}")

        mail.logout()
        return email_list
    except Exception as e:
        print(f"{user} 메일 수신 실패: {e}")
        return []


# 2. 메일 데이터 수집
accounts = [
    {
        "provider": "Naver",
        "server": "imap.naver.com",
        "id": os.getenv("NAVER_USER"),
        "pw": os.getenv("NAVER_PW"),
    },
    {
        "provider": "Nate",
        "server": "imap.nate.com",
        "id": os.getenv("NATE_USER"),
        "pw": os.getenv("NATE_PW"),
    },
    {
        "provider": "Gmail",
        "server": "imap.gmail.com",
        "id": os.getenv("GMAIL_USER"),
        "pw": os.getenv("GMAIL_PW"),
    },
]

all_emails_text = ""
for acc in accounts:
    if acc["id"] and acc["pw"]:
        emails = fetch_recent_emails(acc["server"], acc["id"], acc["pw"])
        all_emails_text += f"\n\n=== [{acc['provider']} 메일함] ===\n"
        all_emails_text += (
            "\n".join(emails) if emails else "최근 24시간 내 수신된 메일이 없습니다."
        )

# 3. Gemini API를 이용한 분류 및 요약
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

prompt = f"""
다음은 사용자의 네이버, 네이트, 지메일에서 수신된 최근 24시간 이메일 목록입니다.
이 메일들을 아래 양식에 맞게 한국어로 명확하게 분류하고 요약해주세요.

[요구사항]
1. 🔥 **중요/긴급 메일**: 결제, 보안 알림, 업무 관련 등 바로 확인해야 할 메일
2. 📢 **일반/뉴스레터**: 정보성, 광고, 이벤트 메일
3. 💡 **오늘의 한 줄 브리핑**: 사용자가 아침에 빠르게 파악해야 할 핵심 포인트 요약

[이메일 목록]
{all_emails_text}
"""

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=prompt
)
summary_result = response.text

# 4. 텔레그램 메시지 전송
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

message = f"☀️ **[아침 이메일 일일 브리핑]**\n\n{summary_result}"
requests.post(
    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
    data={
        "chat_id": telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    },
)
