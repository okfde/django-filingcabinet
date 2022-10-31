import os
import tempfile
from contextlib import contextmanager

from django.core.files.storage import default_storage


def chunks(li, n):
    n = max(1, n)
    return (li[i : i + n] for i in range(0, len(li), n))


def estimate_time(filesize, page_count=None):
    """
    Estimate processing time as
    one minute + 5 seconds per megabyte timeout
    """
    return int(60 + 5 * filesize / (1024 * 1024))


@contextmanager
def get_local_file(path, storage=default_storage):
    _, extension = os.path.splitext(path)
    local_file_path = None
    try:
        local_file = tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=extension
        )

        local_file.write(storage.open(path).read())
        local_file.flush()
        local_file_path = local_file.name
        local_file.close()

        yield local_file.name
    finally:
        if local_file_path:
            os.remove(local_file_path)
