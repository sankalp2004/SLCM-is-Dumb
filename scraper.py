print("[DEBUG] scraper.py started")
# scraper.py - New Tab Navigation & LLM Fallback for CGPA Extraction
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import re
import time
import os
import sys
import logging
from config import *
from utils import setup_logging, retry_on_failure
from exceptions import LoginError, TokenExtractionError, CGPAExtractionError
from dotenv import load_dotenv
import ollama
import base64
import io
import json
from collections import Counter

# Load environment variables
load_dotenv()
print("[DEBUG] Environment variables loaded")

# Configure logging
logger = logging.getLogger(__name__)
print("[DEBUG] Logger configured")

print("[DEBUG] scraper.py started")

class SLCMScraper:
    def __init__(self):
        print("[DEBUG] SLCMScraper.__init__ started")
        try:
        self.driver = None
            self.ollama_available = False
            self.captcha_attempts = []
            self.captcha_failure_analysis = []
            self.login_attempts = 0
            self.current_window = None  # Track current window
            self.gradesheet_window = None  # Track gradesheet window
            print("[DEBUG] About to setup driver")
        self.setup_driver()
            print("[DEBUG] Driver setup completed")
            
            # Test Ollama availability
            self.check_ollama_availability()
            
        if TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
                if not os.path.exists(TESSERACT_PATH):
                    logger.error(f"Tesseract not found at {TESSERACT_PATH}")
                    print("[WARNING] Tesseract not found - OCR fallback may not work")
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            raise
    
    def check_ollama_availability(self):
        """Check if Ollama is available and has vision models"""
        try:
            models = ollama.list()
            vision_models = []
            
            for model in models.get('models', []):
                model_name = model['name']
                if any(vm in model_name.lower() for vm in ['llava', 'vision', 'llama3.2-vision']):
                    vision_models.append(model_name)
            
            if vision_models:
                self.ollama_available = True
                # Prefer llava:13b if available
                preferred_models = ['llava:13b', 'llava:latest', 'llama3.2-vision']
                self.vision_model = None
                
                for preferred in preferred_models:
                    if any(preferred in vm for vm in vision_models):
                        self.vision_model = preferred
                        break
                
                if not self.vision_model:
                    self.vision_model = vision_models[0]
                
                print(f"✓ Ollama available with vision model: {self.vision_model}")
                logger.info(f"Ollama initialized with model: {self.vision_model}")
            else:
                print("✗ No vision models found in Ollama")
                self.ollama_available = False
                
        except Exception as e:
            print(f"✗ Ollama not available: {e}")
            self.ollama_available = False
    
    def verify_config(self):
        """Verify that all required configuration is loaded"""
        print("=== CONFIGURATION VERIFICATION ===")
        
        if not USERNAME:
            raise ValueError("USERNAME not found in environment variables")
        if not PASSWORD:
            raise ValueError("PASSWORD not found in environment variables")
        
        print(f"✓ Username loaded: {USERNAME[:3]}***")
        print(f"✓ Password loaded: {'*' * len(PASSWORD)}")
        print(f"✓ Ollama available: {self.ollama_available}")
        if self.ollama_available:
            print(f"✓ Vision model: {self.vision_model}")
        print("✓ All credentials configured")
    
    def setup_driver(self):
        """Setup Chrome driver with enhanced options for captcha solving"""
        try:
        chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
            
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
            
            chrome_driver_path = os.getenv('CHROME_DRIVER_PATH')
            
            if chrome_driver_path and os.path.exists(chrome_driver_path):
                service = Service(chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(IMPLICIT_WAIT)
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            logger.info("Enhanced Chrome driver setup successful")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def is_session_valid(self):
        """Check if the WebDriver session is still valid"""
        try:
            self.driver.current_url
            return True
        except:
            return False
    
    # [ENHANCED CAPTCHA SOLVING METHODS - Keep existing enhanced captcha code]
    def ultra_preprocess_captcha_image(self, image_path):
        """Ultra-aggressive preprocessing for 3-digit captchas with multiple techniques"""
        try:
            image = cv2.imread(image_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            height, width = image_rgb.shape[:2]
            scale_factor = max(200/height, 600/width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            pil_image = Image.fromarray(image_rgb)
            enhanced_versions = []
            
            # Version 1: Maximum contrast and sharpness
            enhancer = ImageEnhance.Contrast(pil_image)
            max_contrast = enhancer.enhance(4.0)
            enhancer = ImageEnhance.Sharpness(max_contrast)
            max_sharp = enhancer.enhance(3.0)
            enhancer = ImageEnhance.Brightness(max_sharp)
            max_bright = enhancer.enhance(1.1)
            enhanced_versions.append(("max_enhance", max_bright))
            
            # Version 2: Noise reduction focused
            enhancer = ImageEnhance.Contrast(pil_image)
            clean_contrast = enhancer.enhance(2.5)
            clean_filtered = clean_contrast.filter(ImageFilter.MedianFilter(size=3))
            enhancer = ImageEnhance.Sharpness(clean_filtered)
            clean_sharp = enhancer.enhance(2.0)
            enhanced_versions.append(("noise_reduced", clean_sharp))
            
            # Version 3: Edge enhancement
            edge_enhanced = pil_image.filter(ImageFilter.EDGE_ENHANCE_MORE)
            enhancer = ImageEnhance.Contrast(edge_enhanced)
            edge_contrast = enhancer.enhance(2.8)
            enhanced_versions.append(("edge_enhanced", edge_contrast))
            
            return enhanced_versions
            
        except Exception as e:
            print(f"Ultra image preprocessing failed: {e}")
            return [("original", Image.open(image_path))]
    
    def solve_captcha_with_ollama_enhanced(self, image_path):
        """Enhanced Ollama captcha solving with improved prompts"""
        try:
            if not self.ollama_available:
                return []
            
            print(f"Solving 3-digit captcha with enhanced Ollama {self.vision_model}...")
            enhanced_versions = self.ultra_preprocess_captcha_image(image_path)
            
            enhanced_prompts = [
                "This image shows a 3-digit security code. Look carefully at each digit from left to right. The digits are numbers 0-9. Respond with exactly 3 digits, like 123 or 456 or 789.",
                "Extract the 3-digit verification code from this captcha. Focus on the numbers only. Ignore any background noise. Return just the 3 consecutive numbers.",
                "I need the 3-digit captcha code from this image. Each position contains one digit (0-9). Read from left to right and give me the 3-digit number.",
                "This security image contains exactly 3 numerical digits. Identify each digit carefully. Respond with only the 3-digit code.",
                "Look at this 3-digit captcha. What numbers do you see? Give me the complete 3-digit code as one number."
            ]
            
            ollama_results = []
            
            for version_name, enhanced_image in enhanced_versions:
                enhanced_path = image_path.replace('.png', f'_{version_name}.png')
                enhanced_image.save(enhanced_path)
                
                for i, prompt in enumerate(enhanced_prompts):
                    try:
                        response = ollama.chat(
                            model=self.vision_model,
                            messages=[{
                                'role': 'user',
                                'content': prompt,
                                'images': [enhanced_path]
                            }],
                            options={'temperature': 0.1, 'top_p': 0.9}
                        )
                        
                        result = response['message']['content'].strip()
                        numeric_result = ''.join(c for c in result if c.isdigit())
                        
                        if len(numeric_result) == 3:
                            ollama_results.append(numeric_result)
                            print(f"✓ Enhanced Ollama ({version_name}, prompt {i+1}): {numeric_result}")
                        elif len(numeric_result) > 3:
                            truncated = numeric_result[:3]
                            ollama_results.append(truncated)
                            print(f"✓ Enhanced Ollama ({version_name}, prompt {i+1}) truncated: {truncated}")
                        else:
                            print(f"Enhanced Ollama ({version_name}, prompt {i+1}) invalid: '{result}' -> '{numeric_result}'")
                            
                    except Exception as e:
                        print(f"Enhanced Ollama ({version_name}, prompt {i+1}) failed: {e}")
                        continue
                
                try:
                    os.remove(enhanced_path)
                except:
                    pass
            
            return ollama_results
            
        except Exception as e:
            print(f"Enhanced Ollama captcha solving failed: {e}")
            return []
    
    def solve_captcha_with_ocr_advanced(self, image_path):
        """Advanced OCR with multiple preprocessing strategies"""
        try:
            print("Solving 3-digit captcha with advanced OCR...")
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            height, width = image.shape
            scale_factor = max(150/height, 450/width)
            new_size = (int(width * scale_factor * 2.5), int(height * scale_factor * 2.5))
            image = cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)
            
            ocr_results = []
            strategies = []
            
            # Multiple CLAHE settings
            for clip_limit in [2.0, 3.0, 4.0, 5.0]:
                clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(4,4))
                clahe_enhanced = clahe.apply(image)
                _, thresh = cv2.threshold(clahe_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                strategies.append((f"clahe_{clip_limit}", thresh))
            
            # Enhanced OCR configurations
            configs = [
                r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',
                r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',
                r'--oem 1 --psm 8 -c tessedit_char_whitelist=0123456789',
                r'--psm 13 --oem 3 -c tessedit_char_whitelist=0123456789'
            ]
            
            for strategy_name, processed_image in strategies:
                for config_idx, config in enumerate(configs):
                    try:
                        pil_image = Image.fromarray(processed_image)
                        text = pytesseract.image_to_string(pil_image, config=config).strip()
                        numeric_text = ''.join(c for c in text if c.isdigit())
                        
                        if len(numeric_text) == 3:
                            ocr_results.append(numeric_text)
                            print(f"✓ Advanced OCR ({strategy_name}, config {config_idx+1}): {numeric_text}")
                        elif len(numeric_text) > 3:
                            truncated = numeric_text[:3]
                            ocr_results.append(truncated)
                            print(f"✓ Advanced OCR ({strategy_name}, config {config_idx+1}) truncated: {truncated}")
                            
                    except Exception as e:
                        continue
            
            return ocr_results
            
        except Exception as e:
            print(f"Advanced OCR failed: {e}")
            return []
    
    def calculate_weighted_consensus(self, all_attempts):
        """Enhanced consensus calculation with confidence weighting"""
        try:
            print(f"\n=== ENHANCED 3-DIGIT CONSENSUS CALCULATION ===")
            print(f"Total attempts collected: {len(all_attempts)}")
            
            if not all_attempts:
                return None
            
            valid_attempts = [attempt for attempt in all_attempts if len(attempt) == 3 and attempt.isdigit()]
            print(f"Valid 3-digit attempts: {valid_attempts}")
            
            if not valid_attempts:
                return None
            
            # Strategy 1: Weighted full consensus
            attempt_weights = {}
            for i, attempt in enumerate(valid_attempts):
                weight = 1.0 + (i * 0.1)
                attempt_weights[attempt] = attempt_weights.get(attempt, 0) + weight
            
            print(f"Weighted attempt scores: {attempt_weights}")
            
            if attempt_weights:
                best_weighted = max(attempt_weights.items(), key=lambda x: x[1])
                if best_weighted[1] > 1.5:
                    print(f"✓ Weighted consensus: {best_weighted[0]} (weight: {best_weighted[1]:.1f})")
                    return best_weighted[0]
            
            # Strategy 2: Position-wise consensus
            position_analysis = [[], [], []]
            
            for attempt in valid_attempts:
                for pos in range(3):
                    position_analysis[pos].append(attempt[pos])
            
            consensus_digits = []
            confidence_score = 0
            
            for pos in range(3):
                digit_counts = Counter(position_analysis[pos])
                most_common = digit_counts.most_common(1)[0]
                digit, count = most_common
                
                consensus_digits.append(digit)
                position_confidence = count / len(valid_attempts)
                confidence_score += position_confidence
                
                print(f"Position {pos+1}: {dict(digit_counts)} -> {digit} (confidence: {position_confidence:.2f})")
            
            average_confidence = confidence_score / 3
            position_consensus = ''.join(consensus_digits)
            
            print(f"✓ Position-wise consensus: {position_consensus} (avg confidence: {average_confidence:.2f})")
            
            if attempt_weights and best_weighted[1] > 1.5:
                return best_weighted[0]
            else:
                return position_consensus
            
        except Exception as e:
            print(f"Enhanced consensus calculation failed: {e}")
            return valid_attempts[0] if valid_attempts else None
    
    def solve_captcha_comprehensive_enhanced(self):
        """Comprehensive enhanced 3-digit captcha solving"""
        try:
            print(f"\n=== ENHANCED 3-DIGIT CAPTCHA SOLVING ===")
            
            captcha_img = self.driver.find_element(By.ID, "imgCaptcha")
            img_path = f"captcha_enhanced_{int(time.time())}.png"
            captcha_img.screenshot(img_path)
            print(f"Captured captcha: {img_path}")
            
            current_attempts = []
            
            # Enhanced Ollama results (multiple attempts)
            for attempt in range(2):
                ollama_results = self.solve_captcha_with_ollama_enhanced(img_path)
                current_attempts.extend(ollama_results)
                if ollama_results:
                    print(f"Ollama attempt {attempt+1}: {ollama_results}")
            
            # Enhanced OCR results
            ocr_results = self.solve_captcha_with_ocr_advanced(img_path)
            current_attempts.extend(ocr_results)
            if ocr_results:
                print(f"Advanced OCR results: {ocr_results}")
            
            print(f"Current round total results: {current_attempts}")
            
            self.captcha_attempts.extend(current_attempts)
            consensus_result = self.calculate_weighted_consensus(self.captcha_attempts)
            
            try:
                os.remove(img_path)
            except:
                pass
            
            return consensus_result
            
        except Exception as e:
            print(f"Enhanced captcha solving failed: {e}")
            return None
    
    @retry_on_failure(max_attempts=1, delay=1)
    def login(self):
        """Perform automated login with enhanced 3-digit captcha consensus strategy"""
        if not USERNAME or not PASSWORD:
            logger.error("Username or password not configured in .env file")
            raise LoginError("Username or password not configured in .env file")
        
        try:
            self.login_attempts += 1
            logger.info(f"Starting automated login process (attempt {self.login_attempts}/3)...")
            print(f"=== AUTOMATED LOGIN PROCESS (ATTEMPT {self.login_attempts}/3) ===")
            
            self.verify_config()
            
            if not self.is_session_valid():
                logger.error("Browser session lost")
                raise LoginError("Browser session disconnected")
            
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            print("✓ No iframes detected - accessing elements directly")
            
            # Fill username
            print("Entering username...")
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "txtUserid"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            print("✓ Username entered successfully")
            time.sleep(1)
            
            # Fill password
            print("Entering password...")
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "txtpassword"))
            )
            password_field.clear()
            password_field.send_keys(PASSWORD)
            print("✓ Password entered successfully")
            time.sleep(1)
            
            # Enhanced 3-digit captcha solving
            print("Solving 3-digit captcha with enhanced consensus strategy...")
            
            for captcha_guess in range(1, 4):
                print(f"\n--- ENHANCED CAPTCHA GUESS {captcha_guess}/3 ---")
                
                captcha_text = self.solve_captcha_comprehensive_enhanced()
                
                if not captcha_text:
                    print(f"Failed to solve captcha on guess {captcha_guess}")
                    if captcha_guess < 3:
                        try:
                            refresh_button = self.driver.find_element(By.ID, "txtRefreshCaptcha")
                            refresh_button.click()
                            time.sleep(2)
                            print("Refreshed captcha for next guess")
                        except:
                            print("Could not refresh captcha")
                    continue
                
                print(f"Entering enhanced consensus captcha: {captcha_text}")
                captcha_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "txtCaptcha"))
                )
                captcha_field.clear()
                captcha_field.send_keys(captcha_text)
                print("✓ Captcha entered successfully")
                time.sleep(1)
                
                print("Clicking login button...")
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnLogin"))
                )
            login_button.click()
                print("✓ Login button clicked")
                
                print("Waiting for login response...")
                time.sleep(5)
                
                current_url = self.driver.current_url.lower()
                page_source = self.driver.page_source.lower()
                
                success_indicators = [
                    "studenthomepage.aspx" in current_url,
                    "dashboard" in current_url,
                    "home" in current_url,
                    "welcome" in current_url,
                    "student" in current_url
                ]
                
                if any(success_indicators):
                    logger.info("✓ Automated login successful!")
                    print("✓ AUTOMATED LOGIN SUCCESSFUL!")
                    self.current_window = self.driver.current_window_handle
                    return True
                
                error_element = self.driver.find_elements(By.ID, "labelerror")
                if error_element and error_element[0].text.strip():
                    error_text = error_element[0].text.strip()
                    print(f"Login error: {error_text}")
                    
                    self.captcha_failure_analysis.append({
                        'attempt': captcha_text,
                        'error': error_text,
                        'guess_number': captcha_guess
                    })
                    
                    if "captcha" in error_text.lower():
                        print(f"Enhanced captcha {captcha_guess}/3 failed, trying next guess...")
                        if captcha_guess < 3:
                            try:
                                refresh_button = self.driver.find_element(By.ID, "txtRefreshCaptcha")
                                refresh_button.click()
                                time.sleep(2)
                            except:
                                pass
                        continue
                    else:
                        raise LoginError(f"Login failed: {error_text}")
            
            raise LoginError(f"All 3 enhanced captcha guesses failed for login attempt {self.login_attempts}")
                
        except Exception as e:
            logger.error(f"Enhanced login attempt {self.login_attempts} failed: {e}")
            raise LoginError(f"Login error: {e}")
    
    def navigate_to_gradesheet(self):
        """Navigate to grade sheet handling new tab opening"""
        try:
            print("Navigating to Academic Details...")
            logger.info("Navigating to Academic Details...")
            
            # Store current window handle
            self.current_window = self.driver.current_window_handle
            all_windows_before = self.driver.window_handles
            print(f"Current windows before navigation: {len(all_windows_before)}")
            
            # Wait for and click 'Academics Detail' - DISCOVERED ID: rtpchkMenu_lnkbtn2_1
            academic_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "rtpchkMenu_lnkbtn2_1"))
            )
            academic_link.click()
            print("✓ Clicked Academics Detail")
            time.sleep(3)

            print("Clicking Grade Sheet/Mark Sheet...")
            logger.info("Clicking Grade Sheet/Mark Sheet...")
            
            # Wait for and click 'Grade Sheet/Mark Sheet' link
            gradesheet_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Grade Sheet/Mark Sheet"))
            )
            gradesheet_link.click()
            print("✓ Clicked Grade Sheet/Mark Sheet")
            
            # Wait for new window/tab to open
            print("Waiting for new tab to open...")
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: len(driver.window_handles) > len(all_windows_before)
                )
                print("✓ New tab detected")
            except TimeoutException:
                print("No new tab detected, checking current page...")
                # Fallback: check if we're already on gradesheet page
                current_url = self.driver.current_url.lower()
                if "gradesheet.aspx" in current_url:
                    print("✓ Already on grade sheet page")
                    return True
                else:
                    raise Exception("Grade sheet did not open in new tab and current page is not gradesheet")
            
            # Switch to the new tab
            all_windows_after = self.driver.window_handles
            print(f"Windows after click: {len(all_windows_after)}")
            
            # Find the new window
            new_windows = [w for w in all_windows_after if w not in all_windows_before]
            if new_windows:
                self.gradesheet_window = new_windows[0]
                self.driver.switch_to.window(self.gradesheet_window)
                print(f"✓ Switched to new tab")
                
                # Wait for grade sheet to load
                print("Waiting for grade sheet page to load...")
                time.sleep(5)
                
                # Verify we're on the grade sheet page
                current_url = self.driver.current_url
                print(f"New tab URL: {current_url}")
                
                if "gradesheet.aspx" in current_url.lower():
                    print("✓ Successfully navigated to Grade Sheet page")
                    return True
                else:
                    print(f"Warning: Expected gradesheet.aspx but got: {current_url}")
                    # Continue anyway, might still have grade data
                return True
            else:
                raise Exception("Could not find new window after clicking Grade Sheet")
            
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            print(f"Error during navigation: {e}")
            
            # Debug: take screenshot and list all windows
            try:
                self.driver.save_screenshot("navigation_error_debug.png")
                print(f"Debug screenshot saved. Current windows: {self.driver.window_handles}")
                print(f"Current URL: {self.driver.current_url}")
            except:
                pass
            
            raise
    
    # COMPREHENSIVE CGPA EXTRACTION METHODS FOR NEW TAB
    def extract_cgpa_from_gradesheet_tab(self):
        """Extract CGPA from the grade sheet tab using multiple strategies"""
        try:
            print("Starting CGPA extraction from grade sheet tab...")
            
            # Take screenshot for debugging
            self.driver.save_screenshot("gradesheet_tab_debug.png")
            print("Debug screenshot saved: gradesheet_tab_debug.png")
            
            # Strategy 1: Direct element targeting
            cgpa = self.extract_cgpa_targeted()
            if cgpa:
                return cgpa
            
            # Strategy 2: Table-based extraction
            cgpa = self.extract_cgpa_from_table()
            if cgpa:
                return cgpa
            
            # Strategy 3: OCR on specific sections
            cgpa = self.extract_cgpa_focused_ocr()
            if cgpa:
                return cgpa
                
            # Strategy 4: Vision model extraction
            cgpa = self.extract_cgpa_with_vision()
            if cgpa:
                return cgpa
            
            # Strategy 5: Screenshot + LLM fallback
            print("All direct methods failed, using screenshot + LLM fallback...")
            cgpa = self.extract_cgpa_screenshot_llm_fallback()
            if cgpa:
                return cgpa
            
            print("All CGPA extraction strategies failed")
            return None
            
        except Exception as e:
            print(f"CGPA extraction from gradesheet tab failed: {e}")
            return None
    
    def extract_cgpa_targeted(self):
        """Target specific CGPA display elements"""
        try:
            print("Attempting targeted CGPA extraction...")
            
            # Enhanced search strategies for grade sheet page
            cgpa_strategies = [
                # Direct CGPA text search
                (By.XPATH, "//*[contains(text(), 'CGPA') or contains(text(), 'cgpa')]"),
                (By.XPATH, "//*[contains(text(), 'Cumulative') or contains(text(), 'cumulative')]"),
                (By.XPATH, "//*[contains(text(), 'Grade Point Average')]"),
                
                # Common grade sheet element patterns
                (By.XPATH, "//td[contains(text(), 'CGPA')]/following-sibling::td"),
                (By.XPATH, "//th[contains(text(), 'CGPA')]/following-sibling::th"),
                (By.XPATH, "//label[contains(text(), 'CGPA')]/following-sibling::*"),
                
                # Summary/total row patterns
                (By.XPATH, "//tr[contains(@class, 'total') or contains(@class, 'summary')]//td"),
                (By.XPATH, "//tr[last()]//td"),  # Often CGPA is in the last row
                (By.XPATH, "//tfoot//td"),  # Footer often contains totals
                
                # Generic patterns for grade sheets
                (By.XPATH, "//span[contains(text(), '.') and string-length(text()) < 10]"),
                (By.XPATH, "//div[contains(text(), '.') and string-length(text()) < 20]"),
                (By.XPATH, "//strong[contains(text(), '.')]"),
                (By.XPATH, "//b[contains(text(), '.')]")
            ]
            
            for strategy_name, locator_type, locator_value in [
                ("CGPA Text", By.XPATH, "//*[contains(text(), 'CGPA')]"),
                ("CGPA Cell Following", By.XPATH, "//td[contains(text(), 'CGPA')]/following-sibling::td"),
                ("Last Row Cells", By.XPATH, "//tr[last()]//td"),
                ("Summary Spans", By.XPATH, "//span[contains(text(), '.')]")
            ]:
                try:
                    elements = self.driver.find_elements(locator_type, locator_value)
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            # Look for CGPA values
                            cgpa_matches = re.findall(r'(\d+\.\d+)', text)
                            for match in cgpa_matches:
                                cgpa_value = float(match)
                                if 0.0 <= cgpa_value <= 10.0:
                                    # Validate by checking context
                                    text_lower = text.lower()
                                    element_context = f"{element.get_attribute('outerHTML')[:200]}"
                                    
                                    if any(keyword in text_lower for keyword in ['cgpa', 'cumulative', 'gpa', 'grade point']):
                                        print(f"✓ Targeted extraction found CGPA: {cgpa_value} using {strategy_name}")
                                        print(f"  Context: {text}")
                                        return cgpa_value
                                    elif any(keyword in element_context.lower() for keyword in ['cgpa', 'cumulative', 'total']):
                                        print(f"✓ Targeted extraction found CGPA: {cgpa_value} using {strategy_name} (context match)")
                                        print(f"  Context: {text}")
                                        return cgpa_value
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Targeted CGPA extraction failed: {e}")
            return None
    
    def extract_cgpa_from_table(self):
        """Extract CGPA from grade sheet tables"""
        try:
            print("Extracting CGPA from tables...")
            
            # Find all tables
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables on the grade sheet")
            
            for i, table in enumerate(tables):
                try:
                    table_text = table.text.lower()
                    
                    # Check if table contains grade-related content
                    if any(keyword in table_text for keyword in ['cgpa', 'gpa', 'cumulative', 'grade', 'total']):
                        print(f"Analyzing table {i+1} for CGPA...")
                        
                        # Get all cells
                        cells = table.find_elements(By.XPATH, ".//td | .//th")
                        
                        for j, cell in enumerate(cells):
                            cell_text = cell.text.strip()
                            if cell_text:
                                # Look for CGPA patterns
                                cgpa_matches = re.findall(r'(\d+\.\d+)', cell_text)
                                for match in cgpa_matches:
                                    cgpa_value = float(match)
                                    if 0.0 <= cgpa_value <= 10.0:
                                        # Check if this cell or nearby cells mention CGPA
                                        cell_context = cell_text.lower()
                                        
                                        # Check previous and next cells for context
                                        try:
                                            prev_cell = cells[j-1] if j > 0 else None
                                            next_cell = cells[j+1] if j < len(cells)-1 else None
                                            
                                            prev_text = prev_cell.text.lower() if prev_cell else ""
                                            next_text = next_cell.text.lower() if next_cell else ""
                                            
                                            context_text = f"{prev_text} {cell_context} {next_text}"
                                            
                                            if any(keyword in context_text for keyword in ['cgpa', 'cumulative', 'gpa', 'grade point']):
                                                print(f"✓ Table extraction found CGPA: {cgpa_value}")
                                                print(f"  Table: {i+1}, Cell: {j+1}")
                                                print(f"  Context: {context_text}")
                                                return cgpa_value
                                        except:
                                            pass
                                        
                                        # Also check if it's in a summary/total row
                                        row = cell.find_element(By.XPATH, "./ancestor::tr[1]")
                                        row_text = row.text.lower()
                                        if any(keyword in row_text for keyword in ['total', 'summary', 'overall', 'cgpa']):
                                            print(f"✓ Table extraction found CGPA in summary row: {cgpa_value}")
                                            return cgpa_value
                except Exception as e:
                    continue
            
            return None
                
        except Exception as e:
            print(f"Table CGPA extraction failed: {e}")
            return None
    
    def extract_cgpa_focused_ocr(self):
        """Use OCR on focused areas of the grade sheet"""
        try:
            print("Attempting focused OCR CGPA extraction...")
            
            # Try to screenshot the entire page first
            full_screenshot = "gradesheet_full_ocr.png"
            self.driver.save_screenshot(full_screenshot)
            
            # Use OCR on the full screenshot
            image = Image.open(full_screenshot)
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(2.0)
            
            # OCR with focus on CGPA
            text = pytesseract.image_to_string(
                enhanced,
                config=r'--oem 3 --psm 6'
            ).strip()
            
            print(f"OCR extracted text length: {len(text)} characters")
            
            # Look for CGPA patterns in the text
            cgpa_patterns = [
                r'CGPA[:\s]*(\d+\.\d+)',
                r'cgpa[:\s]*(\d+\.\d+)', 
                r'Cumulative[:\s]*Grade[:\s]*Point[:\s]*Average[:\s]*(\d+\.\d+)',
                r'Cumulative[:\s]*(\d+\.\d+)',
                r'Total[:\s]*CGPA[:\s]*(\d+\.\d+)'
            ]
            
            for pattern in cgpa_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        cgpa_value = float(match)
                        if 0.0 <= cgpa_value <= 10.0:
                            print(f"✓ Focused OCR found CGPA: {cgpa_value}")
                            return cgpa_value
                    except:
                        continue
            
            # Cleanup
            try:
                os.remove(full_screenshot)
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"Focused OCR extraction failed: {e}")
            return None
    
    def extract_cgpa_with_vision(self):
        """Use Ollama vision to identify CGPA in the grade sheet"""
        try:
            if not self.ollama_available:
                return None
            
            print("Attempting vision model CGPA extraction...")
                
            # Screenshot the grade sheet page
            self.driver.save_screenshot("gradesheet_vision.png")
            
            enhanced_prompts = [
                "Look at this grade sheet image. Find the CGPA (Cumulative Grade Point Average) value. It should be a decimal number between 0.0 and 10.0, like 8.74 or 9.25. Return only the CGPA number.",
                "This is a student grade sheet. Locate the Cumulative GPA or CGPA value displayed somewhere on this page. Return just the decimal number.",
                "Examine this academic grade sheet. Find the overall CGPA value which should be a number like 8.45 or 9.12. Give me only that number.",
                "Look for the total CGPA or cumulative grade point average in this grade sheet. Return only the numerical value.",
                "This grade sheet shows academic performance. Find the CGPA value and return only that decimal number."
            ]
            
            for i, prompt in enumerate(enhanced_prompts):
                try:
                    response = ollama.chat(
                        model=self.vision_model,
                        messages=[{
                            'role': 'user',
                            'content': prompt,
                            'images': ['gradesheet_vision.png']
                        }],
                        options={'temperature': 0.1}
                    )
                    
                    result = response['message']['content'].strip()
                    
                    # Extract decimal number from response
                    cgpa_matches = re.findall(r'(\d+\.\d+)', result)
                    for match in cgpa_matches:
                        cgpa_value = float(match)
                        if 0.0 <= cgpa_value <= 10.0:
                            print(f"✓ Vision model extracted CGPA: {cgpa_value}")
                            return cgpa_value
                            
                except Exception as e:
                    print(f"Vision prompt {i+1} failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"Vision CGPA extraction failed: {e}")
            return None
    
    def extract_cgpa_screenshot_llm_fallback(self):
        """Fallback method: Take screenshot and use LLM for CGPA extraction"""
        try:
            print("Using screenshot + LLM fallback method...")
            
            if not self.ollama_available:
                print("Ollama not available for LLM fallback")
                return None
            
            # Take a high-quality screenshot
            screenshot_path = "gradesheet_llm_fallback.png"
            self.driver.save_screenshot(screenshot_path)
            
            # Enhanced prompt for LLM fallback
            fallback_prompt = """You are looking at a student grade sheet from SLCM (Student Life Cycle Management) portal. 

This image contains academic performance data including subjects, grades, credits, and importantly, the CGPA (Cumulative Grade Point Average).

Your task is to find and extract ONLY the CGPA value from this grade sheet. The CGPA is typically:
- A decimal number between 0.0 and 10.0 (like 8.74, 9.25, 7.89, etc.)
- Labeled as "CGPA", "Cumulative GPA", "Cumulative Grade Point Average", or similar
- Usually displayed prominently in a summary section
- Often found at the bottom or in a totals row

Look carefully at the image and identify the CGPA value. Respond with ONLY the numerical CGPA value, nothing else. For example, if you see CGPA: 8.74, respond with just: 8.74"""
            
            try:
                response = ollama.chat(
                    model=self.vision_model,
                    messages=[{
                        'role': 'user',
                        'content': fallback_prompt,
                        'images': [screenshot_path]
                    }],
                    options={'temperature': 0.0}  # Most deterministic
                )
                
                result = response['message']['content'].strip()
                print(f"LLM fallback response: '{result}'")
                
                # Extract decimal number from response
                cgpa_match = re.search(r'(\d+\.\d+)', result)
                if cgpa_match:
                    cgpa_value = float(cgpa_match.group(1))
                    if 0.0 <= cgpa_value <= 10.0:
                        print(f"✓ LLM fallback extracted CGPA: {cgpa_value}")
                        return cgpa_value
                
                # If no decimal found, try to extract any number that could be CGPA
                number_matches = re.findall(r'(\d+\.?\d*)', result)
                for match in number_matches:
                    try:
                        value = float(match)
                        if 0.0 <= value <= 10.0 and '.' in match:  # Must be decimal
                            print(f"✓ LLM fallback extracted CGPA (alternative): {value}")
                            return value
                    except:
                        continue
                
                print("LLM fallback could not extract valid CGPA")
                return None
                
            except Exception as e:
                print(f"LLM fallback failed: {e}")
                return None
            
        except Exception as e:
            print(f"Screenshot + LLM fallback failed: {e}")
            return None
    
    def parse_cgpa_from_text(self, text):
        """Parse CGPA from extracted text using multiple patterns"""
        patterns = [
            r'CGPA[:\s]*(\d+\.\d+)',
            r'cgpa[:\s]*(\d+\.\d+)',
            r'Cumulative[:\s]*Grade[:\s]*Point[:\s]*Average[:\s]*(\d+\.\d+)',
            r'Cumulative[:\s]*(\d+\.\d+)',
            r'Overall[:\s]*(\d+\.\d+)',
            r'Grade[:\s]*Point[:\s]*Average[:\s]*(\d+\.\d+)',
            r'Total[:\s]*CGPA[:\s]*(\d+\.\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                cgpa = float(match.group(1))
                    if 0.0 <= cgpa <= 10.0:
                        logger.info(f"Successfully extracted CGPA: {cgpa}")
                    return cgpa
                except ValueError:
                    continue
        
        logger.warning("Could not find valid CGPA in extracted text")
        return None
    
    def run_scraper(self):
        """Main method to run the scraper with new tab handling"""
        try:
            print("[DEBUG] Starting enhanced scraper with new tab support...")
            logger.info("Starting Enhanced SLCM CGPA Scraper with New Tab Navigation...")
            
            # Navigate to login page
            print("[DEBUG] Navigating to login page...")
            self.driver.get(LOGIN_URL)
            print("[DEBUG] Reached login page")
            time.sleep(5)
            
            # Take screenshot for debugging
            self.driver.save_screenshot("login_page.png")
            print("[DEBUG] Saved screenshot of login page")
            
            # Try login up to 3 times
            login_successful = False
            
            while self.login_attempts < 3 and not login_successful:
                try:
                    print(f"\n[DEBUG] Attempting enhanced login {self.login_attempts + 1}/3...")
                    self.login()
                    login_successful = True
                    print("[DEBUG] Enhanced login successful!")
                    
                except LoginError as e:
                    print(f"[DEBUG] Enhanced login attempt {self.login_attempts} failed: {e}")
                    if self.login_attempts >= 3:
                        break
                    
                    # Reset captcha attempts for next login attempt
                    self.captcha_attempts = []
                    
                    # Navigate back to login page for next attempt
                    print("[DEBUG] Navigating back to login page for next attempt...")
                    self.driver.get(LOGIN_URL)
                    time.sleep(3)
            
            if not login_successful:
                print("[DEBUG] All enhanced login attempts failed, requesting manual login...")
                print("=== MANUAL LOGIN REQUIRED ===")
                print("All automatic login attempts have failed.")
                print("Please log in manually in the browser window.")
                input("Press Enter after you have logged in manually and reached the student homepage...")
                
                # Verify manual login
                current_url = self.driver.current_url.lower()
                if "studenthomepage.aspx" not in current_url:
                    raise LoginError("Manual login verification failed")
                    
                print("✓ Manual login verified successfully")
                self.current_window = self.driver.current_window_handle
            
            # Navigate to grade sheet (with new tab handling)
            print("[DEBUG] Navigating to grade sheet with new tab support...")
            self.navigate_to_gradesheet()
            
            # Extract CGPA from the new tab
            print("[DEBUG] Extracting CGPA from grade sheet tab...")
            cgpa = self.extract_cgpa_from_gradesheet_tab()
            
            if cgpa:
                print(f"[DEBUG] Successfully extracted CGPA: {cgpa}")
                return cgpa
            else:
                print("[DEBUG] Failed to extract CGPA with all methods")
                raise CGPAExtractionError("Failed to extract CGPA from grade sheet tab")
                
        except Exception as e:
            print(f"[DEBUG] Error in run_scraper: {str(e)}")
            logger.error(f"Scraper error: {e}")
            raise
        
        finally:
            if self.driver:
                try:
                    input("Press Enter to close the browser...")
                self.driver.quit()
                    print("[DEBUG] Driver cleanup completed")
                except Exception as cleanup_error:
                    print(f"[DEBUG] Driver cleanup error: {cleanup_error}")

# Main execution block
if __name__ == "__main__":
    scraper = None
    
    try:
        print("[DEBUG] Initializing enhanced scraper with new tab support...")
        scraper = SLCMScraper()
        print("[DEBUG] Running enhanced scraper...")
        result = scraper.run_scraper()
        print(f"[DEBUG] Enhanced scraper completed successfully. CGPA: {result}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")
        
    finally:
        if scraper and hasattr(scraper, 'driver') and scraper.driver:
            try:
                scraper.driver.quit()
                print("[DEBUG] Final driver cleanup completed")
            except Exception as cleanup_error:
                print(f"[DEBUG] Final cleanup error: {cleanup_error}")
