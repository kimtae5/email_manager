import imaplib
import os

PASSWORD = os.getenv("NATE_PW")

users = [
    "kimtae5",
    "kimtae5@nate.com",
]

for user in users:

    print("=" * 70)
    print("USER TEST:", user)
    print("=" * 70)

    try:
        mail = imaplib.IMAP4_SSL(
            "imap.nate.com",
            993,
            timeout=30
        )

        print("WELCOME:", mail.welcome)
        print("CAPABILITY:", mail.capability())

        result = mail.login(
            user,
            PASSWORD
        )

        print("✅ LOGIN SUCCESS")
        print(result)

        mail.logout()

    except Exception as e:

        print("❌ LOGIN FAILED")
        print("TYPE:", type(e).__name__)
        print("ERROR:", repr(e))
