import os

from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        # FIXME: max_length is ignored
        # If the filename already exists,
        # remove it as if it was a true file system
        if self.exists(name):
            full_path = self.path(name)
            os.remove(full_path)
        return name
