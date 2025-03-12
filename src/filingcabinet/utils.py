import os
import tempfile
from contextlib import contextmanager
from pathlib import PurePath
from typing import Generator

from django.core.files.storage import default_storage

from .models import CollectionDirectory, DocumentCollection


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


DirectoryDict = dict[PurePath, CollectionDirectory]


def ensure_directory_exists(
    collection: DocumentCollection, directories: DirectoryDict, path: PurePath, user
) -> DirectoryDict:
    directories = directories.copy()

    for parent_path in reversed(path.parents):
        if str(parent_path) == ".":
            continue
        if parent_path not in directories:
            parent_parent_path = parent_path.parent
            parent_parent_dir = directories.get(parent_parent_path)
            directory = CollectionDirectory(
                name=PurePath(parent_path).name,
                user=user,
                collection=collection,
            )
            if parent_parent_dir is None:
                directory = CollectionDirectory.add_root(instance=directory)
            else:
                directory = parent_parent_dir.add_child(instance=directory)
            directories[parent_path] = directory

    return directories


def get_existing_directories(collection: DocumentCollection) -> DirectoryDict:
    directories = {}
    dirs = CollectionDirectory.objects.filter(collection=collection)
    for dir in dirs:
        tree_to_root = list(dir.get_ancestors()) + [dir]
        path = PurePath("/".join([x.name for x in tree_to_root]))
        directories[path] = dir
    return directories
