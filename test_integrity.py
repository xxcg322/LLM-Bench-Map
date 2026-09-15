"""Small tests for line endings, corruption detection and safe manifest paths."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from integrity import digest, verify_release


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='integrity-test-')
        self.root = Path(self.tmp.name)
        self.data = self.root/'example.csv'
        self.data.write_bytes(b'id,n\na,2\n')
        self.manifest = {'hash_policy':'utf8_crlf_to_lf_otherwise_raw',
                         'files':{'example.csv':digest(self.data)}}
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        (self.root/'RELEASE_MANIFEST.json').write_text(json.dumps(self.manifest),encoding='utf-8')

    def test_lf_and_crlf(self):
        self.data.write_bytes(b'id,n\r\na,2\r\n')
        verify_release(self.root)

    def test_meaningful_change_rejected(self):
        self.data.write_bytes(b'id,n\na,3\n')
        with self.assertRaises(ValueError):
            verify_release(self.root)

    def test_missing_file_rejected(self):
        self.data.unlink()
        with self.assertRaises(ValueError):
            verify_release(self.root)

    def test_binary_is_exact(self):
        path = self.root/'archive.gz'
        path.write_bytes(b'not-a-real-archive\r\n')
        self.assertEqual(digest(path),hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertNotEqual(digest(path),hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest())

    def test_outside_path_rejected(self):
        self.manifest['files']={'../outside.csv':'0'*64}
        self.save()
        with self.assertRaises(ValueError):
            verify_release(self.root)


if __name__=='__main__':
    unittest.main()
