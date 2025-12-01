"""
End-to-end tests for authentication flows.
"""
import pytest
from playwright.sync_api import Page, expect


class TestVolunteerLogin:
    """Test suite for volunteer login functionality."""

    def test_verified_volunteer_can_login(self, page: Page, django_server: str):
        """Test that a verified volunteer can successfully log in and reach dashboard."""
        # Navigate to the login page
        page.goto(f"{django_server}/accounts/login/")

        # Verify we're on the login page
        expect(page).to_have_title("Login - Volunteer Finder")

        # Fill in the login form
        page.fill('input[name="username"]', 'testvolunteer')
        page.fill('input[name="password"]', 'TestPass123!')

        # Submit the form
        page.click('button[type="submit"]')

        # Wait for navigation to complete
        page.wait_for_url(f"{django_server}/dashboard/volunteer/")

        # Verify we're on the volunteer dashboard
        expect(page).to_have_url(f"{django_server}/dashboard/volunteer/")

    def test_login_with_invalid_credentials_shows_error(self, page: Page, django_server: str):
        """Test that invalid credentials show an error message."""
        # Navigate to the login page
        page.goto(f"{django_server}/accounts/login/")

        # Fill in invalid credentials
        page.fill('input[name="username"]', 'testvolunteer')
        page.fill('input[name="password"]', 'WrongPassword123!')

        # Submit the form
        page.click('button[type="submit"]')

        # Verify we're still on the login page
        expect(page).to_have_url(f"{django_server}/accounts/login/")

        # Verify error message is displayed
        error_alert = page.locator('.alert-error')
        expect(error_alert).to_be_visible()
        expect(error_alert).to_contain_text('Invalid username or password')

    def test_unverified_volunteer_redirected_to_verification_page(self, page: Page, django_server: str):
        """Test that an unverified volunteer is redirected to email verification page."""
        # Navigate to the login page
        page.goto(f"{django_server}/accounts/login/")

        # Fill in the login form with unverified user
        page.fill('input[name="username"]', 'unverifiedvolunteer')
        page.fill('input[name="password"]', 'TestPass123!')

        # Submit the form
        page.click('button[type="submit"]')

        # Wait for navigation
        page.wait_for_url(f"{django_server}/accounts/verify-email/")

        # Verify we're on the email verification required page
        expect(page).to_have_url(f"{django_server}/accounts/verify-email/")

    def test_login_page_has_required_elements(self, page: Page, django_server: str):
        """Test that the login page has all required form elements."""
        # Navigate to the login page
        page.goto(f"{django_server}/accounts/login/")

        # Check for username input
        username_input = page.locator('input[name="username"]')
        expect(username_input).to_be_visible()

        # Check for password input
        password_input = page.locator('input[name="password"]')
        expect(password_input).to_be_visible()

        # Check for submit button
        submit_button = page.locator('button[type="submit"]')
        expect(submit_button).to_be_visible()
        expect(submit_button).to_have_text('Login')

        # Check for registration links
        volunteer_signup = page.locator('a', has_text='Sign up as Volunteer')
        expect(volunteer_signup).to_be_visible()

        org_signup = page.locator('a', has_text='Sign up as Organization')
        expect(org_signup).to_be_visible()

        # Check for forgot password link
        forgot_password = page.locator('a', has_text='Forgot Password')
        expect(forgot_password).to_be_visible()
