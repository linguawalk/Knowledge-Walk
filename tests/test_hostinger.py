"""No remote mutation before artifact and domain directory checks pass."""
import json
import pathlib
import sys
import tempfile
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import deploy_hostinger as deploy

class ReadOnlyFTP:
    def __init__(self,wrong=False):self.wrong=wrong;self.writes=[]
    def cwd(self,path):self.path=path
    def pwd(self):return '/domains/another-site.example/public_html' if self.wrong else '/domains/knowledgewalk.kr/public_html'
    def nlst(self):return ['wp-config.php','wp-content','art']
    def storbinary(self,*args):self.writes.append(args)

class HostingerTests(unittest.TestCase):
    def artifact(self,folder):
        (folder/'knowledgewalk-deployment.json').write_text(json.dumps({'site':'knowledgewalk.kr','stories':117}))
        (folder/'index.html').write_text('ready')
    def test_default_connection_check_does_not_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp);self.artifact(p);ftp=ReadOnlyFTP();deploy.deploy(ftp,p);self.assertEqual(ftp.writes,[])
    def test_wrong_domain_stops_before_upload_even_when_publish_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp);self.artifact(p);ftp=ReadOnlyFTP(wrong=True)
            with self.assertRaises(ValueError):deploy.deploy(ftp,p,write=True)
            self.assertEqual(ftp.writes,[])
    def test_wordpress_configuration_is_not_an_upload_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp);self.artifact(p);(p/'wp-config.php').write_text('not a deployment asset')
            with self.assertRaises(ValueError):deploy.artifact_files(p)

if __name__=='__main__':unittest.main()
