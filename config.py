# config.py
# This file should only be imported, not executed directly. All configuration is loaded from here.
import os
from dotenv import load_dotenv

load_dotenv()

# URLs
LOGIN_URL = "https://slcm.manipal.edu/loginForm.aspx"
GRADE_SHEET_URL = "https://slcm.manipal.edu/GradeSheet.aspx"

# Credentials
USERNAME = os.getenv('SLCM_USERNAME')
PASSWORD = os.getenv('SLCM_PASSWORD')

# Paths
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', './chromedriver.exe')
TESSERACT_PATH = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

# OCR Settings
TESSERACT_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.CGPA:'

# Selenium Settings
IMPLICIT_WAIT = 10
PAGE_LOAD_TIMEOUT = 30 