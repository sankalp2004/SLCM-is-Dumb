# SLCM CGPA Scraper
Are you a Manipal student? Do you hate SLCM? Do you find the UI stupid and confusing and feel exhausted after navigating the website? Here's a Python-based web scraper for extracting CGPA information from the SLCM (Student Life Cycle Management) portal using Selenium and advanced OCR techniques.
We could add other feature to this to the point we can extract everything from SLCM without ever navigating through it again.

## Features

- Automated login with captcha solving
- Multiple CGPA extraction strategies:
  - Direct element targeting
  - Table-based extraction
  - OCR with image preprocessing
  - Vision model extraction (using Ollama)
  - Screenshot + LLM fallback
- Robust error handling and retry mechanisms
- Comprehensive logging
- Support for new tab navigation

## Prerequisites

1. Python 3.13 or higher
2. Chrome browser installed
3. Tesseract OCR installed
4. Ollama installed (optional, for enhanced captcha solving)

## Installation

1. Clone the repository:
```powershell
git clone <repository-url>
cd "Slcm is dumb"
```

2. Create and activate a virtual environment:
```powershell
python -m venv scraper_env
.\scraper_env\Scripts\activate
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Install Tesseract OCR:
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install to default location: `C:\Program Files\Tesseract-OCR`

5. Install Ollama (optional):
- Download from: https://ollama.ai/download
- Install and pull the vision model:
```powershell
ollama pull llava:13b
```

## Configuration

1. Copy the example environment file:
```powershell
copy .env.example .env
```

2. Edit the `.env` file with your credentials and paths:
```env
# SLCM Login Credentials
SLCM_USERNAME=your_username
SLCM_PASSWORD=your_password

# System Paths
CHROME_PATH=path_to_chrome.exe
CHROME_DRIVER_PATH=path_to_chromedriver.exe
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# Optional: OCR Configuration
TESSERACT_CONFIG=--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.CGPA:

# Optional: Debug Settings
DEBUG_MODE=true
HEADLESS_BROWSER=false
```

## Usage

1. Ensure your virtual environment is activated:
```powershell
.\scraper_env\Scripts\activate
```

2. Run the scraper:
```powershell
python scraper.py
```

The script will:
- Attempt to log in automatically
- Navigate to the grade sheet
- Extract your CGPA
- Display the result
- Wait for user input before closing

## Troubleshooting

1. If automatic login fails:
   - The script will prompt for manual login
   - Enter your credentials manually in the browser window
   - Press Enter after successful login

2. Common issues:
   - Captcha solving failures: Ensure Tesseract is properly installed
   - Vision model errors: Check Ollama installation and model availability
   - Browser automation issues: Verify Chrome and ChromeDriver versions match

## Dependencies

- selenium: Web automation
- pytesseract: OCR for captcha solving
- Pillow: Image processing
- opencv-python: Advanced image processing
- python-dotenv: Environment variable management
- numpy: Numerical operations
- requests: HTTP requests
- ollama: Vision model integration (optional)
- llava:13b: Local LLM model for vision tasks

## Security Note

- Never commit your `.env` file to version control
- Keep your credentials secure
- The `.env.example` file is provided as a template only

## License

MIT License
## Contributing

Please Feel Free to Fork and Contribute
