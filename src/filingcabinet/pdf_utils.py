import contextlib
import glob
import hashlib
import io
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO, Callable, Generator, NamedTuple, Optional

import pikepdf
import wand
from PIL import Image as PILImage
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from wand.color import Color
from wand.image import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

from .settings import FILINGCABINET_PAGE_PROCESSING_TIMEOUT

logger = logging.getLogger(__name__)


OFFICE_FILETYPES = (
    "application/msexcel",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
    "application/vnd.msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/rtf",
    "application/rtf",
)
OFFICE_EXTENSIONS = (
    ".doc",
    ".docx",
    ".docm",
    ".odt",
    ".rtf",
)


TESSERACT_LANGUAGE = {"en": "eng", "de": "deu"}


class ShellRecipe(NamedTuple):
    arguments: list[str]
    output_file: Path


ShellRecipeMaker = Callable[[Path, Path], ShellRecipe]


class PDFException(Exception):
    def __init__(self, exc, reason):
        self.exc = exc
        self.reason = reason


def try_reading_pdf(pdf_file: Path, password=None) -> PdfReader:
    try:
        pdf_reader = PdfReader(pdf_file, strict=False)
    except (PdfReadError, ValueError, OSError) as e:
        raise PDFException(e, "rewrite") from None

    if pdf_reader.is_encrypted:
        raise PDFException(None, "decrypt") from None

    try:
        # Try reading number of pages
        len(pdf_reader.pages)
    except KeyError as e:  # catch KeyError '/Pages'
        raise PDFException(e, "rewrite") from None
    except ValueError as e:  # catch invalid literal for int() with base 10
        raise PDFException(e, "rewrite") from None
    except RecursionError as e:  # catch RecursionError in pypdf
        raise PDFException(e, "rewrite") from None
    except PdfReadError as e:
        raise PDFException(e, "decrypt") from None
    return pdf_reader


def get_readable_pdf(pdf_file: Path, copy_func, password=None):
    tries = 0
    timeout = FILINGCABINET_PAGE_PROCESSING_TIMEOUT
    while True:
        try:
            pdf_reader = try_reading_pdf(pdf_file, password=password)
            return pdf_file, pdf_reader
        except PDFException as e:
            if tries == 0 and copy_func:
                pdf_file = copy_func(pdf_file)
            tries += 1
            if tries > 2:
                raise Exception("PDF Redaction Error") from None
            if e.reason == "rewrite":
                next_pdf_file = rewrite_pdf_in_place(
                    pdf_file, password=password, timeout=timeout
                )
                if next_pdf_file is None:
                    next_pdf_file = rewrite_hard_pdf_in_place(
                        pdf_file, password=password, timeout=timeout
                    )
            elif e.reason == "decrypt":
                next_pdf_file = decrypt_pdf_in_place(
                    pdf_file, password=password, timeout=timeout
                )
            if next_pdf_file is None:
                raise Exception("PDF Rewrite Error") from None
            pdf_file = next_pdf_file


class PikePDFProcessor:
    filename: Path

    def __init__(self, filename: Path):
        self._pdf = None
        self.filename = filename

    def open(self):
        if self._pdf is None:
            self._pdf = pikepdf.Pdf.open(self.filename)

    def close(self):
        if self._pdf is not None:
            self._pdf.close()
            self._pdf = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def get_page_number_for_page(self, page):
        try:
            return self._pdf.pages.index(page) + 1
        except ValueError:
            return None

    def get_outline(self, outlines=None, depth=0):
        if outlines is None:
            outline = self._pdf.open_outline()
            outlines = outline.root
        for item in outlines:
            page_number = None
            try:
                if not item or not item.destination:
                    continue
                page_number = self.get_page_number_for_page(item.destination[0])
            except (TypeError, AttributeError, IndexError):
                try:
                    page_number = self.get_page_number_for_page(item.destination)
                except (TypeError, AttributeError, IndexError):
                    pass
            if page_number is None:
                continue
            title = fix_text(item.title)
            yield depth, title, page_number
            yield from self.get_outline(item.children, depth=depth + 1)

    def iter_markdown_outline(self):
        outline_generator = self.get_outline()
        for depth, title, page_number in outline_generator:
            yield "{indent}- [{title}](#page-{page_number})\n".format(
                indent="  " * depth, title=title, page_number=page_number
            )

    def get_markdown_outline(self):
        return "".join(self.iter_markdown_outline())


def fix_text(text: Optional[str | bytes]) -> Optional[str]:
    if text is None:
        return None
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    return text.replace("\u0000", "")


class PDFProcessor(object):
    def __init__(
        self, filename: str | Path, copy_func=None, language=None, config=None
    ):
        filename, pdf_reader = get_readable_pdf(filename, copy_func)
        self.filename = Path(filename)
        self.pdf_reader = pdf_reader
        self.num_pages = len(self.pdf_reader.pages)
        self.language = language
        self.config = config or {}

    def get_meta(self):
        try:
            doc_info = self.pdf_reader.metadata
        except PdfReadError:
            logger.warning(
                "Could not read metadata for pdf %s:", self.filename, exc_info=True
            )
            doc_info = None
        if doc_info is None:
            return {}
        return {
            "title": fix_text(doc_info.title),
            "author": fix_text(doc_info.author),
            "creator": fix_text(doc_info.creator),
            "producer": fix_text(doc_info.producer),
            "subject": fix_text(doc_info.subject),
        }

    def get_markdown_outline(self):
        with PikePDFProcessor(self.filename) as pike_pdf:
            return pike_pdf.get_markdown_outline()

    def get_images(self, pages=None, resolution=300, timeout=5 * 60):
        white = wand.color.Color("#fff")
        if pages is None:
            pages = list(range(1, self.num_pages + 1))
        images = get_images_from_pdf(
            self.pdf_reader,
            self.filename,
            pages,
            max_dpi=resolution,
            timeout=timeout,
        )
        for page_number, image_filename in images:
            logger.info("Generated page %s: %s", page_number, image_filename)
            with Image(filename=image_filename, background=white) as img:
                yield page_number, img

    def get_text_for_page(self, page_no, image=None, use_ocr=False):
        text = self._get_text_for_page(page_no)
        if not text.strip():
            if use_ocr and image is None:
                for _page_number, image in self.get_images([page_no]):
                    text = self.run_ocr_on_image(image)
            elif image is not None:
                text = self.run_ocr_on_image(image)
        return text.strip()

    def _get_text_for_page(self, page_no):
        page = self.pdf_reader.pages[page_no - 1]
        return page.extract_text()

    def get_text(self, pages=None, use_ocr=False):
        if pages is None:
            pages = range(self.num_pages)
        for page_no in pages:
            yield self.get_text_for_page(page_no, use_ocr=use_ocr)

    def run_ocr_on_image(self, image, timeout=30):
        if pytesseract is None:
            return ""
        img_blob = image.make_blob("RGB")
        pil_image = PILImage.frombytes("RGB", image.size, img_blob)

        lang = TESSERACT_LANGUAGE.get(self.language)
        config = ""
        path = self.config.get("TESSERACT_DATA_PATH", "")
        if path:
            config = '--tessdata-dir "{}"'.format(path)

        try:
            return pytesseract.image_to_string(
                pil_image, lang=lang, config=config, timeout=timeout
            )
        except RuntimeError as e:
            logger.warning(e)
            return ""


def draw_highlights(highlights):
    def apply_highlights(img):
        img.colorspace = "rgb"
        for highlight in highlights:
            crop = img[
                highlight["left"] : highlight["left"] + highlight["width"],
                highlight["top"] : highlight["top"] + highlight["height"],
            ]
            crop.opaque_paint(
                target=Color("white"),
                fill=Color(highlight["color"]),
                fuzz=crop.quantum_range * 0.3,
            )
            img.composite(crop, left=highlight["left"], top=highlight["top"])

    return apply_highlights


def crop_image(image_path, left, top, width, height, transform_func=None):
    with Image(filename=image_path) as img:
        img.alpha_channel = False
        img.crop(left, top, left + width, top + height)
        if transform_func is not None:
            transform_func(img)
        return img.make_blob("gif")


def can_convert_to_pdf(filetype, name=None):
    return filetype.lower() in OFFICE_FILETYPES or (
        name is not None and name.lower().endswith(OFFICE_EXTENSIONS)
    )


def convert_to_pdf(
    filepath: Path | str, binary_name=None, construct_call=None, timeout=120
):
    if binary_name is None and construct_call is None:
        return
    filepath = Path(filepath)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        filename = filepath.name
        parts = filename.rsplit(".", 1)
        name = parts[0]
        output_file = temp_dir / f"{name}.pdf"
        arguments = [
            binary_name,
            "--headless",
            "--nodefault",
            "--nofirststartwizard",
            "--nolockcheck",
            "--nologo",
            "--norestore",
            "--invisible",
            "--convert-to",
            "pdf",
            "--outdir",
            str(temp_dir),
            str(filepath),
        ]
        if construct_call is not None:
            arguments, output_file = construct_call(str(filepath), str(temp_dir))

        try:
            output_bytes = shell_call(
                arguments, temp_dir, Path(output_file), timeout=timeout
            )
            return output_bytes
        except Exception as err:
            logger.error("Error during Doc to PDF conversion: %s", err)
            logger.exception(err)


def convert_images_to_ocred_pdf(
    filenames: list[str | Path], language="en", instructions=None
):
    filenames = [Path(f) for f in filenames]
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        try:
            output_file = temp_dir / "out.pdf"
            pdf_bytes = convert_images_to_pdf(filenames, instructions=instructions)

            with open(output_file, "wb") as f:
                f.write(pdf_bytes)

            return run_ocr(output_file, language=language, timeout=180)

        except Exception as err:
            logger.error("Error during convert images to ocred pdf: %s", err)
            logger.exception(err)
            return None


def run_ocr(
    filename: Path, language: Optional[str] = None, binary_name="ocrmypdf", timeout=50
):
    if binary_name is None:
        return
    with tempfile.TemporaryDirectory() as outpath:
        outpath = Path(outpath)
        output_file = outpath / "out.pdf"
        lang = TESSERACT_LANGUAGE.get(language)
        arguments = [binary_name]
        if lang is not None:
            arguments.extend(
                [
                    "-l",
                    lang,
                ]
            )
        arguments += [
            "--deskew",
            "--skip-text",
            # '--title', title
            str(filename),
            str(output_file),
        ]
        try:
            output_bytes = shell_call(arguments, outpath, output_file, timeout=timeout)
            return output_bytes
        except Exception as err:
            logger.error("Error during PDF OCR: %s", err)
            logger.exception(err)


def shell_call(
    arguments: list[str],
    outpath: Path,
    output_file: Optional[Path] = None,
    timeout=50,
    raise_timeout=False,
    successful_returncodes=None,
) -> bytes:
    if successful_returncodes is None:
        successful_returncodes = [0]
    env = dict(os.environ)
    env.update({"HOME": outpath})

    logger.info("Running: %s", arguments)
    out, err = "", ""
    p = None
    try:
        p = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        if p is not None:
            p.kill()
            out, err = p.communicate()
        if raise_timeout:
            raise e
    finally:
        if p is not None and p.returncode is None:
            p.kill()
            out, err = p.communicate()
    if p is not None and p.returncode in successful_returncodes:
        if output_file is not None and output_file.exists():
            with open(output_file, "rb") as f:
                return f.read()
    if output_file is not None:
        raise Exception(err)


def run_command_overwrite(
    filename: Path,
    argument_func: ShellRecipeMaker,
    timeout=50,
    successful_returncodes=None,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        arguments, temp_out = argument_func(filename, temp_dir)
        try:
            output_bytes = shell_call(
                arguments,
                temp_dir,
                temp_out,
                timeout=timeout,
                successful_returncodes=successful_returncodes,
            )

            with open(filename, "wb") as f:
                f.write(output_bytes)
            return filename
        except Exception as err:
            logger.error("Error during command overwrite %s", err)
            logger.exception(err)
            return None


def get_decrypt_pdf_recipe(
    filename: Path, temp_dir: Path, password: Optional[str]
) -> ShellRecipe:
    temp_out = temp_dir / "qpdf_out.pdf"
    arguments = ["qpdf", "--decrypt"]

    if password is not None:
        arguments.extend(["--password=%s" % password])

    arguments.extend([str(filename), str(temp_out)])
    return ShellRecipe(arguments, temp_out)


def decrypt_pdf_recipe_with_password(password: str) -> ShellRecipeMaker:
    def inner(filename: Path, temp_dir: Path) -> ShellRecipe:
        return get_decrypt_pdf_recipe(filename, temp_dir, password)

    return inner


def decrypt_pdf(
    filename: Path, password: Optional[str] = None, timeout: int = 50
) -> Optional[bytes]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        arguments, temp_out = get_decrypt_pdf_recipe(filename, temp_dir, password)
        resulting_bytes = shell_call(
            arguments,
            temp_dir,
            temp_out,
            timeout=timeout,
            successful_returncodes=[0, 3],  # qpdf returns 0 on success and 3 on warning
        )
        return resulting_bytes


def decrypt_pdf_in_place(filename: Path, password: Optional[str] = None, timeout=50):
    return run_command_overwrite(
        filename,
        decrypt_pdf_recipe_with_password(password),
        timeout=timeout,
        successful_returncodes=[0, 3],  # qpdf returns 0 on success and 3 on warning
    )


def rewrite_pdf_in_place(filename: Path, password=None, timeout=50):
    def argument_func(filename: Path, temp_dir: Path):
        temp_out = temp_dir / "gs_pdf_out.pdf"
        arguments = [
            "gs",
            "-o",
            str(temp_out),
        ]
        if password is not None:
            arguments.extend(["-sPDFPassword=%s" % password])
        arguments.extend(
            ["-sDEVICE=pdfwrite", "-dPDFSETTINGS=/prepress", str(filename)]
        )
        return arguments, temp_out

    return run_command_overwrite(filename, argument_func, timeout=timeout)


def rewrite_hard_pdf_in_place(filename: Path, password=None, timeout=50):
    def argument_func(filename, temp_dir):
        temp_out = temp_dir / "pdfcairo_out.pdf"
        arguments = [
            "pdftocairo",
            "-pdf",
        ]
        if password is not None:
            arguments.extend(["-upw", password])
        arguments.extend([str(filename), str(temp_out)])
        return arguments, temp_out

    return run_command_overwrite(filename, argument_func, timeout=timeout)


MAX_HEIGHT_A4 = 3507  # in pixels at 300 dpi


def convert_images_to_pdf(filenames: list[Path], instructions=None, dpi=300):
    if instructions is None:
        instructions = [{} for _ in range(len(filenames))]
    a4_width, a4_height = A4
    writer = io.BytesIO()
    pdf = canvas.Canvas(writer, pagesize=A4)
    for filename, instruction in zip(filenames, instructions, strict=False):
        with Image(filename=str(filename), resolution=dpi) as image:
            image.background_color = Color("white")
            image.format = "jpg"
            image.alpha_channel = "remove"
            try:
                degree = instruction.get("rotate", 0)
                if degree and degree % 90 == 0:
                    image.rotate(degree)
            except ValueError:
                pass

            if image.width > image.height:
                ratio = MAX_HEIGHT_A4 / image.width
            else:
                ratio = MAX_HEIGHT_A4 / image.height
            if ratio < 1:
                image.resize(round(ratio * image.width), round(ratio * image.height))

            width = image.width * 72 / dpi
            height = image.height * 72 / dpi
            pdf.setPageSize((width, height))
            reportlab_io_img = ImageReader(io.BytesIO(image.make_blob()))
            pdf.drawImage(reportlab_io_img, 0, 0, width=width, height=height)
            pdf.showPage()
    pdf.save()
    return writer.getvalue()


def get_images_from_pdf(
    pdf_reader: PdfReader,
    filename: Path,
    pages: list[int],
    max_dpi=300,
    max_resolution=MAX_HEIGHT_A4,
    timeout=5 * 60,
):
    for page in pages:
        with get_image_from_pdf_page(
            pdf_reader,
            filename,
            page=page,
            max_dpi=max_dpi,
            max_resolution=max_resolution,
            timeout=timeout,
        ) as image:
            if image is not None:
                yield image


@contextlib.contextmanager
def get_image_from_pdf_page(
    pdf_reader: PdfReader,
    filename: Path,
    page: int,
    max_dpi: int,
    max_resolution: int,
    timeout: int,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        try:
            yield page_to_png(
                pdf_reader=pdf_reader,
                filename=filename,
                temp_dir=temp_dir,
                page=page,
                max_dpi=max_dpi,
                max_resolution=max_resolution,
                timeout=timeout,
            )
        except Exception as err:
            logger.error("Error during page to png %s", err)
            logger.exception(err)
            yield None


def page_to_png(
    pdf_reader: PdfReader,
    filename: Path,
    temp_dir: Path,
    page: int,
    max_dpi: int,
    max_resolution: int,
    timeout: int,
):
    temp_out = temp_dir / "image"

    page_size = pdf_reader.pages[page - 1].cropbox
    max_x_dpi = max_resolution / (page_size.width / 72)
    max_y_dpi = max_resolution / (page_size.height / 72)
    dpi = min(max_dpi, max_x_dpi, max_y_dpi)

    command = [
        "pdftoppm",
        "-png",
        "-cropbox",
        "-r",
        str(dpi),
        "-singlefile",
        "-f",
        str(page),
        str(filename),
        str(temp_out),
    ]
    shell_call(command, temp_dir, output_file=None, timeout=timeout, raise_timeout=True)

    out_filename = glob.glob(str(temp_out) + "*")[0]
    return (page, out_filename)


def get_continuous_pages(pages: list[int]) -> Generator[tuple[int, int], None, None]:
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


def detect_tables(filename: Path):
    try:
        import camelot
    except ImportError:
        return None
    try:
        tables = camelot.read_pdf(filename)
        return [table.parsing_report for table in tables]
    except Exception:
        # Camelot may fail on bad pdfs, just ignore
        return []


def calculcate_content_hash_from_file(file_object: BinaryIO):
    h = hashlib.sha1()
    file_object.seek(0)
    while True:
        chunk = file_object.read(h.block_size)
        if not chunk:
            break
        h.update(chunk)
    file_object.seek(0)
    return h.hexdigest()


def rotate_pages_on_pdf(input_fh, output_fh, page_numbers, angle):
    with pikepdf.Pdf.open(input_fh) as pdf:
        for page_num in page_numbers:
            page = pdf.pages[page_num - 1]
            page.rotate(angle, relative=True)
        pdf.save(output_fh)
