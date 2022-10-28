from playwright.sync_api import expect


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

    expect(page.locator("#page-3")).to_be_visible()
    page.keyboard.down("PageDown")
    page.keyboard.down("PageDown")
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
