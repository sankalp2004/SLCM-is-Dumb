# element_discovery.py - CGPA-Only Element Discovery
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def discover_cgpa_elements_only():
    """Focused CGPA element discovery for SLCM grade sheet"""
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-notifications')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("=" * 60)
        print("SLCM CGPA-ONLY ELEMENT DISCOVERY")
        print("=" * 60)
        print("\nThis script focuses ONLY on finding CGPA elements.")
        print("Please navigate to the Grade Sheet page manually and then run discovery.")
        print("\nSteps:")
        print("1. Log in manually")
        print("2. Navigate to Academic Details")
        print("3. Click on Grade Sheet/Mark Sheet")
        print("4. When you see the grade sheet with CGPA, press Enter")
        
        # Navigate to login page
        driver.get("https://slcm.manipal.edu/")
        
        # Wait for manual navigation to grade sheet
        input("\nPress Enter when you're on the Grade Sheet page with CGPA visible...")
        
        # Take screenshot for reference
        driver.save_screenshot("cgpa_discovery_page.png")
        print("Screenshot saved: cgpa_discovery_page.png")
        
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        # Run comprehensive CGPA discovery
        discover_cgpa_comprehensive(driver)
        
        print("\n" + "=" * 60)
        print("CGPA DISCOVERY COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error during CGPA discovery: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            input("\nPress Enter to close the browser...")
            driver.quit()
        except:
            pass

def discover_cgpa_comprehensive(driver):
    """Comprehensive CGPA element discovery strategies"""
    try:
        print("\n" + "=" * 50)
        print("COMPREHENSIVE CGPA ELEMENT DISCOVERY")
        print("=" * 50)
        
        # Strategy 1: Direct CGPA text search
        print("\n--- 1. DIRECT CGPA TEXT SEARCH ---")
        cgpa_text_strategies = [
            ("CGPA Upper", By.XPATH, "//*[contains(text(), 'CGPA')]"),
            ("CGPA Lower", By.XPATH, "//*[contains(text(), 'cgpa')]"),
            ("Cumulative Upper", By.XPATH, "//*[contains(text(), 'Cumulative')]"),
            ("Cumulative Lower", By.XPATH, "//*[contains(text(), 'cumulative')]"),
            ("Grade Point Average", By.XPATH, "//*[contains(text(), 'Grade Point Average')]"),
            ("GPA", By.XPATH, "//*[contains(text(), 'GPA')]")
        ]
        
        cgpa_text_elements = []
        for strategy_name, locator_type, locator_value in cgpa_text_strategies:
            try:
                elements = driver.find_elements(locator_type, locator_value)
                if elements:
                    print(f"\n{strategy_name}: Found {len(elements)} elements")
                    for i, element in enumerate(elements):
                        text = element.text.strip()
                        element_id = element.get_attribute('id')
                        element_class = element.get_attribute('class')
                        parent_text = ""
                        
                        try:
                            parent = element.find_element(By.XPATH, '..')
                            parent_text = parent.text.strip()
                        except:
                            pass
                        
                        print(f"  Element {i+1}:")
                        print(f"    Text: '{text}'")
                        print(f"    Tag: {element.tag_name}")
                        print(f"    ID: '{element_id}'")
                        print(f"    Class: '{element_class}'")
                        
                        # Look for CGPA values in the element or parent
                        combined_text = f"{text} {parent_text}"
                        cgpa_values = re.findall(r'\b(\d{1,2}\.\d{1,2})\b', combined_text)
                        for value in cgpa_values:
                            if 0.0 <= float(value) <= 10.0:
                                print(f"    *** CGPA VALUE FOUND: {value} ***")
                                print(f"    Parent Text: '{parent_text[:100]}...'")
                        
                        cgpa_text_elements.append({
                            'element': element,
                            'strategy': strategy_name,
                            'text': text,
                            'id': element_id,
                            'class': element_class
                        })
            except Exception as e:
                print(f"{strategy_name} search failed: {e}")
        
        # Strategy 2: Numeric pattern search in CGPA range
        print("\n--- 2. NUMERIC PATTERN SEARCH (CGPA RANGE) ---")
        all_elements = driver.find_elements(By.XPATH, "//*[text()]")
        cgpa_numeric_candidates = []
        
        cgpa_pattern = r'\b(\d{1,2}\.\d{1,2})\b'  # Matches patterns like 8.74, 9.25
        
        for element in all_elements:
            try:
                text = element.text.strip()
                if text:
                    matches = re.findall(cgpa_pattern, text)
                    for match in matches:
                        value = float(match)
                        if 0.0 <= value <= 10.0:  # CGPA range
                            cgpa_numeric_candidates.append({
                                'value': match,
                                'full_text': text,
                                'element': element,
                                'tag': element.tag_name,
                                'id': element.get_attribute('id'),
                                'class': element.get_attribute('class')
                            })
            except:
                continue
        
        print(f"Found {len(cgpa_numeric_candidates)} elements with CGPA-range values:")
        for i, candidate in enumerate(cgpa_numeric_candidates):
            print(f"\n  Candidate {i+1}: {candidate['value']}")
            print(f"    Full Text: '{candidate['full_text']}'")
            print(f"    Element: {candidate['tag']}")
            print(f"    ID: '{candidate['id']}'")
            print(f"    Class: '{candidate['class']}'")
            
            # Check if this looks like a CGPA summary
            text_lower = candidate['full_text'].lower()
            if any(keyword in text_lower for keyword in ['cgpa', 'cumulative', 'gpa', 'total', 'overall']):
                print(f"    *** LIKELY CGPA ELEMENT ***")
        
        # Strategy 3: Summary section targeting
        print("\n--- 3. SUMMARY/HEADER SECTION ANALYSIS ---")
        summary_strategies = [
            ("Class Summary", By.XPATH, "//*[contains(@class, 'summary')]"),
            ("Class Header", By.XPATH, "//*[contains(@class, 'header')]"),
            ("Class Info", By.XPATH, "//*[contains(@class, 'info')]"),
            ("Class Stats", By.XPATH, "//*[contains(@class, 'stats')]"),
            ("Class Total", By.XPATH, "//*[contains(@class, 'total')]"),
            ("ID Summary", By.XPATH, "//*[contains(@id, 'summary')]"),
            ("ID Header", By.XPATH, "//*[contains(@id, 'header')]"),
            ("ID Total", By.XPATH, "//*[contains(@id, 'total')]"),
            ("ID CGPA", By.XPATH, "//*[contains(@id, 'cgpa') or contains(@id, 'CGPA')]")
        ]
        
        for strategy_name, locator_type, locator_value in summary_strategies:
            try:
                elements = driver.find_elements(locator_type, locator_value)
                if elements:
                    print(f"\n{strategy_name}: Found {len(elements)} elements")
                    for i, element in enumerate(elements):
                        text = element.text.strip()
                        if text and re.search(r'\d+\.\d+', text):
                            print(f"  Element {i+1}:")
                            print(f"    ID: '{element.get_attribute('id')}'")
                            print(f"    Class: '{element.get_attribute('class')}'")
                            print(f"    Text: '{text[:150]}...'")
                            
                            # Extract CGPA values
                            cgpa_values = re.findall(r'\d+\.\d+', text)
                            for value in cgpa_values:
                                if 0.0 <= float(value) <= 10.0:
                                    print(f"    *** CGPA VALUE: {value} ***")
            except Exception as e:
                print(f"{strategy_name} failed: {e}")
        
        # Strategy 4: XPath relationship targeting
        print("\n--- 4. XPATH RELATIONSHIP TARGETING ---")
        xpath_strategies = [
            ("CGPA Following Sibling", "//*[contains(text(), 'CGPA')]/following-sibling::*"),
            ("CGPA Parent Children", "//*[contains(text(), 'CGPA')]/parent::*//*"),
            ("CGPA Same Element", "//*[contains(text(), 'CGPA') and contains(text(), '.')]"),
            ("Decimal After CGPA", "//*[contains(text(), 'CGPA')]/following::*[contains(text(), '.')]"),
            ("CGPA Preceding Text", "//*[contains(text(), '.')]/preceding::*[contains(text(), 'CGPA')]")
        ]
        
        for strategy_name, xpath_expr in xpath_strategies:
            try:
                elements = driver.find_elements(By.XPATH, xpath_expr)
                if elements:
                    print(f"\n{strategy_name}: Found {len(elements)} elements")
                    for i, element in enumerate(elements[:3]):  # Show first 3
                        text = element.text.strip()
                        if text and re.search(r'\d+\.\d+', text):
                            print(f"  Element {i+1}:")
                            print(f"    Tag: {element.tag_name}")
                            print(f"    ID: '{element.get_attribute('id')}'")
                            print(f"    Class: '{element.get_attribute('class')}'")
                            print(f"    Text: '{text}'")
                            
                            cgpa_values = re.findall(r'\d+\.\d+', text)
                            for value in cgpa_values:
                                if 0.0 <= float(value) <= 10.0:
                                    print(f"    *** CGPA CANDIDATE: {value} ***")
            except Exception as e:
                print(f"{strategy_name} failed: {e}")
        
        # Strategy 5: Table cell analysis for CGPA
        print("\n--- 5. TABLE CELL CGPA ANALYSIS ---")
        tables = driver.find_elements(By.TAG_NAME, 'table')
        print(f"Analyzing {len(tables)} tables for CGPA values...")
        
        for table_idx, table in enumerate(tables):
            try:
                table_text = table.text.lower()
                if 'cgpa' in table_text or 'cumulative' in table_text:
                    print(f"\nTable {table_idx + 1} contains CGPA-related text:")
                    print(f"  ID: '{table.get_attribute('id')}'")
                    print(f"  Class: '{table.get_attribute('class')}'")
                    
                    # Check all cells for CGPA values
                    cells = table.find_elements(By.XPATH, ".//td | .//th")
                    for cell_idx, cell in enumerate(cells):
                        cell_text = cell.text.strip()
                        if cell_text and re.search(r'\d+\.\d+', cell_text):
                            cgpa_values = re.findall(r'\d+\.\d+', cell_text)
                            for value in cgpa_values:
                                if 0.0 <= float(value) <= 10.0:
                                    print(f"    Cell {cell_idx + 1}: '{cell_text}'")
                                    print(f"    *** TABLE CGPA VALUE: {value} ***")
                                    print(f"    Cell ID: '{cell.get_attribute('id')}'")
                                    print(f"    Cell Class: '{cell.get_attribute('class')}'")
            except Exception as e:
                print(f"Error analyzing table {table_idx + 1}: {e}")
        
        # Strategy 6: Specific CGPA element patterns
        print("\n--- 6. SPECIFIC CGPA ELEMENT PATTERNS ---")
        specific_patterns = [
            ("CGPA Span", By.XPATH, "//span[contains(text(), 'CGPA') or contains(text(), '.')]"),
            ("CGPA Div", By.XPATH, "//div[contains(text(), 'CGPA') or contains(text(), '.')]"),
            ("CGPA TD", By.XPATH, "//td[contains(text(), 'CGPA') or contains(text(), '.')]"),
            ("CGPA Strong", By.XPATH, "//strong[contains(text(), 'CGPA') or contains(text(), '.')]"),
            ("CGPA Label", By.XPATH, "//label[contains(text(), 'CGPA') or contains(text(), '.')]"),
            ("Data Attributes", By.XPATH, "//*[@data-cgpa or @data-gpa]"),
            ("Value Attributes", By.XPATH, "//*[@value and contains(@value, '.')]")
        ]
        
        for strategy_name, locator_type, locator_value in specific_patterns:
            try:
                elements = driver.find_elements(locator_type, locator_value)
                if elements:
                    print(f"\n{strategy_name}: Found {len(elements)} elements")
                    for i, element in enumerate(elements):
                        text = element.text.strip()
                        value_attr = element.get_attribute('value')
                        
                        # Check text content
                        if text and re.search(r'\d+\.\d+', text):
                            cgpa_values = re.findall(r'\d+\.\d+', text)
                            for value in cgpa_values:
                                if 0.0 <= float(value) <= 10.0:
                                    print(f"  Element {i+1} (text): {value}")
                                    print(f"    ID: '{element.get_attribute('id')}'")
                                    print(f"    Class: '{element.get_attribute('class')}'")
                                    print(f"    *** PATTERN CGPA: {value} ***")
                        
                        # Check value attribute
                        if value_attr and re.search(r'\d+\.\d+', value_attr):
                            cgpa_values = re.findall(r'\d+\.\d+', value_attr)
                            for value in cgpa_values:
                                if 0.0 <= float(value) <= 10.0:
                                    print(f"  Element {i+1} (value attr): {value}")
                                    print(f"    ID: '{element.get_attribute('id')}'")
                                    print(f"    *** ATTRIBUTE CGPA: {value} ***")
            except Exception as e:
                print(f"{strategy_name} failed: {e}")
        
        # Strategy 7: JavaScript variable analysis
        print("\n--- 7. JAVASCRIPT VARIABLE ANALYSIS ---")
        try:
            # Execute JavaScript to find CGPA in page variables
            js_script = """
            var cgpaValues = [];
            
            // Check window variables
            for (var key in window) {
                if (typeof window[key] === 'string' || typeof window[key] === 'number') {
                    var value = window[key].toString();
                    if (/\\b\\d{1,2}\\.\\d{1,2}\\b/.test(value)) {
                        var matches = value.match(/\\b\\d{1,2}\\.\\d{1,2}\\b/g);
                        if (matches) {
                            matches.forEach(function(match) {
                                var num = parseFloat(match);
                                if (num >= 0.0 && num <= 10.0) {
                                    cgpaValues.push({key: key, value: match});
                                }
                            });
                        }
                    }
                }
            }
            
            return cgpaValues;
            """
            
            js_results = driver.execute_script(js_script)
            if js_results:
                print(f"Found {len(js_results)} JavaScript variables with CGPA-like values:")
                for result in js_results:
                    print(f"  Variable '{result['key']}': {result['value']}")
                    print(f"    *** JS CGPA CANDIDATE: {result['value']} ***")
        except Exception as e:
            print(f"JavaScript analysis failed: {e}")
        
        print("\n" + "=" * 50)
        print("CGPA DISCOVERY SUMMARY")
        print("=" * 50)
        print("\nLook for elements marked with:")
        print("  *** CGPA VALUE FOUND ***")
        print("  *** LIKELY CGPA ELEMENT ***") 
        print("  *** CGPA CANDIDATE ***")
        print("  *** PATTERN CGPA ***")
        print("  *** TABLE CGPA VALUE ***")
        print("\nThese indicate the most probable locations of your CGPA value.")
        
    except Exception as e:
        print(f"Comprehensive CGPA discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    discover_cgpa_elements_only()
