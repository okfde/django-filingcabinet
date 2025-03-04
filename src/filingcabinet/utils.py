import os
import tempfile
from contextlib import contextmanager
from typing import Generator

from django.core.files.storage import default_storage


@contextmanager
def get_local_file(path, storage=default_storage) -> Generator[str, None, None]:
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
