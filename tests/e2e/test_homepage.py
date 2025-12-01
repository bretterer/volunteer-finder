"""
End-to-end tests for the homepage.
"""
import pytest
from playwright.sync_api import Page, expect


class TestHomepage:
    """Test suite for the homepage."""

    def test_homepage_loads_successfully(self, page: Page, django_server: str):
        """Test that the homepage loads and renders correctly."""
        # Navigate to the homepage
        page.goto(django_server)

        # Verify the page title
        expect(page).to_have_title("Volunteer Finder - Connect. Serve. Make a Difference.")

    def test_homepage_hero_section_displays(self, page: Page, django_server: str):
        """Test that the hero section displays correctly."""
        page.goto(django_server)

        # Check for the main heading
        heading = page.locator("h1")
        expect(heading).to_be_visible()
        expect(heading).to_have_text("Connect. Serve. Make a Difference.")

        # Check for the hero description
        hero_text = page.locator(".hero-text p").first
        expect(hero_text).to_contain_text("Join thousands of volunteers")

    def test_homepage_navigation_links_present(self, page: Page, django_server: str):
        """Test that navigation links are present for unauthenticated users."""
        page.goto(django_server)

        # Check for logo link
        logo = page.locator(".logo-text")
        expect(logo).to_be_visible()
        expect(logo).to_have_text("Volunteer Finder")

        # Check for navigation links (unauthenticated state)
        nav_links = page.locator(".nav-links")
        expect(nav_links).to_be_visible()

        # Check for Browse Opportunities link
        browse_link = page.locator(".nav-links a", has_text="Browse Opportunities")
        expect(browse_link).to_be_visible()

        # Check for Login link
        login_link = page.locator(".nav-links a", has_text="Login")
        expect(login_link).to_be_visible()

        # Check for Sign Up button
        signup_button = page.locator(".nav-links a.nav-btn", has_text="Sign Up")
        expect(signup_button).to_be_visible()

    def test_homepage_cta_buttons_present(self, page: Page, django_server: str):
        """Test that call-to-action buttons are present."""
        page.goto(django_server)

        # Check for "Find Opportunities" button
        find_opportunities_btn = page.locator(".btn-primary", has_text="Find Opportunities")
        expect(find_opportunities_btn).to_be_visible()

        # Check for "Post an Opportunity" button
        post_opportunity_btn = page.locator(".btn-secondary", has_text="Post an Opportunity")
        expect(post_opportunity_btn).to_be_visible()

    def test_homepage_features_section_displays(self, page: Page, django_server: str):
        """Test that the features section displays correctly."""
        page.goto(django_server)

        # Check for features section heading
        features_heading = page.locator(".features h2")
        expect(features_heading).to_be_visible()
        expect(features_heading).to_have_text("Why Choose Volunteer Finder?")

        # Check that feature cards are present (should have 6 cards)
        feature_cards = page.locator(".feature-card")
        expect(feature_cards).to_have_count(6)

    def test_homepage_how_it_works_section_displays(self, page: Page, django_server: str):
        """Test that the 'How It Works' section displays correctly."""
        page.goto(django_server)

        # Check for section heading
        how_it_works_heading = page.locator(".how-it-works h2")
        expect(how_it_works_heading).to_be_visible()
        expect(how_it_works_heading).to_have_text("How It Works")

        # Check that there are 3 steps
        steps = page.locator(".step")
        expect(steps).to_have_count(3)

    def test_homepage_stats_section_displays(self, page: Page, django_server: str):
        """Test that the stats section displays correctly."""
        page.goto(django_server)

        # Check for stats section
        stats = page.locator(".stat")
        expect(stats).to_have_count(3)

        # Verify stat labels are visible
        stat_labels = page.locator(".stat-label")
        expect(stat_labels.nth(0)).to_contain_text("Volunteers")
        expect(stat_labels.nth(1)).to_contain_text("Organizations")
        expect(stat_labels.nth(2)).to_contain_text("Opportunities")

    def test_homepage_footer_displays(self, page: Page, django_server: str):
        """Test that the footer displays correctly."""
        page.goto(django_server)

        # Check for footer
        footer = page.locator("footer")
        expect(footer).to_be_visible()

        # Check for copyright text
        copyright_text = page.locator(".footer-bottom")
        expect(copyright_text).to_contain_text("2025 Volunteer Finder")
