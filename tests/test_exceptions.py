"""Tests for custom exceptions."""

from wanpc.exceptions import PackageCreationError

def test_package_creation_error():
    """Test PackageCreationError exception."""
    error = PackageCreationError("Test error message")
    assert str(error) == "Test error message"
    assert isinstance(error, Exception)
