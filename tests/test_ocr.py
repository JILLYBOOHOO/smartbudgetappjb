import io
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import pytest
from pypdf import PdfWriter
from services import ocr

pytestmark=pytest.mark.skipif(os.name != "nt", reason="Windows OCR adapter")

def blank_pdf(pages=1):
    w=PdfWriter()
    for _ in range(pages):w.add_blank_page(300,300)
    b=io.BytesIO();w.write(b);return b.getvalue()

def test_ocr_limits_and_file_validation(tmp_path):
    for data in [b'',b'not a PDF',b'%PDF-'+b'x'*(10*1024*1024)]:
        with pytest.raises(ValueError):ocr.ocr_pdf(data,tmp_path)
    with pytest.raises(ValueError,match='20 pages'):ocr.ocr_pdf(blank_pdf(21),tmp_path)

def test_ocr_cleanup_and_no_records_written(tmp_path,monkeypatch):
    def run(*args,**kwargs):
        Path(kwargs['env']['SMARTBUDGET_OCR_OUTPUT']).write_text('2026-10-01 Groceries 2500.00',encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(ocr.subprocess,'run',run)
    assert '2500.00' in ocr.ocr_pdf(blank_pdf(),tmp_path)
    assert not list((tmp_path/'ocr-temp').iterdir())
    assert not list(tmp_path.glob('*.json'))

def test_ocr_failure_and_timeout_cleanup(tmp_path,monkeypatch):
    monkeypatch.setattr(ocr.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1))
    with pytest.raises(ValueError,match='Windows OCR'):ocr.ocr_pdf(blank_pdf(),tmp_path)
    def timeout(*a,**k):raise subprocess.TimeoutExpired('powershell',180)
    monkeypatch.setattr(ocr.subprocess,'run',timeout)
    with pytest.raises(ValueError,match='too long'):ocr.ocr_pdf(blank_pdf(),tmp_path)
    assert not list((tmp_path/'ocr-temp').iterdir())

def test_photo_pdf_conversion_and_validation():
    from PIL import Image
    image=io.BytesIO();Image.new('RGB',(80,100),'white').save(image,format='JPEG')
    pdf=ocr.photo_to_pdf(image.getvalue())
    from pypdf import PdfReader
    assert len(PdfReader(io.BytesIO(pdf)).pages)==1
    for bad in [b'',b'not an image',b'x'*(10*1024*1024+1)]:
        with pytest.raises(ValueError):ocr.photo_to_pdf(bad)
