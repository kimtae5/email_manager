import os
import imaplib
import ssl

USER = os.getenv("NATE_USER")
PASSWORD = os.getenv("NATE_PW")

print("USER:", USER)
print("PASSWORD:", "SET" if PASSWORD else "NOT SET")

context = ssl.create_default_context()

mail = imaplib.IMAP4_SSL(
    "imap.nate.com",
    993,
    ssl_context=context,
    timeout=30
)

print("CONNECTED")
print("WELCOME:", mail.welcome)

try:
    result = mail.login(USER, PASSWORD)
    print("LOGIN:", result)

    result = mail.select("INBOX", readonly=True)
    print("INBOX:", result)

except Exception as e:
    print("ERROR:", type(e).__name__, repr(e))

finally:
    try:
        mail.logout()
    except:
        pass
