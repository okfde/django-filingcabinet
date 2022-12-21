from collections import defaultdict

from filingcabinet.views import ensure_unique_filename


def test_ensure_unique_filename():
    filename_counter = defaultdict(int)

    assert ensure_unique_filename(filename_counter, "file.pdf") == "file.pdf"
    assert ensure_unique_filename(filename_counter, "file.pdf") == "file-1.pdf"
    assert ensure_unique_filename(filename_counter, "file.pdf") == "file-2.pdf"
    assert ensure_unique_filename(filename_counter, "file.pdf") == "file-3.pdf"
    assert ensure_unique_filename(filename_counter, "dir/file.pdf") == "dir/file.pdf"
    assert ensure_unique_filename(filename_counter, "dir/file.pdf") == "dir/file-1.pdf"
    assert ensure_unique_filename(filename_counter, "dir/file.pdf") == "dir/file-2.pdf"
    assert ensure_unique_filename(filename_counter, "file-1.pdf") == "file-1-1.pdf"
    assert ensure_unique_filename(filename_counter, "file-4.pdf") == "file-4.pdf"
    assert ensure_unique_filename(filename_counter, "file.pdf") == "file-5.pdf"
