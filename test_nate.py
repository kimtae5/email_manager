import imaplib
import os
import socket
import ssl

USER = os.getenv("NATE_USER")
PASSWORD = os.getenv("NATE_PW")

print("=" * 70)
print("NATE IMAP AUTH TEST")
print("=" * 70)

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

print("WELCOME:")
print(mail.welcome)

print()
print("CAPABILITY:")
print(mail.capability())

print()
print("STATE:")
print(mail.state)

print()
print("[LOGIN]")

try:

    result = mail.login(
        USER,
        PASSWORD
    )

    print("LOGIN SUCCESS")
    print(result)

    print()
    print("[SELECT]")

    result = mail.select(
        "INBOX",
        readonly=True
    )

    print(result)

    mail.logout()

except Exception as e:

    print("LOGIN FAILED")
    print("TYPE:", type(e).__name__)
    print("ERROR:", repr(e))

    try:
        mail.logout()
    except:
        pass
