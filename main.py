import datetime
import email
from email.header import decode_header, make_header
import imaplib
import os
import socket
import ssl
import traceback
import time

import google.genai as genai
import requests


# ============================================================
# IMAP 디버깅 출력
# ============================================================

def mask_email(value):
    """이메일 주소를 로그용으로 일부 마스킹"""
    if not value:
        return "(없음)"

    if "@" in value:
        name, domain = value.split("@", 1)

        if len(name) <= 2:
            masked_name = name[0] + "*"
        else:
            masked_name = name[0] + "*" * (len(name) - 1)

        return f"{masked_name}@{domain}"

    return value[:2] + "***"


def print_environment():
    print("\n" + "=" * 70)
    print("🔍 ENVIRONMENT DEBUG")
    print("=" * 70)

    print(f"Python : {os.sys.version}")
    print(f"GitHub Actions : {os.getenv('GITHUB_ACTIONS')}")
    print(f"Runner OS : {os.getenv('RUNNER_OS')}")
    print(f"Runner IP : {os.getenv('GITHUB_RUN_ID')}")

    variables = [
        "NAVER_USER",
        "NAVER_PW",
        "NATE_USER",
        "NATE_PW",
        "GMAIL_USER",
        "GMAIL_PW",
        "GEMINI_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]

    print("\n[Secrets 존재 여부]")

    for name in variables:
        value = os.getenv(name)

        if value:
            if name.endswith("_PW") or "API_KEY" in name or "TOKEN" in name:
                print(f"  {name}: ✅ 설정됨 (값은 숨김)")
            else:
                print(f"  {name}: ✅ {mask_email(value)}")
        else:
            print(f"  {name}: ❌ 없음")

    print("=" * 70)


# ============================================================
# DNS / TCP / SSL 테스트
# ============================================================

def test_network(host, port=993):
    print("\n" + "-" * 70)
    print(f"🌐 NETWORK TEST : {host}:{port}")
    print("-" * 70)

    # --------------------------------------------------------
    # 1. DNS
    # --------------------------------------------------------

    try:
        print(f"[1/3] DNS 조회: {host}")

        addresses = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM
        )

        unique_ips = sorted(
            set(addr[4][0] for addr in addresses)
        )

        print(f"      ✅ DNS 성공")
        print(f"      IP: {unique_ips}")

    except Exception as e:
        print(f"      ❌ DNS 실패")
        print(f"      {type(e).__name__}: {e}")
        return False

    # --------------------------------------------------------
    # 2. TCP
    # --------------------------------------------------------

    sock = None

    try:
        print(f"[2/3] TCP 연결: {host}:{port}")

        start = time.time()

        sock = socket.create_connection(
            (host, port),
            timeout=20
        )

        elapsed = time.time() - start

        print(f"      ✅ TCP 연결 성공 ({elapsed:.2f}s)")

    except Exception as e:
        print(f"      ❌ TCP 연결 실패")
        print(f"      {type(e).__name__}: {e}")

        return False

    # --------------------------------------------------------
    # 3. SSL
    # --------------------------------------------------------

    try:
        print(f"[3/3] SSL/TLS 연결")

        context = ssl.create_default_context()

        ssl_sock = context.wrap_socket(
            sock,
            server_hostname=host
        )

        print("      ✅ SSL 연결 성공")
        print(f"      TLS version : {ssl_sock.version()}")
        print(f"      Cipher      : {ssl_sock.cipher()}")

        try:
            response = ssl_sock.recv(1024)

            print(
                f"      Server greeting : "
                f"{response[:200]!r}"
            )

        except Exception as e:
            print(
                f"      ⚠️ 서버 greeting 읽기 실패: "
                f"{type(e).__name__}: {e}"
            )

        ssl_sock.close()

        return True

    except Exception as e:
        print(f"      ❌ SSL 연결 실패")
        print(f"      {type(e).__name__}: {e}")

        try:
            sock.close()
        except Exception:
            pass

        return False


# ============================================================
# IMAP 메일 수신
# ============================================================

def fetch_recent_emails(
    provider,
    imap_server,
    user,
    password,
    folder="INBOX"
):

    print("\n")
    print("=" * 70)
    print(f"📧 [{provider}] IMAP CONNECTION START")
    print("=" * 70)

    # --------------------------------------------------------
    # Secret 확인
    # --------------------------------------------------------

    print(f"서버     : {imap_server}")
    print(f"포트     : 993")
    print(f"사용자   : {mask_email(user)}")
    print(f"비밀번호 : {'설정됨' if password else '없음'}")
    print(f"폴더     : {folder}")

    if not user:
        print("❌ 사용자 ID가 없습니다.")
        return []

    if not password:
        print("❌ 비밀번호가 없습니다.")
        return []

    # --------------------------------------------------------
    # DNS / TCP / SSL
    # --------------------------------------------------------

    network_ok = test_network(
        imap_server,
        993
    )

    if not network_ok:
        print(
            f"❌ [{provider}] "
            f"네트워크 단계에서 실패했습니다."
        )

        return []

    # --------------------------------------------------------
    # IMAP SSL 연결
    # --------------------------------------------------------

    mail = None

    try:

        print("\n[IMAP 1/5] IMAP4_SSL 객체 생성")

        context = ssl.create_default_context()

        mail = imaplib.IMAP4_SSL(
            host=imap_server,
            port=993,
            ssl_context=context,
            timeout=30
        )

        print("      ✅ IMAP SSL 연결 성공")

        # ----------------------------------------------------
        # IMAP 서버 응답
        # ----------------------------------------------------

        print("\n[IMAP 2/5] 서버 응답 확인")

        print(f"      {mail.welcome!r}")

        # ----------------------------------------------------
        # 로그인
        # ----------------------------------------------------

        print("\n[IMAP 3/5] 로그인 시도")

        print(
            f"      username = {mask_email(user)}"
        )

        login_status, login_data = mail.login(
            user,
            password
        )

        print(
            f"      login status = {login_status}"
        )

        print(
            f"      login data   = {login_data!r}"
        )

        if login_status != "OK":
            print("❌ 로그인 실패")

            try:
                mail.logout()
            except Exception:
                pass

            return []

        print("      ✅ 로그인 성공")

        # ----------------------------------------------------
        # 폴더 선택
        # ----------------------------------------------------

        print(
            f"\n[IMAP 4/5] 폴더 선택: {folder}"
        )

        select_status, select_data = mail.select(
            folder,
            readonly=True
        )

        print(
            f"      select status = {select_status}"
        )

        print(
            f"      select data   = {select_data!r}"
        )

        if select_status != "OK":
            print("❌ INBOX 선택 실패")

            try:
                mail.logout()
            except Exception:
                pass

            return []

        print("      ✅ INBOX 선택 성공")

        # ----------------------------------------------------
        # 최근 24시간 메일 검색
        # ----------------------------------------------------

        date_str = (
            datetime.date.today()
            - datetime.timedelta(days=1)
        ).strftime("%d-%b-%Y")

        print(
            f"\n[IMAP 5/5] 메일 검색"
        )

        print(
            f"      검색 조건: SINCE {date_str}"
        )

        search_status, messages = mail.search(
            None,
            f'(SINCE "{date_str}")'
        )

        print(
            f"      search status = {search_status}"
        )

        print(
            f"      search data   = {messages!r}"
        )

        if search_status != "OK":
            print("❌ 메일 검색 실패")

            try:
                mail.logout()
            except Exception:
                pass

            return []

        # ----------------------------------------------------
        # 메일 번호
        # ----------------------------------------------------

        if not messages or not messages[0]:

            print(
                "      ℹ️ 최근 24시간 메일 없음"
            )

            try:
                mail.logout()
            except Exception:
                pass

            return []

        mail_numbers = messages[0].split()

        print(
            f"      총 검색된 메일: "
            f"{len(mail_numbers)}개"
        )

        # 최근 10개
        mail_numbers = mail_numbers[-10:]

        print(
            f"      실제 가져올 메일: "
            f"{len(mail_numbers)}개"
        )

        email_list = []

        # ----------------------------------------------------
        # 메일 가져오기
        # ----------------------------------------------------

        for index, num in enumerate(
            mail_numbers,
            start=1
        ):

            print(
                f"\n      📩 메일 {index}/"
                f"{len(mail_numbers)}"
                f" UID/번호={num!r}"
            )

            try:

                fetch_status, data = mail.fetch(
                    num,
                    "(RFC822)"
                )

                print(
                    f"         fetch status = "
                    f"{fetch_status}"
                )

                if fetch_status != "OK":
                    print(
                        "         ❌ fetch 실패"
                    )
                    continue

                if not data:
                    print(
                        "         ❌ fetch data 없음"
                    )
                    continue

                raw_email = None

                for item in data:
                    if (
                        isinstance(item, tuple)
                        and len(item) >= 2
                    ):
                        raw_email = item[1]
                        break

                if not raw_email:
                    print(
                        "         ❌ 이메일 원본 없음"
                    )
                    continue

                msg = email.message_from_bytes(
                    raw_email
                )

                # 제목
                subject_header = msg["Subject"]

                if subject_header:
                    try:
                        subject = str(
                            make_header(
                                decode_header(
                                    subject_header
                                )
                            )
                        )
                    except Exception:
                        subject = str(
                            subject_header
                        )
                else:
                    subject = "(제목 없음)"

                sender = msg.get(
                    "From",
                    "알 수 없음"
                )

                email_list.append(
                    f"[-발신자]: {sender}\n"
                    f"[-제목]: {subject}"
                )

                print(
                    f"         발신자: {sender}"
                )

                print(
                    f"         제목: {subject}"
                )

            except Exception as e:

                print(
                    f"         ❌ 메일 처리 실패: "
                    f"{type(e).__name__}: {e}"
                )

                traceback.print_exc()

        # ----------------------------------------------------
        # Logout
        # ----------------------------------------------------

        try:

            logout_status, logout_data = (
                mail.logout()
            )

            print(
                f"\n🚪 logout: "
                f"{logout_status} / "
                f"{logout_data!r}"
            )

        except Exception as e:

            print(
                f"\n⚠️ logout 실패: "
                f"{type(e).__name__}: {e}"
            )

        print("\n" + "=" * 70)

        print(
            f"✅ [{provider}] "
            f"메일 수신 완료: "
            f"{len(email_list)}개"
        )

        print("=" * 70)

        return email_list

    # --------------------------------------------------------
    # 전체 IMAP 오류
    # --------------------------------------------------------

    except imaplib.IMAP4.error as e:

        print("\n" + "!" * 70)

        print(
            f"❌ [{provider}] IMAP 프로토콜 오류"
        )

        print(
            f"Exception type: {type(e).__name__}"
        )

        print(
            f"Exception: {e!r}"
        )

        print("!" * 70)

        traceback.print_exc()

        return []

    except socket.timeout as e:

        print("\n" + "!" * 70)

        print(
            f"❌ [{provider}] Socket TIMEOUT"
        )

        print(
            f"Exception: {e!r}"
        )

        print("!" * 70)

        traceback.print_exc()

        return []

    except ssl.SSLError as e:

        print("\n" + "!" * 70)

        print(
            f"❌ [{provider}] SSL/TLS 오류"
        )

        print(
            f"Exception type: {type(e).__name__}"
        )

        print(
            f"Exception: {e!r}"
        )

        print("!" * 70)

        traceback.print_exc()

        return []

    except Exception as e:

        print("\n" + "!" * 70)

        print(
            f"❌ [{provider}] IMAP 알 수 없는 오류"
        )

        print(
            f"Exception type: {type(e).__name__}"
        )

        print(
            f"Exception: {e!r}"
        )

        print("!" * 70)

        traceback.print_exc()

        return []

    finally:

        if mail is not None:

            try:
                mail.shutdown()
            except Exception:
                pass


# ============================================================
# 프로그램 시작
# ============================================================

print("\n")
print("#" * 70)
print("🚀 DAILY EMAIL AGENT START")
print("#" * 70)

print_environment()


# ============================================================
# 메일 계정
# ============================================================

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


# ============================================================
# 메일 수집
# ============================================================

all_emails_text = ""

for acc in accounts:

    print("\n")
    print(
        "📧 PROCESS ACCOUNT:",
        acc["provider"]
    )

    if acc["id"] and acc["pw"]:

        emails = fetch_recent_emails(
            provider=acc["provider"],
            imap_server=acc["server"],
            user=acc["id"],
            password=acc["pw"]
        )

        all_emails_text += (
            f"\n\n=== "
            f"[{acc['provider']} 메일함] "
            f"===\n"
        )

        all_emails_text += (
            "\n".join(emails)
            if emails
            else
            "최근 24시간 내 수신된 메일이 "
            "없거나 로그인에 실패했습니다."
        )

    else:

        print(
            f"⚠️ [{acc['provider']}] "
            f"Secret 없음 → 건너뜀"
        )


# ============================================================
# Gemini
# ============================================================

print("\n")
print("=" * 70)
print("🤖 GEMINI START")
print("=" * 70)

gemini_key = os.getenv(
    "GEMINI_API_KEY"
)

if not gemini_key:

    print(
        "❌ GEMINI_API_KEY 없음"
    )

    summary_result = (
        "Gemini API KEY가 설정되지 않았습니다."
    )

else:

    try:

        client = genai.Client(
            api_key=gemini_key
        )

        prompt = f"""
다음은 사용자의 네이버, 네이트, 지메일에서
수신된 최근 24시간 이메일 목록입니다.

이 메일들을 아래 양식에 맞게
한국어로 명확하게 분류하고 요약해주세요.

[요구사항]

1. 🔥 중요/긴급 메일
결제, 보안 알림, 업무 관련 등
바로 확인해야 할 메일

2. 📢 일반/뉴스레터
정보성, 광고, 이벤트 메일

3. 💡 오늘의 한 줄 브리핑
사용자가 아침에 빠르게 파악해야 할
핵심 포인트 요약

[이메일 목록]

{all_emails_text}
"""

        print(
            "Gemini API 호출 중..."
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        summary_result = response.text

        print("✅ Gemini 성공")
        print(
            f"결과 길이: "
            f"{len(summary_result)}"
        )

    except Exception as e:

        print(
            f"❌ Gemini 실패: "
            f"{type(e).__name__}: {e}"
        )

        traceback.print_exc()

        summary_result = (
            "Gemini 요약 생성에 실패했습니다."
        )


# ============================================================
# Telegram
# ============================================================

print("\n")
print("=" * 70)
print("📱 TELEGRAM START")
print("=" * 70)

telegram_token = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

telegram_chat_id = os.getenv(
    "TELEGRAM_CHAT_ID"
)

if (
    not telegram_token
    or not telegram_chat_id
):

    print(
        "❌ TELEGRAM Secret 없음"
    )

else:

    try:

        message = (
            "☀️ [아침 이메일 일일 브리핑]\n\n"
            + summary_result
        )

        url = (
            "https://api.telegram.org/"
            f"bot{telegram_token}/sendMessage"
        )

        payload = {
            "chat_id": telegram_chat_id,
            "text": message
        }

        print(
            f"Telegram chat_id: "
            f"{telegram_chat_id}"
        )

        print(
            f"메시지 길이: "
            f"{len(message)}"
        )

        res = requests.post(
            url,
            data=payload,
            timeout=30
        )

        print(
            f"📡 Telegram HTTP status: "
            f"{res.status_code}"
        )

        print(
            f"📡 Telegram response: "
            f"{res.text}"
        )

        if res.ok:

            print(
                "✅ Telegram 전송 성공"
            )

        else:

            print(
                "❌ Telegram 전송 실패"
            )

    except Exception as e:

        print(
            f"❌ Telegram 오류: "
            f"{type(e).__name__}: {e}"
        )

        traceback.print_exc()


print("\n")
print("#" * 70)
print("🏁 DAILY EMAIL AGENT END")
print("#" * 70)
