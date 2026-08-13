import imaplib
import os
import socket

USER = os.getenv("NATE_USER")
PASSWORD = os.getenv("NATE_PW")

print("=" * 60)
print("NATE IMAP AUTH TEST")
print("=" * 60)

print("USER:", repr(USER))
print("USER length:", len(USER) if USER else 0)
print("PW exists:", bool(PASSWORD))
print("PW length:", len(PASSWORD) if PASSWORD else 0)

print()
print("[NETWORK]")

print(
    "NATE IP:",
    socket.gethostbyname("imap.nate.com")
)

print()
print("[IMAP]")

mail = imaplib.IMAP4_SSL(
    "imap.nate.com",
    993,
    timeout=30
)

print("WELCOME:", repr(mail.welcome))

print()
print("[CAPABILITY]")

try:
    print(mail.capability())
except Exception as e:
    print("CAPABILITY ERROR:", repr(e))

print()
print("[LOGIN]")

try:

    result = mail.login(
        USER,
        PASSWORD
    )

    print("LOGIN RESULT:", result)

except Exception as e:

    print("LOGIN FAILED")
    print("TYPE:", type(e).__name__)
    print("ERROR:", repr(e))

    raise

finally:

    try:
        mail.logout()
    except:
        pass
