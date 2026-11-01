#!/usr/bin/env python3
"""Explicit-TLS FTP deployment of the approved kr artifact; default is read-only."""
import argparse
import ftplib
import hashlib
import os
from pathlib import Path
import ssl
import sys
from datetime import datetime, timezone
from build_site import ROOT, require

HOST='145.79.26.89'
USER='u250225041'
SITE='knowledgewalk.kr'
CANDIDATE_DIRS=['/domains/knowledgewalk.kr/public_html','/home/u250225041/domains/knowledgewalk.kr/public_html']


def artifact_files(folder):
    require(folder.is_dir(),'kr build is missing')
    files=sorted(p for p in folder.rglob('*') if p.is_file())
    require((folder/'knowledgewalk-deployment.json').is_file(),'kr site marker is missing')
    import json
    marker=json.loads((folder/'knowledgewalk-deployment.json').read_text())
    require(marker['site']==SITE and marker['stories']>0,'Wrong deployment artifact')
    for p in files:
        require(not p.is_symlink(),'Symlinks cannot be deployed')
        name=p.relative_to(folder).as_posix()
        require(not any(x in name.split('/') for x in ['..','wp-config.php','wp-content','art','content','docs']), 'Non-site file in artifact')
    return files


def enter_site(ftp):
    for path in CANDIDATE_DIRS:
        try:ftp.cwd(path)
        except ftplib.error_perm:continue
        require('/knowledgewalk.kr/public_html' in ftp.pwd().rstrip('/'),'Server did not confirm the kr directory')
        return
    raise ValueError('Cannot confirm knowledgewalk.kr/public_html; no files were changed')


def mkdirs(ftp,name):
    current=''
    for part in Path(name).parts:
        current+='/'+part
        try:ftp.mkd('.'+current)
        except ftplib.error_perm as e:
            # Verify existing directories instead of treating all errors as success.
            here=ftp.pwd()
            try:ftp.cwd('.'+current)
            except ftplib.error_perm:raise e
            finally:ftp.cwd(here)


def put(ftp,path,name):
    with path.open('rb') as stream:ftp.storbinary('STOR '+name,stream)
    ftp.voidcmd('TYPE I')
    require(ftp.size(name)==path.stat().st_size,'Uploaded size mismatch: '+name)


def deploy(ftp,folder,write=False):
    files=artifact_files(folder)
    enter_site(ftp)
    names=set(ftp.nlst())
    require(any(Path(n).name in ['wp-config.php','knowledgewalk-deployment.json'] for n in names),'Unexpected destination; no files were changed')
    print('Confirmed destination: knowledgewalk.kr/public_html')
    print('Approved deployment files:',len(files))
    if not write:
        print('Read-only connection check complete. No files changed.')
        return
    # Assets first, entry files last. Never delete WordPress, art or unrelated files.
    entry={'index.html','.htaccess'}
    for path in files:
        rel=path.relative_to(folder).as_posix()
        if rel in entry:continue
        if '/' in rel:mkdirs(ftp,str(Path(rel).parent))
        put(ftp,path,rel)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for name in ['.htaccess','index.html']:
        current=set(Path(n).name for n in ftp.nlst())
        if name in current:ftp.rename(name,'.knowledgewalk-backup-'+stamp+'-'+name.lstrip('.'))
        incoming='.knowledgewalk-incoming-'+name.lstrip('.')
        put(ftp,folder/name,incoming);ftp.rename(incoming,name)
    marker=bytearray()
    ftp.retrbinary('RETR knowledgewalk-deployment.json',marker.extend)
    require(hashlib.sha256(marker).digest()==hashlib.sha256((folder/'knowledgewalk-deployment.json').read_bytes()).digest(),'Remote marker mismatch')
    print('kr files uploaded. Public HTTPS verification is still required.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publish',action='store_true');args=parser.parse_args()
    password=os.environ.get('HOSTINGER_FTP_PASSWORD')
    if not password:
        print('Required GitHub secret HOSTINGER_FTP_PASSWORD is not configured.', file=sys.stderr)
        raise SystemExit(2)
    # Certificate/hostname verification stays enabled; no plaintext FTP fallback.
    host=os.environ.get('HOSTINGER_FTPS_HOST',HOST)
    ftp=ftplib.FTP_TLS(context=ssl.create_default_context(),timeout=40)
    try:
        ftp.connect(host,21);ftp.auth();ftp.login(USER,password);ftp.prot_p()
        deploy(ftp,ROOT/'_kr-site',args.publish)
    finally:
        try:ftp.close()
        except Exception:pass


if __name__=='__main__':
    try:main()
    except ssl.SSLCertVerificationError:
        print('TLS server identity could not be verified. No authenticated upload was attempted; a verified Hostinger FTP hostname is required.',file=sys.stderr);sys.exit(1)
    except (ValueError,ftplib.Error,OSError):
        # Do not print server replies that might contain authentication details.
        print('Hostinger connection/deployment stopped. Check the encrypted password, verified TLS hostname and kr directory. No plaintext fallback was used.',file=sys.stderr);sys.exit(1)
