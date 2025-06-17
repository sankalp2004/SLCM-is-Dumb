# check.py - DOM State Monitoring and Navigation Diagnostics (Fixed JavaScript Errors)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DOMDiagnosticTool:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        self.initial_state = {}
        self.state_snapshots = []
        self.network_logs = []
        
    def setup_driver(self):
        """Setup Chrome driver with devtools enabled for network monitoring (Selenium 4.x compatible)"""
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Enable logging for Selenium 4.x
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set up service (Selenium 4.x pattern)
        chrome_driver_path = os.getenv('CHROME_DRIVER_PATH')
        
        try:
            if chrome_driver_path and os.path.exists(chrome_driver_path):
                service = Service(chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Let Selenium Manager handle driver automatically
                self.driver = webdriver.Chrome(options=chrome_options)
                
            print("Chrome driver setup successful")
            
        except Exception as e:
            print(f"Chrome driver setup failed: {e}")
            raise
        
    def inject_monitoring_scripts(self):
        """Inject JavaScript to monitor DOM changes and AJAX requests"""
        print("\n[INJECTING MONITORING SCRIPTS]")
        
        # DOM Mutation Observer
        mutation_script = """
        window.domChanges = [];
        
        // Create a MutationObserver to track DOM changes
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    // Track added nodes
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            window.domChanges.push({
                                type: 'added',
                                tagName: node.tagName,
                                id: node.id || null,
                                className: typeof node.className === 'string' ? node.className : null,
                                textContent: node.textContent ? node.textContent.substring(0, 50) : null,
                                timestamp: new Date().toISOString()
                            });
                        }
                    });
                    
                    // Track removed nodes
                    mutation.removedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            window.domChanges.push({
                                type: 'removed',
                                tagName: node.tagName,
                                id: node.id || null,
                                className: typeof node.className === 'string' ? node.className : null,
                                timestamp: new Date().toISOString()
                            });
                        }
                    });
                } else if (mutation.type === 'attributes') {
                    // Track attribute changes
                    window.domChanges.push({
                        type: 'attribute',
                        tagName: mutation.target.tagName,
                        id: mutation.target.id || null,
                        className: typeof mutation.target.className === 'string' ? mutation.target.className : null,
                        attributeName: mutation.attributeName,
                        timestamp: new Date().toISOString()
                    });
                }
            });
        });
        
        // Observe document body and all its descendants
        observer.observe(document.body, { 
            childList: true, 
            subtree: true, 
            attributes: true,
            attributeFilter: ['style', 'class', 'display', 'visibility']
        });
        
        // Function to get DOM changes and reset the log
        window.getDOMChanges = function() {
            const changes = window.domChanges;
            window.domChanges = [];
            return changes;
        };
        """
        
        # AJAX Request Monitor
        ajax_script = """
        window.ajaxRequests = [];
        
        // Monitor XMLHttpRequest
        const origOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function() {
            window.ajaxRequests.push({
                type: 'xhr',
                method: arguments[0],
                url: arguments[1],
                timestamp: new Date().toISOString()
            });
            return origOpen.apply(this, arguments);
        };
        
        // Monitor Fetch API
        const origFetch = window.fetch;
        window.fetch = function() {
            const url = arguments[0];
            const method = arguments[1] && arguments[1].method ? arguments[1].method : 'GET';
            window.ajaxRequests.push({
                type: 'fetch',
                method: method,
                url: typeof url === 'string' ? url : url.url,
                timestamp: new Date().toISOString()
            });
            return origFetch.apply(this, arguments);
        };
        
        // Function to get AJAX requests and reset the log
        window.getAJAXRequests = function() {
            const requests = window.ajaxRequests;
            window.ajaxRequests = [];
            return requests;
        };
        """
        
        # Fixed Visual state change monitor
        visual_script = """
        window.visibilityChanges = [];
        
        // Store initial visibility state of elements
        window.trackVisibilityChanges = function() {
            let allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                const wasVisible = style.display !== 'none' && style.visibility !== 'hidden';
                const rect = el.getBoundingClientRect();
                const hasSize = rect.width > 0 && rect.height > 0;
                
                // Store initial state in a custom attribute
                el._previousVisibility = wasVisible && hasSize;
                
                // Check if className is a string before calling includes
                if (typeof el.className === 'string' && (el.id || el.className.length > 0)) {
                    // If it's an interesting element, monitor it specifically
                    if ((el.id && el.id.includes('grade')) || 
                        el.className.includes('grade') || 
                        el.textContent.includes('CGPA') ||
                        el.textContent.includes('Grade') ||
                        el.textContent.includes('Mark')) {
                        
                        window.visibilityChanges.push({
                            tagName: el.tagName,
                            id: el.id || null,
                            className: el.className || null,
                            initialVisibility: wasVisible && hasSize,
                            timestamp: new Date().toISOString()
                        });
                    }
                }
            });
        };
        
        // Compare current visibility with previous state
        window.detectVisibilityChanges = function() {
            let changes = [];
            let allElements = document.querySelectorAll('*');
            
            allElements.forEach(el => {
                if (el._previousVisibility !== undefined) {
                    const style = window.getComputedStyle(el);
                    const isVisible = style.display !== 'none' && style.visibility !== 'hidden';
                    const rect = el.getBoundingClientRect();
                    const hasSize = rect.width > 0 && rect.height > 0;
                    const currentVisibility = isVisible && hasSize;
                    
                    // Detect changes
                    if (el._previousVisibility !== currentVisibility) {
                        changes.push({
                            tagName: el.tagName,
                            id: el.id || null,
                            className: typeof el.className === 'string' ? el.className : null,
                            previousVisibility: el._previousVisibility,
                            currentVisibility: currentVisibility,
                            timestamp: new Date().toISOString()
                        });
                        
                        // Update state
                        el._previousVisibility = currentVisibility;
                    }
                }
            });
            
            return changes;
        };
        
        // Call immediately to establish baseline
        window.trackVisibilityChanges();
        """
        
        # Enhanced Content inspection script with better error handling
        content_script = """
        window.findGradeSections = function() {
            const gradeRelatedContent = [];
            
            // Look for grade-related elements
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                try {
                    const text = el.textContent || '';
                    const id = el.id || '';
                    const className = typeof el.className === 'string' ? el.className : '';
                    
                    // Check for grade-related content
                    if (text.includes('CGPA') || 
                        text.includes('GPA') || 
                        text.includes('Grade') ||
                        text.includes('Mark Sheet') ||
                        text.includes('Semester') ||
                        id.toLowerCase().includes('grade') ||
                        id.toLowerCase().includes('cgpa') ||
                        className.toLowerCase().includes('grade') ||
                        className.toLowerCase().includes('cgpa')) {
                        
                        gradeRelatedContent.push({
                            tagName: el.tagName,
                            id: el.id || null,
                            className: className,
                            textPreview: text.substring(0, 100),
                            visible: el.offsetParent !== null,
                            timestamp: new Date().toISOString()
                        });
                    }
                } catch (error) {
                    // Skip elements that cause errors
                    console.log('Error processing element:', error);
                }
            });
            
            return gradeRelatedContent;
        };
        """
        
        # Inject all scripts with error handling
        try:
            self.driver.execute_script(mutation_script)
            print("✓ DOM mutation observer injected")
        except Exception as e:
            print(f"Failed to inject mutation script: {e}")
        
        try:
            self.driver.execute_script(ajax_script)
            print("✓ AJAX monitor injected")
        except Exception as e:
            print(f"Failed to inject AJAX script: {e}")
        
        try:
            self.driver.execute_script(visual_script)
            print("✓ Visual change monitor injected")
        except Exception as e:
            print(f"Failed to inject visual script: {e}")
        
        try:
            self.driver.execute_script(content_script)
            print("✓ Content inspector injected")
        except Exception as e:
            print(f"Failed to inject content script: {e}")
        
        print("✓ All monitoring scripts injection completed")
    
    def capture_dom_state(self, name="state"):
        """Capture the current state of the DOM"""
        try:
            # Get DOM changes
            dom_changes = self.driver.execute_script("return window.getDOMChanges ? window.getDOMChanges() : [];")
            
            # Get AJAX requests
            ajax_requests = self.driver.execute_script("return window.getAJAXRequests ? window.getAJAXRequests() : [];")
            
            # Get visibility changes
            visibility_changes = self.driver.execute_script("return window.detectVisibilityChanges ? window.detectVisibilityChanges() : [];")
            
            # Find grade-related content
            grade_content = self.driver.execute_script("return window.findGradeSections ? window.findGradeSections() : [];")
            
            # Capture current URL
            current_url = self.driver.current_url
            
            # Get browser console logs (simplified for Selenium 4.x)
            console_logs = []
            try:
                logs = self.driver.get_log('browser')
                console_logs = [{'level': log['level'], 'message': log['message']} for log in logs[-10:]]  # Last 10 logs
            except Exception as e:
                console_logs = [{'error': f'Could not get console logs: {e}'}]
            
            # Create state snapshot
            state = {
                'name': name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'url': current_url,
                'dom_changes': dom_changes,
                'ajax_requests': ajax_requests,
                'visibility_changes': visibility_changes,
                'grade_content': grade_content,
                'console_logs': console_logs
            }
            
            # Save state snapshot
            self.state_snapshots.append(state)
            print(f"✓ Captured DOM state: {name}")
            
            # Print summary of findings
            print(f"  - DOM changes: {len(dom_changes)}")
            print(f"  - AJAX requests: {len(ajax_requests)}")
            print(f"  - Visibility changes: {len(visibility_changes)}")
            print(f"  - Grade-related elements: {len(grade_content)}")
            
            # Return state
            return state
            
        except Exception as e:
            print(f"Error capturing DOM state: {e}")
            return None
    
    def analyze_changes(self, before_state, after_state):
        """Analyze changes between two states"""
        print("\n[ANALYZING CHANGES]")
        
        # Compare URLs
        if before_state['url'] != after_state['url']:
            print(f"URL changed: {before_state['url']} -> {after_state['url']}")
        else:
            print(f"URL remained same: {after_state['url']}")
        
        # Analyze new AJAX requests
        print("\nNew AJAX Requests:")
        if after_state['ajax_requests']:
            for req in after_state['ajax_requests']:
                print(f"  - {req['method']} {req['url']}")
        else:
            print("  - No AJAX requests detected")
        
        # Analyze visibility changes
        print("\nElement Visibility Changes:")
        if after_state['visibility_changes']:
            for change in after_state['visibility_changes']:
                visibility = "became visible" if change['currentVisibility'] else "became hidden"
                element_id = f"#{change['id']}" if change['id'] else ""
                element_class = f".{change['className'].replace(' ', '.')}" if change['className'] else ""
                print(f"  - {change['tagName']}{element_id}{element_class} {visibility}")
        else:
            print("  - No visibility changes detected")
        
        # Analyze newly available grade content
        print("\nGrade-Related Content:")
        if after_state['grade_content']:
            for content in after_state['grade_content']:
                visibility = "visible" if content['visible'] else "hidden"
                element_id = f"#{content['id']}" if content['id'] else ""
                element_class = f".{content['className'].replace(' ', '.')}" if content['className'] else ""
                print(f"  - {content['tagName']}{element_id}{element_class} ({visibility})")
                print(f"    Text: {content['textPreview']}")
        else:
            print("  - No grade-related content found")
    
    def run_diagnostics(self):
        """Run the diagnostic flow"""
        try:
            print("=" * 60)
            print("SLCM DOM DIAGNOSTIC TOOL (Fixed JavaScript Version)")
            print("=" * 60)
            
            # Navigate to login page
            self.driver.get("https://slcm.manipal.edu/")
            print("\nNavigated to SLCM login page. Please login manually.")
            
            input("\nPress Enter after logging in and reaching the student homepage...")
            print("✓ Login confirmed")
            
            # Inject monitoring scripts after login
            self.inject_monitoring_scripts()
            
            # Capture initial state
            initial_state = self.capture_dom_state("initial")
            
            print("\nPlease navigate to Academic Details. Click on the Academic Details link.")
            input("Press Enter after reaching the Academics page...")
            
            # Capture post-navigation state
            academics_state = self.capture_dom_state("academics")
            
            print("\n" + "=" * 60)
            print("GRADE SHEET NAVIGATION DIAGNOSTIC")
            print("=" * 60)
            print("\nINSTRUCTIONS:")
            print("1. When you click on Grade Sheet/Mark Sheet, pay attention to:")
            print("   - Does the page change or stay the same?")
            print("   - Do new sections appear within the same page?")
            print("   - Are there any popups, modals, or dropdowns?")
            print("   - Do you need to select a semester or year?")
            print("   - Does any content load dynamically?")
            print("   - Do you see your actual grades/CGPA anywhere?")
            
            print("\n2. Try clicking on 'Grade Sheet/Mark Sheet' now")
            input("   Press Enter IMMEDIATELY after clicking...")
            
            # Wait briefly to allow DOM changes to occur
            time.sleep(3)
            
            # Capture post-click state
            post_click_state = self.capture_dom_state("post_click")
            
            # Analyze changes
            self.analyze_changes(academics_state, post_click_state)
            
            print("\nWait for any content to load fully (10 seconds)...")
            time.sleep(10)
            
            # Capture fully loaded state
            loaded_state = self.capture_dom_state("loaded")
            
            # Analyze changes from post-click to fully loaded
            print("\n" + "=" * 40)
            print("FINAL LOAD STATE ANALYSIS")
            print("=" * 40)
            self.analyze_changes(post_click_state, loaded_state)
            
            # Enhanced element detection with better error handling
            print("\n[COMPREHENSIVE ELEMENT ANALYSIS]")
            
            # Look for select dropdowns
            try:
                selector_elements = self.driver.find_elements(By.XPATH, "//select | //input[@type='radio'] | //input[@type='checkbox']")
                if selector_elements:
                    print(f"Found {len(selector_elements)} potential selector elements:")
                    for i, elem in enumerate(selector_elements):
                        try:
                            elem_type = elem.tag_name
                            elem_id = elem.get_attribute('id') or 'no-id'
                            elem_name = elem.get_attribute('name') or 'no-name'
                            elem_visible = elem.is_displayed()
                            elem_text = elem.text[:30] if elem.text else 'no-text'
                            print(f"  {i+1}. {elem_type} (ID: {elem_id}, Name: {elem_name}, Visible: {elem_visible}, Text: '{elem_text}')")
                        except:
                            print(f"  {i+1}. Error reading selector element")
                else:
                    print("No obvious selector elements found")
            except Exception as e:
                print(f"Error searching for selector elements: {e}")
            
            # Look for buttons and clickable elements with enhanced detection
            try:
                button_selectors = [
                    "//button",
                    "//input[@type='button']",
                    "//input[@type='submit']", 
                    "//a[contains(@class, 'btn')]",
                    "//*[@onclick]",
                    "//a[contains(@href, 'grade') or contains(@href, 'Grade')]",
                    "//*[contains(text(), 'View') or contains(text(), 'Show') or contains(text(), 'Display')]"
                ]
                
                all_clickable = []
                for selector in button_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        all_clickable.extend(elements)
                    except:
                        continue
                
                # Remove duplicates
                unique_clickable = []
                seen = set()
                for elem in all_clickable:
                    try:
                        elem_id = elem.get_attribute('id') or ''
                        elem_xpath = self.driver.execute_script("return arguments[0].tagName + (arguments[0].id ? '#' + arguments[0].id : '') + (arguments[0].className ? '.' + arguments[0].className.replace(/ /g, '.') : '');", elem)
                        if elem_xpath not in seen:
                            seen.add(elem_xpath)
                            unique_clickable.append(elem)
                    except:
                        continue
                
                if unique_clickable:
                    print(f"\nFound {len(unique_clickable)} potential clickable elements:")
                    for i, elem in enumerate(unique_clickable[:15]):  # Show first 15
                        try:
                            elem_type = elem.tag_name
                            elem_id = elem.get_attribute('id') or 'no-id'
                            elem_text = elem.text or elem.get_attribute('value') or 'no-text'
                            elem_visible = elem.is_displayed()
                            elem_href = elem.get_attribute('href') or ''
                            elem_onclick = elem.get_attribute('onclick') or ''
                            
                            print(f"  {i+1}. {elem_type} (ID: {elem_id}, Visible: {elem_visible})")
                            print(f"      Text: '{elem_text[:40]}...'")
                            if elem_href:
                                print(f"      Href: {elem_href[:50]}...")
                            if elem_onclick:
                                print(f"      OnClick: {elem_onclick[:50]}...")
                        except:
                            print(f"  {i+1}. Error reading clickable element")
                else:
                    print("\nNo obvious clickable elements found")
            except Exception as e:
                print(f"Error searching for clickable elements: {e}")
            
            # Enhanced grade content detection
            print("\n[ENHANCED GRADE CONTENT SEARCH]")
            try:
                grade_selectors = [
                    "//*[contains(text(), 'CGPA')]",
                    "//*[contains(text(), 'GPA')]", 
                    "//*[contains(text(), 'Grade')]",
                    "//*[contains(text(), 'Mark')]",
                    "//*[contains(@id, 'grade')]",
                    "//*[contains(@id, 'cgpa')]",
                    "//*[contains(@class, 'grade')]",
                    "//*[contains(@class, 'cgpa')]",
                    "//table[contains(@id, 'grade') or contains(@class, 'grade')]",
                    "//*[contains(text(), 'Semester')]",
                    "//*[contains(text(), 'Academic')]"
                ]
                
                all_grade_elements = []
                for selector in grade_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        all_grade_elements.extend(elements)
                    except:
                        continue
                
                # Remove duplicates and analyze
                unique_grade_elements = []
                seen_elements = set()
                for elem in all_grade_elements:
                    try:
                        elem_hash = f"{elem.tag_name}_{elem.get_attribute('id')}_{elem.text[:20] if elem.text else ''}"
                        if elem_hash not in seen_elements:
                            seen_elements.add(elem_hash)
                            unique_grade_elements.append(elem)
                    except:
                        continue
                
                if unique_grade_elements:
                    print(f"Found {len(unique_grade_elements)} grade-related elements:")
                    for i, elem in enumerate(unique_grade_elements[:20]):  # Show first 20
                        try:
                            elem_type = elem.tag_name
                            elem_id = elem.get_attribute('id') or 'no-id'
                            elem_text = elem.text[:80] if elem.text else 'no-text'
                            elem_visible = elem.is_displayed()
                            elem_style = elem.get_attribute('style') or ''
                            elem_class = elem.get_attribute('class') or ''
                            
                            print(f"  {i+1}. {elem_type} (ID: {elem_id}, Visible: {elem_visible})")
                            print(f"      Text: '{elem_text}...'")
                            if elem_class:
                                print(f"      Class: {elem_class[:50]}...")
                            if 'display' in elem_style or 'visibility' in elem_style:
                                print(f"      Style: {elem_style[:50]}...")
                        except:
                            print(f"  {i+1}. Error reading grade element")
                else:
                    print("No grade-related elements found")
            except Exception as e:
                print(f"Error searching for grade elements: {e}")
            
            # Save all state snapshots
            try:
                with open("dom_diagnostic_results.json", "w") as f:
                    json.dump(self.state_snapshots, f, indent=2)
                print("\n✓ Detailed results saved to dom_diagnostic_results.json")
            except Exception as e:
                print(f"\nError saving results: {e}")
            
            print("\n" + "=" * 60)
            print("DIAGNOSTIC COMPLETE")
            print("=" * 60)
            
            print("\nBased on what you observed:")
            print("1. Did any new content appear after clicking Grade Sheet?")
            print("2. Did you see any dropdown menus for semester/year selection?")
            print("3. Are there any tabs or accordion sections that opened?")
            print("4. Do you see your actual grades/CGPA anywhere on the current page?")
            print("5. Are there any additional buttons that became visible?")
            
            input("\nPress Enter when ready to close the browser...")
            
        except Exception as e:
            print(f"Diagnostic error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    tool = DOMDiagnosticTool()
    tool.run_diagnostics()
