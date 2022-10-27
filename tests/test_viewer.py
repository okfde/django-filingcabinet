def test_document_viewer(page, live_server, processed_document):
    page.goto(live_server.url + processed_document.get_absolute_url())
    assert processed_document.title in page.title()
    assert page.query_selector("h2").text_content() == processed_document.title
    page.pause()
