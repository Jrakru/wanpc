"""Custom exceptions for wanpc package."""

class WanpcError(Exception):
    """Base exception for wanpc package."""
    pass

class PackageCreationError(WanpcError):
    """Raised when there is an error creating a package."""
    pass

class ConfigError(WanpcError):
    """Raised when there is an error with configuration."""
    pass
