"""Optional, local Windows OCR for image-only PDFs. No remote service is used."""
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def ocr_pdf(content, work_root):
    if os.name != 'nt' or not shutil.which('powershell.exe'):
        raise ValueError('Local scanned-PDF OCR currently requires Windows. Use a text-based PDF or CSV on this computer.')
    if not content or len(content)>10*1024*1024 or not content.startswith(b'%PDF-'):
        raise ValueError('Choose a valid PDF up to 10 MB.')
    from pypdf import PdfReader
    try:
        reader=PdfReader(io.BytesIO(content))
        if reader.is_encrypted: raise ValueError('Encrypted PDFs are not supported.')
        if len(reader.pages)>20: raise ValueError('Scanned PDFs must contain at most 20 pages. Split the statement into smaller files.')
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('The PDF could not be opened for OCR.') from exc
    root=Path(work_root)/'ocr-temp';root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as temporary:
        folder=Path(temporary).resolve();source=folder/'input.pdf';target=folder/'text.txt'
        source.write_bytes(content)
        try:
            script=Path(__file__).with_name('windows_ocr.ps1').read_text().split('\n',1)[1]
            command='$InputPath=$env:SMARTBUDGET_OCR_INPUT; $OutputPath=$env:SMARTBUDGET_OCR_OUTPUT; '+script
            environment={**os.environ,'SMARTBUDGET_OCR_INPUT':str(source),'SMARTBUDGET_OCR_OUTPUT':str(target)}
            result=subprocess.run([shutil.which('powershell.exe'),'-NoProfile','-NonInteractive','-Command',command],env=environment,capture_output=True,timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except subprocess.TimeoutExpired as exc:
            raise ValueError('OCR took too long. Split the PDF into fewer pages and try again.') from exc
        if result.returncode or not target.exists():
            raise ValueError('Windows OCR could not read this file. Check that the English OCR language feature is installed, or try a clearer scan or a text-based PDF/CSV.')
        text=target.read_text(encoding='utf-8').strip()
        if not text: raise ValueError('OCR found no readable text. Try a clearer scan or a text-based PDF/CSV.')
        if len(text)>1_000_000: raise ValueError('OCR text exceeds the one-million-character limit.')
        return text

def photo_to_pdf(content):
    """Wrap a captured receipt image as PDF for the local OCR pipeline."""
    if not content or len(content)>10*1024*1024:
        raise ValueError('Choose a receipt photo up to 10 MB.')
    from PIL import Image, ImageOps, UnidentifiedImageError
    try:
        with Image.open(io.BytesIO(content)) as source:
            if source.format not in ('JPEG','PNG'):
                raise ValueError('Choose a JPEG or PNG receipt photo.')
            if source.width*source.height>16_000_000:
                raise ValueError('The photo is too large. Use a photo below 16 megapixels.')
            image=ImageOps.exif_transpose(source).convert('RGB')
            try:
                output=io.BytesIO();image.save(output,format='PDF',resolution=150.0)
            finally:
                image.close()
        pdf=output.getvalue()
        if len(pdf)>10*1024*1024: raise ValueError('The converted photo exceeds 10 MB. Use a smaller photo.')
        return pdf
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as exc:
        raise ValueError('This image could not be opened. Use a clear JPEG or PNG receipt photo.') from exc
