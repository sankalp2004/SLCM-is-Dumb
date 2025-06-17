from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

def discover_all_elements():
    """Comprehensive element discovery script for SLCM login page - FIXED VERSION"""
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to your SLCM login page
        driver.get("https://slcm.manipal.edu/")  # Replace with actual SLCM URL
        time.sleep(5)  # Wait for page to load
        
        print("=" * 60)
        print("SLCM LOGIN PAGE ELEMENT DISCOVERY - FIXED")
        print("=" * 60)
        
        # 1. Find all elements with IDs - FIXED
        print("\n1. ALL ELEMENTS WITH IDs:")
        print("-" * 30)
        elements_with_ids = driver.find_elements(By.XPATH, '//*[@id]')  # Removed [8]
        print(f"Found {len(elements_with_ids)} elements with IDs")
        for i, element in enumerate(elements_with_ids):
            try:
                tag = element.tag_name
                element_id = element.get_attribute('id')
                element_name = element.get_attribute('name') or 'None'
                element_type = element.get_attribute('type') or 'None'
                element_class = element.get_attribute('class') or 'None'
                print(f"{i+1}. Tag: {tag}, ID: {element_id}, Name: {element_name}, Type: {element_type}")
            except Exception as e:
                print(f"{i+1}. Error reading element: {e}")
        
        # 2. Find all input elements - FIXED
        print("\n2. ALL INPUT ELEMENTS:")
        print("-" * 25)
        input_elements = driver.find_elements(By.TAG_NAME, 'input')  # Removed [8]
        print(f"Found {len(input_elements)} input elements")
        for i, input_elem in enumerate(input_elements):
            try:
                input_id = input_elem.get_attribute('id') or 'None'
                input_name = input_elem.get_attribute('name') or 'None'
                input_type = input_elem.get_attribute('type') or 'None'
                input_placeholder = input_elem.get_attribute('placeholder') or 'None'
                input_value = input_elem.get_attribute('value') or 'None'
                print(f"Input {i+1}: ID='{input_id}', Name='{input_name}', Type='{input_type}', Placeholder='{input_placeholder}'")
            except Exception as e:
                print(f"Input {i+1}: Error reading element: {e}")
        
        # 3. Find all button elements - FIXED
        print("\n3. ALL BUTTON ELEMENTS:")
        print("-" * 25)
        button_elements = driver.find_elements(By.TAG_NAME, 'button')  # Removed [12]
        submit_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"]')
        all_buttons = button_elements + submit_inputs
        print(f"Found {len(all_buttons)} button/submit elements")
        for i, button in enumerate(all_buttons):
            try:
                button_id = button.get_attribute('id') or 'None'
                button_name = button.get_attribute('name') or 'None'
                button_type = button.get_attribute('type') or 'None'
                button_text = button.text or button.get_attribute('value') or 'None'
                button_class = button.get_attribute('class') or 'None'
                print(f"Button {i+1}: ID='{button_id}', Name='{button_name}', Type='{button_type}', Text='{button_text}'")
            except Exception as e:
                print(f"Button {i+1}: Error reading element: {e}")
        
        # 4. Find all image elements - FIXED
        print("\n4. ALL IMAGE ELEMENTS:")
        print("-" * 22)
        image_elements = driver.find_elements(By.TAG_NAME, 'img')  # Removed [13]
        print(f"Found {len(image_elements)} image elements")
        for i, img in enumerate(image_elements):
            try:
                img_id = img.get_attribute('id') or 'None'
                img_src = img.get_attribute('src') or 'None'
                img_alt = img.get_attribute('alt') or 'None'
                img_class = img.get_attribute('class') or 'None'
                # Truncate long src URLs
                display_src = img_src[:50] + '...' if img_src and len(img_src) > 50 else img_src
                print(f"Image {i+1}: ID='{img_id}', Src='{display_src}', Alt='{img_alt}'")
            except Exception as e:
                print(f"Image {i+1}: Error reading element: {e}")
        
        # 5. TARGET LOGIN ELEMENTS
        print("\n5. TARGET LOGIN ELEMENTS:")
        print("-" * 29)
        
        # Look for specific login elements
        login_targets = {
            'Username Field': ['txtUserId', 'txtUserid', 'username'],
            'Password Field': ['txtpassword', 'txtPassword', 'password'],
            'Captcha Field': ['txtCaptcha', 'captcha'],
            'Login Button': ['btnLogin', 'login'],
            'Captcha Image': ['imgCaptcha', 'captchaImage']
        }
        
        for target_name, possible_ids in login_targets.items():
            print(f"\n{target_name}:")
            found = False
            for possible_id in possible_ids:
                try:
                    element = driver.find_element(By.ID, possible_id)
                    print(f"  ✓ FOUND: ID='{possible_id}'")
                    print(f"    Tag: {element.tag_name}")
                    print(f"    Name: {element.get_attribute('name')}")
                    print(f"    Type: {element.get_attribute('type')}")
                    print(f"    Class: {element.get_attribute('class')}")
                    found = True
                    break
                except:
                    continue
            
            if not found:
                print(f"  ✗ NOT FOUND with any common ID")
        
        # 6. Check for iframes - FIXED
        print("\n6. IFRAME DETECTION:")
        print("-" * 20)
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')  # Removed [8]
        print(f"Total iframes found: {len(iframes)}")
        for i, iframe in enumerate(iframes):
            try:
                iframe_id = iframe.get_attribute('id') or 'None'
                iframe_name = iframe.get_attribute('name') or 'None'
                iframe_src = iframe.get_attribute('src') or 'None'
                print(f"Iframe {i+1}: ID='{iframe_id}', Name='{iframe_name}', Src='{iframe_src}'")
            except Exception as e:
                print(f"Iframe {i+1}: Error reading iframe: {e}")
    except Exception as e:
        print(f"Error in main try block: {e}")
