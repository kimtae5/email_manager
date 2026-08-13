import imaplib
import os
import ssl

USER = os.getenv("NATE_USER")
PASSWORD = os.getenv("NATE_PW")

print("=" * 60)
print("NATE IMAP LOW LEVEL TEST")
print("=" * 60)

print("USER:", repr(USER))
print("USER length:", len(USER))
print("PW exists:", bool(PASSWORD))
print("PW length:", len(PASSWORD))

context = ssl.create_default_context()

mail = imaplib.IMAP4_SSL(
    "imap.nate.com",
    993,
    ssl_context=context,
    timeout=30
)

print()
print("WELCOME:")
print(repr(mail.welcome))

print()
print("CAPABILITY:")
print(mail.capability())

print()
print("STATE:")
print(mail.state)

print()
print("LOGIN:")

try:
    result = mail.login(USER, PASSWORD)

    print("SUCCESS:")
    print(result)

except Exception as e:

    print("FAILED")
    print("TYPE:", type(e).__name__)
    print("ERROR:", repr(e))

finally:

    try:
        mail.logout()
    except:
        pass
