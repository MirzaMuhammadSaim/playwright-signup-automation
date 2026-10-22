from playwright.sync_api import Page, expect


def test_homepage_title(page: Page):
    page.goto("https://playwright.dev/")

    expect(page).to_have_title(
        "Fast and reliable end-to-end testing for modern web apps | Playwright"
    )


def test_get_started_navigation(page: Page):
    page.goto("https://playwright.dev/")

    page.get_by_role(
        "link", name="Get started"
    ).click()

    expect(
        page.get_by_role("heading", name="Installation")
    ).to_be_visible()