"""Synthetic round-trip, refusal and no-overwrite checks; no external files."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from stars import encode,decode

class CodecTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.p=Path(self.temp.name)/'picture.png'
    def test_hello_roundtrip(self):
        encode('HELLO HERMES',self.p)
        self.assertEqual(decode(self.p),'HELLO HERMES')
    def test_alphabet_and_word_gap(self):
        text='ABCDEFGHIJKLMNOPQRSTUVWXYZ A Z'
        encode(text,self.p)
        self.assertEqual(decode(self.p),text)
    def test_single_letter(self):
        encode('A',self.p)
        self.assertEqual(decode(self.p),'A')
    def test_capacity_boundary(self):
        encode('Z'*40,self.p)
        self.assertEqual(decode(self.p),'Z'*40)
    def test_unsupported_input_refused(self):
        for text in ['', 'Привет', 'hello', 'A  B', ' A', 'A ', 'A1', 'A'*41]:
            with self.subTest(length=len(text)):
                with self.assertRaises(ValueError):encode(text,self.p)
                self.assertFalse(self.p.exists())
    def test_no_overwrite(self):
        encode('A',self.p)
        before=self.p.read_bytes()
        with self.assertRaises(FileExistsError):encode('B',self.p)
        self.assertEqual(self.p.read_bytes(),before)
    def test_resized_image_refused(self):
        encode('HELLO',self.p)
        with Image.open(self.p) as im:
            changed=Path(self.temp.name)/'resized.png'
            im.resize((600,400)).save(changed)
        with self.assertRaises(ValueError):decode(changed)
    def test_off_grid_star_refused(self):
        encode('HELLO',self.p)
        with Image.open(self.p) as orig:im=orig.convert('RGB')
        im.putpixel((100,320),(255,244,196));im.putpixel((100,321),(255,255,255))
        changed=Path(self.temp.name)/'changed.png';im.save(changed)
        with self.assertRaises(ValueError):decode(changed)
    def test_blank_image_refused(self):
        Image.new('RGB',(1200,800)).save(self.p)
        with self.assertRaises(ValueError):decode(self.p)

if __name__=='__main__':unittest.main()
