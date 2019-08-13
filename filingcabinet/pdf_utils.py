import contextlib
import glob
import io
import logging
import os
import shutil
import subprocess
import tempfile

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

import wand
from wand.image import Image
from wand.color import Color

from PyPDF2 import PdfFileReader
from PIL import Image as PILImage

try:
    import tesserocr
except ImportError:
    tesserocr = None
try:
    import pdflib
except ImportError:
    pdflib = None


OFFICE_FILETYPES = (
    'application/msexcel',
    'application/vnd.ms-excel',
    'application/msword',
    'application/vnd.msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
)
OFFICE_EXTENSIONS = (
    '.doc',
    '.docx',
    '.odt'
)


TESSERACT_LANGUAGE = {
    'en': 'eng',
    'de': 'deu'
}


class PDFProcessor(object):
    def __init__(self, filename, language=None, config=None):
        self.filename = filename
        self.pdf_reader = PdfFileReader(filename)
        self.num_pages = self.pdf_reader.getNumPages()
        self.language = language
        self.config = config or {}

    def get_meta(self):
        doc_info = self.pdf_reader.getDocumentInfo()
        return {
            'title': doc_info.title
        }

    def get_images(self, pages=None, resolution=300):
        if pages is None:
            pages = range(self.num_pages)
        for page_no in pages:
            with self.get_image(page_no, resolution=resolution) as img:
                yield img

    def get_all_images(self, resolution=300):
        white = wand.color.Color('#fff')
        with get_images_from_pdf(self.filename, dpi=resolution) as images:
            for i, image_filename in enumerate(images):
                with Image(filename=image_filename, background=white) as img:
                    yield i + 1, img

    def get_text_for_page(self, page_no, image=None):
        text = self._get_text_for_page(page_no)
        if not text.strip() and image is not None:
            text = self.run_ocr_on_image(image)
        return text.strip()

    def _get_text_for_page(self, page_no):
        if not hasattr(self, 'pdflib_pages'):
            if pdflib is not None:
                pdflib_doc = pdflib.Document(self.filename)
                self.pdflib_pages = list(pdflib_doc)
        if hasattr(self, 'pdflib_pages'):
            page = self.pdflib_pages[page_no]
            return ' '.join(page.lines).strip()
        page = self.pdf_reader.getPage(page_no - 1)
        return page.extractText()

    def get_text(self, pages=None):
        if pages is None:
            pages = range(self.num_pages)
        for page_no in pages:
            yield self.get_for_page(page_no)

    def run_ocr_on_image(self, image):
        if tesserocr is None:
            return ''
        img_blob = image.make_blob('RGB')
        pil_image = PILImage.frombytes('RGB', image.size, img_blob)
        return tesserocr.image_to_text(
            pil_image,
            lang=TESSERACT_LANGUAGE[self.language],
            path=self.config.get('TESSERACT_DATA_PATH', '')
        )


def crop_image(image_path, left, top, width, height):
    with Image(filename=image_path) as img:
        img.alpha_channel = False
        img.crop(left, top, left + width, top + height)
        return img.make_blob('gif')


def can_convert_to_pdf(filetype, name=None):
    return filetype.lower() in OFFICE_FILETYPES or (
        name is not None and name.lower().endswith(OFFICE_EXTENSIONS))


def convert_to_pdf(filepath, binary_name=None, construct_call=None,
                   timeout=120):
    if binary_name is None and construct_call is None:
        return
    outpath = tempfile.mkdtemp()
    path, filename = os.path.split(filepath)
    parts = filename.rsplit('.', 1)
    name = parts[0]
    output_file = os.path.join(outpath, '%s.pdf' % name)
    arguments = [
        binary_name,
        '--headless',
        '--nodefault',
        '--nofirststartwizard',
        '--nolockcheck',
        '--nologo',
        '--norestore',
        '--invisible',
        '--convert-to',
        'pdf',
        '--outdir',
        outpath,
        filepath
    ]
    if construct_call is not None:
        arguments, output_file = construct_call(filepath, outpath)

    try:
        output_bytes = shell_call(
            arguments, outpath, output_file,
            timeout=timeout
        )
        return output_bytes
    except Exception as err:
        logging.error("Error during Doc to PDF conversion: %s", err)
    finally:
        shutil.rmtree(outpath)
    return None


def convert_images_to_ocred_pdf(filenames, language='en', instructions=None):
    try:
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, 'out.pdf')
        pdf_bytes = convert_images_to_pdf(filenames, instructions=instructions)

        with open(output_file, 'wb') as f:
            f.write(pdf_bytes)

        return run_ocr(output_file, language=language, timeout=180)

    except Exception as err:
        logging.error("Error during convert images to ocred pdf: %s", err)
        return None
    finally:
        # Delete all temporary files
        shutil.rmtree(temp_dir)


def run_ocr(filename, language=None, binary_name='ocrmypdf', timeout=50):
    if binary_name is None:
        return
    outpath = tempfile.mkdtemp()
    lang = TESSERACT_LANGUAGE[language]
    output_file = os.path.join(outpath, 'out.pdf')
    arguments = [
        binary_name,
        '-l',
        lang,
        '--deskew',
        '--skip-text',
        # '--title', title
        filename,
        output_file
    ]
    try:
        output_bytes = shell_call(
            arguments, outpath, output_file,
            timeout=timeout
        )
        return output_bytes
    except Exception as err:
        logging.error("Error during PDF OCR: %s", err)
    finally:
        shutil.rmtree(outpath)
    return None


def shell_call(arguments, outpath, output_file=None, timeout=50):
    env = dict(os.environ)
    env.update({'HOME': outpath})

    logging.info("Running: %s", arguments)
    out, err = '', ''
    p = None
    try:
        p = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )

        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if p is not None:
            p.kill()
            out, err = p.communicate()
    finally:
        if p is not None and p.returncode is None:
            p.kill()
            out, err = p.communicate()
    if p is not None and p.returncode == 0:
        if output_file is not None and os.path.exists(output_file):
            with open(output_file, 'rb') as f:
                return f.read()
    if output_file is not None:
        raise Exception(err)


def run_command_overwrite(filename, argument_func, timeout=50):
    try:
        temp_dir = tempfile.mkdtemp()
        temp_out = os.path.join(temp_dir, 'gs_pdf_out.pdf')
        arguments, temp_out = argument_func(filename, temp_dir)
        output_bytes = shell_call(
            arguments, temp_dir, temp_out, timeout=timeout
        )

        with open(filename, 'wb') as f:
            f.write(output_bytes)
        return filename
    except Exception as err:
        logging.error("Error during command overwrite %s", err)
        return None
    finally:
        # Delete all temporary files
        shutil.rmtree(temp_dir)


def decrypt_pdf_in_place(filename, password=None, timeout=50):
    def argument_func(filename, temp_dir):
        temp_out = os.path.join(temp_dir, 'qpdf_out.pdf')
        arguments = ['qpdf', '--decrypt']

        if password is not None:
            arguments.extend([
                '--password=%s' % password
            ])

        arguments.extend([filename, temp_out])
        return arguments, temp_out

    return run_command_overwrite(filename, argument_func, timeout=timeout)


def rewrite_pdf_in_place(filename, password=None, timeout=50):
    def argument_func(filename, temp_dir):
        temp_out = os.path.join(temp_dir, 'gs_pdf_out.pdf')
        arguments = [
            'gs', '-o', temp_out,
        ]
        if password is not None:
            arguments.extend([
                '-sPDFPassword=%s' % password
            ])
        arguments.extend([
            '-sDEVICE=pdfwrite',
            '-dPDFSETTINGS=/prepress',
            filename
        ])
        return arguments, temp_out

    return run_command_overwrite(filename, argument_func, timeout=timeout)


def rewrite_hard_pdf_in_place(filename, password=None, timeout=50):
    def argument_func(filename, temp_dir):
        temp_out = os.path.join(temp_dir, 'pdfcairo_out.pdf')
        arguments = [
            'pdftocairo',
            '-pdf',
        ]
        if password is not None:
            arguments.extend([
                '-upw', password
            ])
        arguments.extend([
            filename,
            temp_out
        ])
        return arguments, temp_out

    return run_command_overwrite(filename, argument_func, timeout=timeout)


MAX_HEIGHT_A4 = 3507  # in pixels at 300 dpi


def convert_images_to_pdf(filenames, instructions=None, dpi=300):
    if instructions is None:
        instructions = [{} for _ in range(len(filenames))]
    a4_width, a4_height = A4
    writer = io.BytesIO()
    pdf = canvas.Canvas(writer, pagesize=A4)
    for filename, instruction in zip(filenames, instructions):
        with Image(filename=filename, resolution=dpi) as image:
            image.background_color = Color('white')
            image.format = 'jpg'
            image.alpha_channel = 'remove'
            try:
                degree = instruction.get('rotate', 0)
                if degree and degree % 90 == 0:
                    image.rotate(degree)
            except ValueError:
                pass

            if image.width > image.height:
                ratio = MAX_HEIGHT_A4 / image.width
            else:
                ratio = MAX_HEIGHT_A4 / image.height
            if ratio < 1:
                image.resize(
                    round(ratio * image.width),
                    round(ratio * image.height)
                )

            width = image.width * 72 / dpi
            height = image.height * 72 / dpi
            pdf.setPageSize((width, height))
            reportlab_io_img = ImageReader(io.BytesIO(image.make_blob()))
            pdf.drawImage(reportlab_io_img, 0, 0, width=width, height=height)
            pdf.showPage()
    pdf.save()
    return writer.getvalue()


@contextlib.contextmanager
def get_images_from_pdf(filename, pages=None, dpi=300, timeout=5 * 60):
    try:
        temp_dir = tempfile.mkdtemp()
        yield run_pdfto_ppm_on_pages(filename, temp_dir, pages, dpi, timeout)
    except Exception as err:
        logging.error("Error during command overwrite %s", err)
    finally:
        # Delete all temporary files
        shutil.rmtree(temp_dir)


def run_pdfto_ppm_on_pages(filename, temp_dir, pages, dpi, timeout):
    temp_out = os.path.join(temp_dir, 'image')

    base_arguments = [
        'pdftoppm', '-png', '-r', str(dpi),
        '-forcenum',
    ]

    if pages is not None:
        pages = list(pages)
        pages.sort()
        page_iterator = get_continuous_pages(pages)
    else:
        page_iterator = ((None, None) for _ in (None,))

    for first, last in page_iterator:
        arguments = list(base_arguments)
        if first is not None:
            arguments.extend(['-f', str(first), '-l', str(last)])

        arguments.extend([filename, temp_out])
        shell_call(
            arguments, temp_dir, output_file=None, timeout=timeout
        )

    images = glob.glob(temp_out + '-*.png')
    images.sort()
    return images


def get_continuous_pages(pages):
    first, last = None, None

    for page in pages:
        if first is None:
            first = page
            last = page
            continue
        if page - last > 1:
            yield (first, last)
            first = page
            last = page
            continue
        last = page
    yield (first, last)
