import os
import re

import pytest
from playwright.sync_api import Page, expect

LOGIN_URL = "https://app.integricoreglobal.com/"
INVALID_LOGIN_MSG = "Invalid identifier or password"
SHORT_PASSWORD_MSG = "Password must be at least 6 characters long"

# Delay (ms) after every browser action so it is easy to watch.
# Set to 0 for a fast run.
SLOW_MO_MS = int(os.getenv("SLOW_MO_MS", "1000"))


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "headless": False, "slow_mo": SLOW_MO_MS}


# ---------------------------------------------------------------- helpers
@pytest.fixture
def login_page(page: Page) -> Page:
    """Open the login page with the Administrator tab selected."""
    page.goto(LOGIN_URL)
    page.get_by_role("button", name="Administrator").first.click()
    expect(page.locator("#email")).to_be_visible()
    return page


@pytest.fixture
def credentials():
    email = os.getenv("INTEGRICORE_EMAIL")
    password = os.getenv("INTEGRICORE_PASSWORD")
    if not email or not password:
        pytest.skip("INTEGRICORE_EMAIL / INTEGRICORE_PASSWORD not set")
    return email, password


def email_input(page: Page):
    return page.locator("#email")


def password_input(page: Page):
    return page.locator("#password")


def sign_in(page: Page, email: str = "", password: str = ""):
    email_input(page).fill(email)
    password_input(page).fill(password)
    page.get_by_role("button", name="SIGN IN").click()


def is_invalid(locator) -> bool:
    """Playwright Python has no to_be_invalid(); ask the browser instead."""
    return locator.evaluate("el => !el.checkValidity()")


def assert_still_on_login(page: Page):
    expect(page).to_have_url(re.compile(r"app\.integricoreglobal\.com/?$"))
    expect(password_input(page)).to_be_visible()


# =================================================================
# UI / PAGE-LOAD TESTS (positive)
# =================================================================
def test_login_page_elements_visible(login_page: Page):
    expect(login_page).to_have_title("Hospitality Panel")
    expect(email_input(login_page)).to_be_visible()
    expect(password_input(login_page)).to_be_visible()
    expect(login_page.get_by_role("button", name="SIGN IN")).to_be_visible()
    expect(login_page.get_by_role("link", name="Forgot password?")).to_be_visible()


def test_login_page_placeholders(login_page: Page):
    expect(email_input(login_page)).to_have_attribute("placeholder", "Enter your email")
    expect(password_input(login_page)).to_have_attribute(
        "placeholder", "Enter your password"
    )


def test_password_is_masked_by_default(login_page: Page):
    expect(password_input(login_page)).to_have_attribute("type", "password")


def test_password_visibility_toggle(login_page: Page):
    password_input(login_page).fill("SomePassword123")
    toggle = login_page.locator("#password ~ button")

    toggle.click()
    expect(password_input(login_page)).to_have_attribute("type", "text")

    toggle.click()
    expect(password_input(login_page)).to_have_attribute("type", "password")


def test_forgot_password_link_navigates(login_page: Page):
    login_page.get_by_role("link", name="Forgot password?").click()
    expect(login_page).to_have_url(re.compile(r"/forgot-password"))


def test_administrator_portal_heading_visible(login_page: Page):
    expect(
        login_page.get_by_role("heading", name="Administrator Portal")
    ).to_be_visible()


# =================================================================
# POSITIVE LOGIN TESTS (need real credentials in env vars)
# =================================================================
def test_login_with_valid_credentials(login_page: Page, credentials):
    email, password = credentials
    sign_in(login_page, email, password)

    # Successful login leaves the login form behind.
    expect(password_input(login_page)).to_be_hidden(timeout=15000)
    expect(login_page.get_by_text(INVALID_LOGIN_MSG)).to_have_count(0)


def test_login_by_pressing_enter(login_page: Page, credentials):
    email, password = credentials
    email_input(login_page).fill(email)
    password_input(login_page).fill(password)
    password_input(login_page).press("Enter")

    expect(password_input(login_page)).to_be_hidden(timeout=15000)


def test_login_email_is_case_insensitive(login_page: Page, credentials):
    email, password = credentials
    sign_in(login_page, email.upper(), password)

    expect(password_input(login_page)).to_be_hidden(timeout=15000)


# =================================================================
# NEGATIVE LOGIN TESTS
# =================================================================
def test_login_wrong_password(login_page: Page, credentials):
    email, _ = credentials
    sign_in(login_page, email, "Invalid-Test-Password-123!")

    expect(login_page.get_by_text(INVALID_LOGIN_MSG)).to_be_visible()
    assert_still_on_login(login_page)


def test_login_wrong_email(login_page: Page, credentials):
    _, password = credentials
    sign_in(login_page, "no.such.user.12345@example.com", password)

    expect(login_page.get_by_text(INVALID_LOGIN_MSG)).to_be_visible()
    assert_still_on_login(login_page)


def test_login_both_wrong(login_page: Page):
    sign_in(login_page, "no.such.user.12345@example.com", "Invalid-Test-Password-123!")

    expect(login_page.get_by_text(INVALID_LOGIN_MSG)).to_be_visible()
    assert_still_on_login(login_page)


def test_login_empty_fields(login_page: Page):
    login_page.get_by_role("button", name="SIGN IN").click()

    assert is_invalid(email_input(login_page))
    assert is_invalid(password_input(login_page))
    assert_still_on_login(login_page)


def test_login_empty_email_only(login_page: Page):
    sign_in(login_page, "", "SomePassword123")

    assert is_invalid(email_input(login_page))
    assert_still_on_login(login_page)


def test_login_empty_password_only(login_page: Page):
    sign_in(login_page, "someone@example.com", "")

    assert is_invalid(password_input(login_page))
    assert_still_on_login(login_page)


@pytest.mark.parametrize(
    "bad_email",
    [
        "plainaddress",
        "missing-at-sign.com",
        "@no-local-part.com",
        "user@",
        "user@@example.com",
        "user name@example.com",
    ],
)
def test_login_invalid_email_format(login_page: Page, bad_email):
    sign_in(login_page, bad_email, "SomePassword123")

    assert is_invalid(email_input(login_page))
    assert_still_on_login(login_page)


@pytest.mark.parametrize(
    "payload",
    [
        "' OR '1'='1",
        "admin'--",
        "<script>alert(1)</script>",
        "\" OR \"\"=\"",
    ],
)
def test_login_injection_payload_in_password(login_page: Page, payload):
    sign_in(login_page, "someone@example.com", payload)

    expect(login_page.get_by_text(INVALID_LOGIN_MSG)).to_be_visible()
    assert_still_on_login(login_page)


def test_login_sql_injection_in_email_is_rejected(login_page: Page):
    sign_in(login_page, "' OR '1'='1", "SomePassword123")

    # type="email" validation must block this before it is sent.
    assert is_invalid(email_input(login_page))
    assert_still_on_login(login_page)


def test_login_very_long_inputs(login_page: Page):
    long_email = ("a" * 300) + "@example.com"
    sign_in(login_page, long_email, "P" * 1000)

    # Must fail cleanly: still on the login page, no crash / blank screen.
    assert_still_on_login(login_page)


def test_login_password_too_short(login_page: Page):
    sign_in(login_page, "someone@example.com", "12345")

    expect(login_page.get_by_text(SHORT_PASSWORD_MSG)).to_be_visible()
    assert_still_on_login(login_page)


def test_login_whitespace_only_password(login_page: Page):
    sign_in(login_page, "someone@example.com", "     ")

    expect(login_page.get_by_text(SHORT_PASSWORD_MSG)).to_be_visible()
    assert_still_on_login(login_page)


def test_password_not_exposed_in_url(login_page: Page):
    secret = "Sup3r-Secret-Pass!"
    sign_in(login_page, "someone@example.com", secret)

    login_page.wait_for_timeout(1500)
    assert secret not in login_page.url
    assert "password" not in login_page.url.lower()


def test_error_message_does_not_reveal_which_field_is_wrong(
    login_page: Page, credentials
):
    """Same generic message for wrong email and wrong password."""
    email, password = credentials

    sign_in(login_page, email, "Invalid-Test-Password-123!")
    wrong_password_msg = login_page.get_by_text(INVALID_LOGIN_MSG)
    expect(wrong_password_msg).to_be_visible()

    sign_in(login_page, "no.such.user.12345@example.com", password)
    expect(login_page.get_by_text(INVALID_LOGIN_MSG)).to_be_visible()


def test_protected_page_requires_login(page: Page):
    """Opening an inner page without logging in must not show the dashboard."""
    page.goto(LOGIN_URL + "dashboard")

    expect(password_input(page)).to_be_visible(timeout=10000)
