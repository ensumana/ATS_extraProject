import os
import re
import win32com.client


RF_KEYWORDS = [
    "rf testing",
    "rf design",
    "rf architect",
    "engineer",
    "resume"
]

MANDATORY_WORD = "application"


def clean(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).lower())


def get_sender_name(mail):
    try:
        if mail.SenderEmailType == "EX":
            user = mail.Sender.GetExchangeUser()
            if user:
                return user.Name
    except:
        pass

    return mail.SenderEmailAddress.split("@")[0]


def is_matching(subject, body):
    text = clean(subject + " " + body)

    if MANDATORY_WORD not in text:
        return False

    return any(k in text for k in RF_KEYWORDS)


def download_resumes(folder_path, from_date, to_date, progress_callback):

    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    inbox = outlook.GetDefaultFolder(6)  # 6 = Inbox
    messages = inbox.Items

    # IMPORTANT: sort by received time
    messages.Sort("[ReceivedTime]", True)

    processed = 0
    downloaded = 0

    total = messages.Count

    if total == 0:
        return 0, 0

    for i, msg in enumerate(messages):

        try:
            processed += 1

            # progress update
            if processed % 10 == 0:
                progress_callback(int((processed / total) * 100))

            # ----------------------------
            # DATE FILTER (CRITICAL FIX)
            # ----------------------------
            received = msg.ReceivedTime

            # normalize to naive datetime
            received = received.replace(tzinfo=None)

            if not (from_date <= received <= to_date):
                continue

            # ----------------------------
            # ATTACHMENT CHECK
            # ----------------------------
            attachments = msg.Attachments
            if attachments.Count == 0:
                continue

            for j in range(1, attachments.Count + 1):
                attachment = attachments.Item(j)

                filename = attachment.FileName.lower()

                if filename.endswith((".pdf", ".doc", ".docx")):
                    # sanitize sender name (VERY important for Windows file system)
                    sender = msg.SenderName if msg.SenderName else "Unknown_Sender"
                    sender = re.sub(r'[\\/*?:"<>|]', "_", sender)  # remove invalid filename chars

                    # file extension preservation
                    ext = os.path.splitext(attachment.FileName)[1]

                    # optional: avoid overwriting if multiple emails from same sender
                    timestamp = msg.ReceivedTime.strftime("%Y%m%d_%H%M%S")

                    filename = f"{sender}_{timestamp}{ext}"

                    save_path = os.path.join(folder_path, filename)

                    attachment.SaveAsFile(save_path)
                    downloaded += 1

        except Exception:
            continue

    progress_callback(100)

    return processed, downloaded

from datetime import timezone

def make_naive(dt):
    """Convert Outlook timezone-aware datetime → naive"""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

