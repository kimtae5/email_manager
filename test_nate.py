import os
import imaplib
import ssl
import socket
import requests


USER = os.getenv("NATE_USER")
PASSWORD = os.getenv("NATE_PW")


print("=" * 60)
print("NATE IMAP TEST")
print("=" * 60)

print("NATE_USER:", repr(USER))
print("NATE_USER length:", len(USER) if USER else 0)
print("NATE_PW:", "설정됨" if PASSWORD else "없음")


# ============================================================
# 네트워크 정보
# ============================================================

print()
print("[NETWORK INFORMATION]")

try:
    print(
        "imap.nate.com IP:",
        socket.gethostbyname("imap.nate.com")
    )
except Exception as e:
    print("DNS ERROR:", e)


try:
    public_ip = requests.get(
        "https://api.ipify.org",
        timeout=10
    ).text

    print("GitHub Runner Public IP:", public_ip)

except Exception as e:
    print("Public IP 확인 실패:", e)


# ============================================================
# IMAP 연결
# ============================================================

print()
print("[1] IMAP SSL 연결")

context = ssl.create_default_context()

mail = imaplib.IMAP4_SSL(
    "imap.nate.com",
    993,
    ssl_context=context,
    timeout=30
)

print("✅ SSL 연결 성공")
print("WELCOME:", mail.welcome)


# ============================================================
# LOGIN
# ============================================================

print()
print("[2] Nate 로그인")

try:

    result = mail.login(
        USER,
        PASSWORD
    )

    print("LOGIN RESULT:", result)
    print("✅ Nate 로그인 성공")

except Exception as e:

    print("❌ Nate 로그인 실패")
    print("Exception:", type(e).__name__)
    print("Message:", repr(e))

    raise


# ============================================================
# INBOX
# ============================================================

print()
print("[3] INBOX 선택")

try:

    result = mail.select(
        "INBOX",
        readonly=True
    )

    print("INBOX RESULT:", result)

    if result[0] == "OK":
        print("✅ INBOX 선택 성공")
    else:
        print("❌ INBOX 선택 실패")

except Exception as e:

    print("❌ INBOX 선택 오류")
    print("Exception:", type(e).__name__)
    print("Message:", repr(e))

    raise


# ============================================================
# 종료
# ============================================================

print()
print("[4] 종료")

try:
    mail.logout()
    print("✅ Logout 성공")
except Exception as e:
    print("Logout 오류:", e)


print()
print("=" * 60)
print("NATE IMAP TEST COMPLETE")
print("=" * 60)
