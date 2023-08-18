"""
This script uses python's ftplib module to upload the static site from
frontent/build/* into the hosting service.
"""
import os
import json
from ftplib import error_perm, FTP


def placeFiles(ftp, path, verbose=False):
    for name in os.listdir(path):
        localpath = os.path.join(path, name)
        if os.path.isfile(localpath):
            print("STOR", name, localpath) if verbose else None
            ftp.storbinary('STOR ' + name, open(localpath, 'rb'))
        elif os.path.isdir(localpath):
            print("MKD", name) if verbose else None
            try:
                ftp.mkd(name)
            except error_perm as e:
                if not e.args[0].startswith('550'):
                    raise

            print("CWD", name) if verbose else None
            ftp.cwd(name)
            placeFiles(ftp, localpath)
            print("CWD", "..") if verbose else None
            ftp.cwd("..")


if __name__ == "__main__":
    with open('../server-token.json') as server_token_file:
        data = json.load(server_token_file)

    ftp = FTP(data['ftp_domain'])
    ftp.login(user=data['ftp_username'], passwd=data['ftp_password'])
    ftp.cwd("/pdhrec.com/public_html")

    placeFiles(ftp, "../frontend/build", verbose=True)
