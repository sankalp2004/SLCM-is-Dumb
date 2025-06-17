# exceptions.py
# Custom exceptions for the SLCM scraper project

class SLCMScraperError(Exception):
    """Base exception for SLCM scraper"""
    pass

class LoginError(SLCMScraperError):
    """Raised when login fails"""
    pass

class TokenExtractionError(SLCMScraperError):
    """Raised when form tokens cannot be extracted"""
    pass

class CGPAExtractionError(SLCMScraperError):
    """Raised when CGPA cannot be extracted"""
    pass
