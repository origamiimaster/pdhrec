from ftplib import FTP
import json
import time
import os
import subprocess
import schedule
import smtplib
from email.message import EmailMessage
import traceback
from generate_frontend_doc import main
from backend.ftp_stuff import placeFiles

# ========== CONFIGURATION ==========
N_DAYS = 3  # interval in days
EMAIL_FROM = 'you@example.com'
EMAIL_TO = 'your-email@domain.com'
SMTP_SERVER = 'smtp.example.com'
SMTP_PORT = 587
SMTP_USER = 'you@example.com'
SMTP_PASS = 'your-email-password'
# ===================================


def run_eleventy_build(target_directory):
    command = [
        "npx", "@11ty/eleventy",
        "--formats=html,css,js,liquid,md",
        "--output=build"
    ]

    try:
        result = subprocess.run(
            command,
            cwd=target_directory,
            capture_output=True,
            text=True,
            check=True  # raises CalledProcessError on failure
        )
        print("Eleventy build succeeded:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Eleventy build failed:\n", e.stderr)
        raise  # re-raise for retry or error handling


def run_ftp_stuff():
    with open('./server-token.json') as server_token_file:
        data = json.load(server_token_file)

    ftp = FTP(data['ftp_domain'])
    ftp.login(user=data['ftp_username'], passwd=data['ftp_password'])
    ftp.cwd("/pdhrec.com/public_html")

    placeFiles(ftp, "./frontend/build", verbose=True)


def run_process():
    main()
    run_eleventy_build("./frontend")
    run_ftp_stuff()


def send_failure_email(error_msg):
    msg = EmailMessage()
    msg['Subject'] = 'Process Failed After Retry'
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg.set_content(f"The process failed after one retry.\n\nError:\n{error_msg}")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    print("Failure email sent.")


def attempt_process():
    try:
        run_process()
        print("Process completed successfully.")
    except Exception as e:
        print("First attempt failed:", e)
        try:
            run_process()
            print("Process completed successfully on retry.")
        except Exception as e2:
            print("Second attempt failed:", e2)
            send_failure_email(traceback.format_exc())


# Schedule the job every N days
# schedule.every(N_DAYS).days.do(attempt_process)

# print(f"Scheduler started. Running every {N_DAYS} days.")
# while True:
#     schedule.run_pending()
#     time.sleep(60)

attempt_process()