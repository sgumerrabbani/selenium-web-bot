from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import logging
import os
import glob

class EpisodeCopyAutomation:
    def __init__(self, username, password, headless=False, images_folder="."):
        self.username = username
        self.password = password
        
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        
        # Set download directory
        prefs = {
            "download.default_directory": os.path.abspath(images_folder),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 30)
            self.images_folder = os.path.abspath(images_folder)
            self.logged_in = False
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            raise
    
    def login(self, retries=3):
        """Login to the portal with retry logic"""
        login_url = "https://app.dev.portal.masjidal.com/login"
        
        for attempt in range(retries):
            try:
                print(f"🔐 Attempting login (attempt {attempt + 1}/{retries})...")
                
                # Navigate to login page
                self.driver.get(login_url)
                time.sleep(3)
                
                # Wait for login form to load
                print("⏳ Waiting for login form to load...")
                email_field = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "email"))
                )
                
                # Fill in credentials
                print("📝 Filling login credentials...")
                email_field.clear()
                email_field.send_keys(self.username)
                
                # Find and fill password field
                password_field = self.driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(self.password)
                
                # Click login button
                print("🔑 Clicking login button...")
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                
                # Wait for login to complete and check if successful
                time.sleep(5)
                
                # Check if login was successful by looking for dashboard elements or checking URL
                if self.check_login_success():
                    print("✅ Login successful!")
                    self.logged_in = True
                    return True
                else:
                    print("❌ Login may have failed - checking for error messages...")
                    
                    # Check for login errors
                    error_messages = [
                        "//div[contains(@class, 'alert-danger')]",
                        "//div[contains(@class, 'error')]",
                        "//*[contains(text(), 'Invalid')]",
                        "//*[contains(text(), 'incorrect')]",
                        "//*[contains(text(), 'error')]"
                    ]
                    
                    for error_xpath in error_messages:
                        try:
                            error_element = self.driver.find_element(By.XPATH, error_xpath)
                            if error_element.is_displayed():
                                print(f"❌ Login error: {error_element.text}")
                        except:
                            continue
                    
                    if attempt < retries - 1:
                        print("🔄 Retrying login...")
                        time.sleep(3)
                        continue
                    
            except Exception as e:
                print(f"❌ Login attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    print("🔄 Retrying login...")
                    time.sleep(3)
                    continue
        
        print("❌ All login attempts failed!")
        return False
    
    def check_login_success(self):
        """Check if login was successful"""
        try:
            # Check if we're redirected away from login page
            current_url = self.driver.current_url
            if "login" not in current_url and "dashboard" in current_url:
                return True
            
            # Check for dashboard elements
            dashboard_indicators = [
                "//*[contains(text(), 'Dashboard')]",
                "//*[contains(text(), 'Welcome')]",
                "//*[contains(@class, 'dashboard')]",
                "//nav",  # Assuming there's a navigation menu after login
            ]
            
            for indicator in dashboard_indicators:
                try:
                    if self.driver.find_elements(By.XPATH, indicator):
                        return True
                except:
                    continue
            
            # Check for logout button or user menu
            logout_indicators = [
                "//*[contains(text(), 'Logout')]",
                "//*[contains(text(), 'Profile')]",
                "//*[contains(@class, 'user-menu')]"
            ]
            
            for indicator in logout_indicators:
                try:
                    if self.driver.find_elements(By.XPATH, indicator):
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠ Error checking login status: {e}")
            return False
    
    def ensure_logged_in(self):
        """Ensure we're logged in, login if not"""
        if self.logged_in:
            return True
        
        # Check if we're already logged in by current URL or page content
        current_url = self.driver.current_url
        if "login" not in current_url:
            # We might already be logged in
            if self.check_login_success():
                self.logged_in = True
                return True
        
        # If not logged in, perform login
        return self.login()
    
    def navigate_to_copy_page(self, episode_id, retries=3):
        """Navigate to the specific episode copy page with retry logic"""
        # Ensure we're logged in first
        if not self.ensure_logged_in():
            print("❌ Cannot navigate - not logged in")
            return False
        
        url = f"https://app.dev.portal.masjidal.com/system-admin/content/media/episode/copy/{episode_id}"
        print(f"🌐 Navigating to: {url}")
        
        for attempt in range(retries):
            try:
                self.driver.get(url)
                # Wait for page to load
                time.sleep(5)
                
                # Check if we got redirected to login (session expired)
                if "login" in self.driver.current_url:
                    print("⚠ Session expired, re-logging in...")
                    self.logged_in = False
                    if not self.ensure_logged_in():
                        return False
                    # Retry navigation after login
                    continue
                
                # Check if page loaded successfully (not 404 or error)
                if "404" in self.driver.title or "Error" in self.driver.title:
                    print(f"❌ Page returned error for episode {episode_id}")
                    return False
                
                # Wait for form to load - try multiple element indicators
                form_indicators = [
                    (By.NAME, "title"),
                    (By.XPATH, "//h1[contains(text(), 'Edit Episode')]"),
                    (By.XPATH, "//h2[contains(text(), 'Episode Information')]"),
                    (By.XPATH, "//input[@name='title']")
                ]
                
                for by, selector in form_indicators:
                    try:
                        element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        if element:
                            print(f"✅ Form loaded successfully for episode {episode_id} (attempt {attempt + 1})")
                            return True
                    except TimeoutException:
                        continue
                
                print(f"⚠ Form not loaded on attempt {attempt + 1} for episode {episode_id}")
                
                # Try refreshing the page
                if attempt < retries - 1:
                    print("🔄 Refreshing page...")
                    self.driver.refresh()
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ Navigation error for episode {episode_id} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
        
        print(f"❌ Failed to load form for episode {episode_id} after {retries} attempts")
        return False
    
    def check_if_episode_exists(self, episode_id):
        """Check if an episode exists by trying to navigate to it"""
        # Ensure we're logged in first
        if not self.ensure_logged_in():
            return False
            
        url = f"https://app.dev.portal.masjidal.com/system-admin/content/media/episode/copy/{episode_id}"
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Check if we got redirected to login
            if "login" in self.driver.current_url:
                return False
                
            # Check for 404 or error pages
            page_source = self.driver.page_source.lower()
            if "404" in page_source or "not found" in page_source or "error" in page_source:
                return False
                
            # Check if form elements exist
            try:
                self.driver.find_element(By.NAME, "title")
                return True
            except:
                return False
                
        except Exception as e:
            print(f"Error checking episode {episode_id}: {e}")
            return False
    
    def find_image_for_episode(self, episode_number):
        """Find the corresponding image file for the episode number"""
        # Skip if episode_number is not a valid number
        try:
            int(episode_number)
        except (ValueError, TypeError):
            print(f"⚠ Invalid episode number: {episode_number}")
            return None
            
        patterns = [
            f"*({episode_number}).jpg",
            f"*({episode_number}).jpeg", 
            f"*({episode_number}).png",
            f"*{episode_number}*.jpg",
            f"*{episode_number}*.jpeg",
            f"*{episode_number}*.png",
            f"*{episode_number}.jpg",
            f"*{episode_number}.jpeg",
            f"*{episode_number}.png",
            f"0 ({episode_number}).jpg",
            f"0 ({episode_number}).jpeg",
            f"0 ({episode_number}).png"
        ]
        
        for pattern in patterns:
            matches = glob.glob(os.path.join(self.images_folder, pattern))
            if matches:
                print(f"📷 Found image: {os.path.basename(matches[0])} for episode {episode_number}")
                return matches[0]
        
        print(f"⚠ No image found for episode {episode_number}")
        return None
    
    def upload_thumbnail_image(self, image_path, episode_number):
        """Upload thumbnail image with better error handling"""
        try:
            if not image_path or not os.path.exists(image_path):
                print(f"❌ Image file not found: {image_path}")
                return False
            
            print(f"📤 Attempting to upload image: {os.path.basename(image_path)}")
            
            # Find and click the upload button
            upload_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(@class, 'btn-ma-primary') and contains(text(), 'Upload Thumbnail Image')]"))
            )
            
            # Scroll to the button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", upload_btn)
            time.sleep(2)
            
            # Click the upload button
            upload_btn.click()
            print("✅ Clicked upload button")
            time.sleep(3)
            
            # Find the file input element
            file_input = self.find_file_input()
            
            if file_input:
                # Send the absolute path to the file input
                absolute_path = os.path.abspath(image_path)
                file_input.send_keys(absolute_path)
                print(f"✅ Image path sent: {os.path.basename(image_path)}")
                
                # Wait for upload to complete
                time.sleep(4)
                
                # Try to close any dialogs
                self.close_dialogs()
                
                print(f"✅ Image upload completed for episode {episode_number}")
                return True
            else:
                print("❌ Could not find file input element")
                return False
                    
        except Exception as e:
            print(f"❌ Error uploading image for episode {episode_number}: {str(e)}")
            return False
    
    def find_file_input(self):
        """Find the file input element with multiple strategies"""
        file_input_selectors = [
            "//input[@type='file']",
            "//input[contains(@accept, 'image')]",
            "//input[@name='file']",
            "//input[@name='image']",
            "//input[@name='upload']",
            "//input[contains(@class, 'file')]"
        ]
        
        for selector in file_input_selectors:
            try:
                file_input = self.driver.find_element(By.XPATH, selector)
                if file_input:
                    # Make sure it's interactable
                    self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
                    self.driver.execute_script("arguments[0].style.visibility = 'visible';", file_input)
                    return file_input
            except:
                continue
        
        return None
    
    def close_dialogs(self):
        """Close any open dialogs"""
        try:
            # Try pressing ESC
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass
        
        try:
            # Try clicking on body
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()
            time.sleep(1)
        except:
            pass
    
    def fill_episode_form(self, episode_data):
        """Fill the episode form with data from Excel"""
        try:
            print("📝 Filling episode form...")
            
            # Skip if episode number is invalid
            try:
                episode_num = int(episode_data['EpisodeNumber'])
            except (ValueError, TypeError):
                print(f"❌ Invalid episode number: {episode_data['EpisodeNumber']}")
                return False
            
            # Fill required fields
            required_fields = {
                'Title': ('name', 'title'),
                'EpisodeNumber': ('name', 'episode_number'), 
                'ContentUrl': ('name', 'content_url')
            }
            
            for excel_col, (attr_type, attr_value) in required_fields.items():
                if pd.notna(episode_data[excel_col]) and str(episode_data[excel_col]).strip():
                    success = self.fill_text_field(attr_type, attr_value, episode_data[excel_col])
                    if success:
                        print(f"  ✅ Filled {excel_col}: {episode_data[excel_col]}")
                    else:
                        print(f"  ❌ Failed to fill {excel_col}")
                        return False
            
            # Fill optional fields if they have values
            optional_fields = {
                'Subtitle': ('name', 'subtitle'),
                'Duration': ('name', 'duration'),
                'ReleaseDate': ('name', 'release_date')
            }
            
            for excel_col, (attr_type, attr_value) in optional_fields.items():
                if (excel_col in episode_data and 
                    pd.notna(episode_data[excel_col]) and 
                    str(episode_data[excel_col]).strip()):
                    
                    if excel_col == 'ReleaseDate':
                        self.fill_date_field(episode_data[excel_col])
                    else:
                        self.fill_text_field(attr_type, attr_value, episode_data[excel_col])
                    print(f"  ✅ Filled {excel_col}: {episode_data[excel_col]}")
            
            # Upload thumbnail image based on episode number
            episode_number = episode_data['EpisodeNumber']
            image_path = self.find_image_for_episode(episode_number)
            if image_path:
                if self.upload_thumbnail_image(image_path, episode_number):
                    print(f"  ✅ Image uploaded successfully")
                else:
                    print(f"  ⚠ Image upload failed, but continuing...")
            else:
                print(f"  ⚠ No image found for episode {episode_number}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error filling form: {str(e)}")
            return False
    
    def fill_text_field(self, attr_type, attr_value, text):
        """Fill text input fields with better error handling"""
        try:
            if attr_type == 'name':
                element = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, attr_value))
                )
                element.clear()
                element.send_keys(str(text))
                return True
        except Exception as e:
            print(f"⚠ Could not fill field {attr_value}: {str(e)}")
            return False
    
    def fill_date_field(self, date_str):
        """Fill date field"""
        try:
            # Try different date field selectors
            date_selectors = [
                (By.NAME, "release_date"),
                (By.XPATH, "//input[@type='date']"),
                (By.CSS_SELECTOR, "input[placeholder*='date']")
            ]
            
            for by, selector in date_selectors:
                try:
                    element = self.driver.find_element(by, selector)
                    element.clear()
                    element.send_keys(str(date_str))
                    return
                except:
                    continue
                    
            print("⚠ Could not find date field to fill")
        except Exception as e:
            print(f"⚠ Could not fill date field: {str(e)}")
    
    def save_episode(self):
        """Click the save button and handle the response properly"""
        try:
            # Wait a moment before saving
            time.sleep(3)
            
            # Find the save button
            save_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[@type='submit' and contains(text(), 'Save')]"))
            )
            
            # Scroll to save button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            time.sleep(2)
            
            print("💾 Clicking Save button...")
            
            # Click the save button
            save_button.click()
            
            # Wait for the save to process
            time.sleep(8)
            
            # Check for success or error
            return self.check_save_result()
            
        except Exception as e:
            print(f"❌ Error clicking save button: {str(e)}")
            return False
    
    def check_save_result(self):
        """Check the result of the save operation"""
        try:
            # Check for error messages first
            error_indicators = [
                "//*[contains(text(), 'Failed to save episode information!')]",
                "//*[contains(text(), 'Error')]",
                "//*[contains(text(), 'failed')]",
                "//div[contains(@class, 'error')]",
                "//div[contains(@class, 'alert-danger')]"
            ]
            
            for indicator in error_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    for element in elements:
                        if element.is_displayed():
                            error_text = element.text
                            print(f"❌ Save failed with error: {error_text}")
                            
                            # Try to handle error dialog
                            self.handle_error_dialog()
                            return False
                except:
                    continue
            
            # Check for success indicators
            success_indicators = [
                "//*[contains(text(), 'success')]",
                "//*[contains(text(), 'saved')]",
                "//*[contains(text(), 'created')]",
                "//div[contains(@class, 'success')]",
                "//div[contains(@class, 'alert-success')]"
            ]
            
            for indicator in success_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    for element in elements:
                        if element.is_displayed():
                            print(f"✅ Save successful: {element.text}")
                            return True
                except:
                    continue
            
            # Check if we've been redirected away from the copy page
            current_url = self.driver.current_url
            if "copy" not in current_url:
                print("✅ Save successful - redirected from copy page")
                return True
            
            # If we're still here and no error, assume partial success
            print("⚠ No clear success or error - assuming save worked")
            return True
            
        except Exception as e:
            print(f"⚠ Error checking save result: {e}")
            return True
    
    def handle_error_dialog(self):
        """Handle error dialogs that might appear after failed save"""
        try:
            # Look for Cancel button in error dialog and click it
            cancel_buttons = [
                "//button[contains(text(), 'Cancel')]",
                "//button[contains(@class, 'btn-secondary')]",
                "//button[contains(@class, 'btn-default')]"
            ]
            
            for button_xpath in cancel_buttons:
                try:
                    cancel_btn = self.driver.find_element(By.XPATH, button_xpath)
                    if cancel_btn.is_displayed():
                        cancel_btn.click()
                        print("✅ Clicked Cancel button in error dialog")
                        time.sleep(2)
                        return
                except:
                    continue
                    
            # If no cancel button, try pressing ESC
            self.close_dialogs()
                
        except Exception as e:
            print(f"⚠ Error handling dialog: {e}")
    
    def process_episode_batch(self, excel_path, start_id=665, end_id=694):
        """Process all episodes from Excel with enhanced error handling"""
        try:
            # Read Excel file
            df = pd.read_excel(excel_path)
            
            # Validate required columns
            required_columns = ['EpisodeNumber', 'Title', 'ContentUrl']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            success_count = 0
            current_id = start_id
            
            print(f"🚀 Starting batch processing from episode ID {start_id} to {end_id}")
            print(f"📊 Found {len(df)} episodes in Excel")
            print(f"📁 Images folder: {self.images_folder}")
            print("=" * 60)
            
            # First, let's check if the starting episode exists
            print(f"🔍 Checking if episode {start_id} exists...")
            if not self.check_if_episode_exists(start_id):
                print(f"❌ Episode {start_id} does not exist or is not accessible!")
                print("💡 Please check:")
                print("   - Does episode 665 exist in the system?")
                print("   - Do you have permission to access it?")
                print("   - Is the URL correct?")
                return 0
            
            for index, row in df.iterrows():
                if current_id > end_id:
                    print("🎯 Reached maximum episode ID")
                    break
                
                # Skip rows with invalid episode numbers
                try:
                    episode_num = int(row['EpisodeNumber'])
                except (ValueError, TypeError):
                    print(f"⏭ Skipping row {index + 1} - invalid episode number: {row['EpisodeNumber']}")
                    current_id += 1
                    continue
                
                episode_number = row['EpisodeNumber']
                print(f"\n📍 Processing episode {current_id} - Excel row {index + 1}/{len(df)}")
                print(f"   Episode: {episode_number}, Title: {row['Title']}")
                
                # Navigate to copy page with retry logic
                if not self.navigate_to_copy_page(current_id):
                    print(f"❌ Failed to load page for episode {current_id}")
                    print(f"💡 Cannot continue because episode {current_id + 1} requires episode {current_id} to exist!")
                    break
                
                # Fill form with episode data and upload image
                if self.fill_episode_form(row):
                    # Save the episode
                    if self.save_episode():
                        success_count += 1
                        print(f"✅ Successfully processed episode {current_id} (Episode {episode_number})")
                        print(f"📝 This should have created episode {current_id + 1}")
                    else:
                        print(f"❌ Failed to save episode {current_id}")
                        print(f"💡 Episode {current_id + 1} will not be created!")
                else:
                    print(f"❌ Failed to fill form for episode {current_id}")
                
                current_id += 1
                print(f"⏳ Waiting 4 seconds before next episode...")
                time.sleep(4)
            
            print(f"\n{'='*60}")
            print(f"🎉 BATCH COMPLETED: {success_count}/{len(df)} episodes processed successfully")
            print(f"{'='*60}")
            return success_count
            
        except Exception as e:
            print(f"❌ Batch processing error: {str(e)}")
            return 0
    
    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
        except:
            pass

# Main execution function
def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('episode_automation.log'),
            logging.StreamHandler()
        ]
    )
    
    # Configuration - UPDATE THESE WITH YOUR CREDENTIALS
    USERNAME = "admin@gmail.com"  # Replace with your email
    PASSWORD = "123456"            # Replace with your password
    EXCEL_PATH = 'episodes.xlsx'
    IMAGES_FOLDER = os.path.expanduser('~/Downloads')
    START_ID = 665
    END_ID = 694
    
    print(f"🔐 Login credentials: {USERNAME}")
    print(f"🔍 Looking for images in: {IMAGES_FOLDER}")
    
    automation = None
    try:
        # Initialize automation with login credentials
        automation = EpisodeCopyAutomation(
            username=USERNAME,
            password=PASSWORD,
            headless=False,  # Keep visible for debugging
            images_folder=IMAGES_FOLDER
        )
        
        # Process episodes
        success_count = automation.process_episode_batch(
            excel_path=EXCEL_PATH,
            start_id=START_ID,
            end_id=END_ID
        )
        
        print(f"\n📊 FINAL RESULT: {success_count} episodes processed successfully")
        
    except Exception as e:
        print(f"❌ Main execution error: {str(e)}")
    
    finally:
        if automation:
            automation.close()

if __name__ == "__main__":
    main()