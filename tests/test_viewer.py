import re
from urllib.parse import urlparse

from playwright.sync_api import expect

PAGE_IMAGE_RE = re.compile(r"page-p(\d+)-\w+\.png$")


def test_document_viewer(page, live_server, processed_document):
    page.goto(live_server.url + processed_document.get_absolute_url())
    assert processed_document.title in page.title()
    assert page.query_selector("h2").text_content() == processed_document.title


def test_keyboard_scroll(long_timeout_page, live_server, processed_document):
    page = long_timeout_page
    page.goto(live_server.url + processed_document.get_absolute_url())
    expect(page.locator(".document")).to_be_visible()
    expect(page.locator("#page-1")).to_be_visible()
    expect(page.locator("#page-2")).to_be_visible()
    expect(page.locator("#page-3")).not_to_be_visible()

    page.keyboard.down("PageDown")
    page.keyboard.down("PageDown")
    page.keyboard.down("PageDown")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#page-3")).to_be_visible()
    page.keyboard.down("PageDown")
    page.keyboard.down("PageDown")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#page-4")).to_be_visible()


def test_number_input_scroll(page, live_server, processed_document):
    page.goto(live_server.url + processed_document.get_absolute_url())
    expect(page.locator("#page-4")).not_to_be_visible()
    page.locator(".page-number-input").fill("4")
    page.keyboard.down("Enter")
    expect(page.locator("#page-4")).to_be_visible()
    page.locator(".page-number-input").fill("4")


def test_sidebar_hide(page, live_server, processed_document):
    page.goto(live_server.url + processed_document.get_absolute_url())
    expect(page.locator(".sidebar")).to_be_visible()
    page.locator(".fa-toggle-left").click()
    expect(page.locator(".sidebar")).not_to_be_visible()


def test_show_search_bar(page, live_server, processed_document):
    page.goto(live_server.url + processed_document.get_absolute_url())
    expect(page.locator(".document-searchbar")).not_to_be_visible()
    page.locator(".fa-search").click()
    expect(page.locator(".document-searchbar")).to_be_visible()


def test_document_viewer_load_images_progressively(
    page, live_server, processed_document
):
    page_image_requests = set()

    def record_page_image_request(request):
        nonlocal page_image_requests
        path = urlparse(request.url).path
        filename = path.split("/")[-1]
        if PAGE_IMAGE_RE.search(filename):
            page_image_requests.add(filename)

    page.on("request", record_page_image_request)

    page.goto(live_server.url + processed_document.get_absolute_url())
    assert processed_document.title in page.title()
    assert page.query_selector("h2").text_content() == processed_document.title

    assert "page-p1-original.png" in page_image_requests
    assert "page-p1-small.png" in page_image_requests
    assert "page-p2-small.png" in page_image_requests
    assert "page-p3-small.png" in page_image_requests

    assert "page-p4-original.png" not in page_image_requests
    page.mouse.wheel(0, 8000)
    page.wait_for_load_state("networkidle")
    assert "page-p4-small.png" in page_image_requests
    assert "page-p4-original.png" in page_image_requests
