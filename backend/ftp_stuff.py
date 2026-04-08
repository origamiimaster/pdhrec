"""
This script uses python's ftplib module to upload the static site from
frontent/build/* into the hosting service.
"""
import os
import json
from ftplib import error_perm, FTP, all_errors
import time
import socket


def placeFiles(ftp, path, verbose=False, max_retries=3):
    for name in os.listdir(path):
        localpath = os.path.join(path, name)
        if os.path.isfile(localpath):
            print("STOR", name, localpath) if verbose else None

            # Retry logic for failed uploads
            for attempt in range(max_retries):
                try:
                    with open(localpath, 'rb') as f:
                        ftp.storbinary('STOR ' + name, f, blocksize=8192)
                    break  # Success, move to next file
                except (all_errors, socket.timeout, OSError) as e:
                    if attempt < max_retries - 1:
                        print(f"Retry {attempt + 1}/{max_retries} for {name}: {e}") if verbose else None
                        time.sleep(2)  # Brief pause before retry
                    else:
                        print(f"Failed to upload {name} after {max_retries} attempts: {e}")
                        raise

        elif os.path.isdir(localpath):
            print("MKD", name) if verbose else None
            try:
                ftp.mkd(name)
            except error_perm as e:
                if not e.args[0].startswith('550'):
                    raise

            print("CWD", name) if verbose else None
            ftp.cwd(name)
            placeFiles(ftp, localpath, verbose=verbose, max_retries=max_retries)
            print("CWD", "..") if verbose else None
            ftp.cwd("..")


if __name__ == "__main__":
    with open('../server-token.json') as server_token_file:
        data = json.load(server_token_file)

    ftp = FTP(data['ftp_domain'], timeout=60)  # Set timeout to 60 seconds
    ftp.login(user=data['ftp_username'], passwd=data['ftp_password'])
    ftp.set_pasv(True)
    ftp.cwd("/pdhrec.com/public_html")

    try:
        placeFiles(ftp, "../frontend/build", verbose=True, max_retries=3)
    finally:
        ftp.quit()
