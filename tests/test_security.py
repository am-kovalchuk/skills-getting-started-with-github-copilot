"""
Security tests for XSS prevention in the frontend.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestXSSPrevention:
    """Test cases to verify XSS prevention measures."""

    def test_malicious_email_signup(self, client):
        """Test that malicious email addresses are handled safely."""
        malicious_email = "<script>alert('email')</script>@evil.com"
        
        response = client.post(f"/activities/Chess Club/signup?email={malicious_email}")
        assert response.status_code == 200

    def test_url_encoding_with_malicious_content(self, client):
        """Test that URL encoding properly handles malicious content."""
        # URL encoded script tag
        encoded_script = "%3Cscript%3Ealert('xss')%3C/script%3E"
        
        response = client.post(f"/activities/{encoded_script}/signup?email=test@safe.com")
        # Should return 404 since the decoded activity name doesn't exist
        assert response.status_code == 404

    def test_double_quote_escaping(self, client):
        """Test that double quotes in data are handled safely."""
        # Add participant with double quotes
        double_quote_email = 'test"onclick=alert("xss")"@evil.com'
        response = client.post(f"/activities/Chess Club/signup?email={double_quote_email}")
        assert response.status_code == 200
        
        # Verify it was added
        response = client.get("/activities")
        activities_data = response.json()
        assert double_quote_email in activities_data["Chess Club"]["participants"]

    def test_single_quote_in_email(self, client):
        """Test that single quotes in email are handled safely."""
        quote_email = "test'test@evil.com"
        
        response = client.post(f"/activities/Chess Club/signup?email={quote_email}")
        assert response.status_code == 200
        
        # Verify it was added
        response = client.get("/activities")
        activities_data = response.json()
        assert quote_email in activities_data["Chess Club"]["participants"]

    def test_backend_does_not_validate_html_content(self, client):
        """Test that the backend accepts but doesn't validate HTML content."""
        # Backend should accept any string content - validation is frontend responsibility
        malicious_email = "<script>document.location='http://evil.com'</script>@test.com"
        
        response = client.post(f"/activities/Chess Club/signup?email={malicious_email}")
        assert response.status_code == 200
        
        # Verify the malicious email was stored as-is
        response = client.get("/activities")
        activities_data = response.json()
        assert malicious_email in activities_data["Chess Club"]["participants"]

    def test_html_tags_in_email(self, client):
        """Test that HTML tags in emails are accepted by backend."""
        html_email = "<img src=x onerror=alert('xss')>@evil.com"
        
        response = client.post(f"/activities/Programming Class/signup?email={html_email}")
        assert response.status_code == 200
        
        response = client.get("/activities")
        activities_data = response.json()
        assert html_email in activities_data["Programming Class"]["participants"]

    def test_script_tags_in_email(self, client):
        """Test that script tags in emails are accepted but should be escaped by frontend."""
        script_email = "<script>alert('xss')</script>@evil.com"
        
        response = client.post(f"/activities/Gym Class/signup?email={script_email}")
        assert response.status_code == 200
        
        # Verify it was stored
        response = client.get("/activities")
        activities_data = response.json()
        assert script_email in activities_data["Gym Class"]["participants"]

    def test_mixed_quotes_and_html(self, client):
        """Test mixed quotes and HTML content."""
        complex_email = """test'"><script>alert("xss")</script>@evil.com"""
        
        response = client.post(f"/activities/Chess Club/signup?email={complex_email}")
        assert response.status_code == 200
        
        response = client.get("/activities")
        activities_data = response.json()
        assert complex_email in activities_data["Chess Club"]["participants"]