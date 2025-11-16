Episode Copy Automation Script
Overview
This automation script was developed to streamline the process of copying and updating media episodes in a CMS system. The script automates form filling, image uploading, and saving episodes in bulk, significantly reducing manual effort for content management teams.

The development process involved:

Creating a robust Selenium-based automation framework

Handling form inputs, file uploads, and save operations

Implementing login functionality for secure access

Adding error handling and retry mechanisms

Debugging 404 errors and save failures

Implementing session management and dialog handling

Prerequisites
Python 3.7+

Chrome browser installed

ChromeDriver (automatically managed by Selenium)

Valid login credentials for the portal

Installation
Install required packages:

bash
pip install selenium pandas openpyxl
Download ChromeDriver (if not automatically managed):

bash
# Usually handled automatically by Selenium, but if needed:
# Download from https://chromedriver.chromium.org/
# Place in your PATH or in the script directory
File Structure
text
episode-automation/
├── downloader2.py          # Main automation script
├── imager.py              # Image downloader script (if needed)
├── episodes.xlsx          # Excel file with episode data
├── episode_automation.log # Automated logging
└── README.md
Setup Steps
1. Prepare Excel Data
Open episodes.xlsx

Remove the first row (header row with "REQUIRED" text)

Ensure columns are properly formatted:

EpisodeNumber (numeric)

Title (text)

ContentUrl (URL)

Subtitle, Duration, ReleaseDate (optional)

ThumbnailUrl (optional)

2. Download Images
bash
python imager.py
Ensure images are saved in Downloads folder

Format should match: 0 (1).jpg, 0 (2).jpg, etc.

Image numbers should correspond to EpisodeNumbers

3. Create First Episode
Manually create the first episode in the CMS

Note the ID number of this episode

This becomes your start_id in the script

4. Configure Script
Edit downloader2.py and update these variables in the main() function:

python
USERNAME = "your_email@gmail.com"  # Your login email
PASSWORD = "your_password"         # Your login password
EXCEL_PATH = 'episodes.xlsx'       # Path to your Excel file
IMAGES_FOLDER = os.path.expanduser('~/Downloads')  # Images location
START_ID = 665                     # ID from step 3
END_ID = 694                       # start_id + (total_episodes - 1)
5. Calculate End ID
Formula: end_id = start_id + (total_episodes - 1)

Example: If start_id is 665 and you have 30 episodes, end_id = 665 + 29 = 694

Running the Automation
Execute the script:

bash
python downloader2.py
Monitor the process:

Script will automatically login

Process each episode sequentially

Upload corresponding images

Save and move to next episode

Log progress and errors

Expected output:

text
🔐 Login credentials: your_email@gmail.com
🔍 Looking for images in: C:/Users/username/Downloads
🚀 Starting batch processing from episode ID 665 to 694
📊 Found 30 episodes in Excel
============================================================

📍 Processing episode 665 - Excel row 1/30
   Episode: 1, Title: Importance of the Sunnah
🌐 Navigating to: https://app.dev.portal.masjidal.com/system-admin/content/media/episode/copy/665
✅ Form loaded successfully
📝 Filling episode form...
  ✅ Filled Title: Importance of the Sunnah
  ✅ Filled EpisodeNumber: 1
  ✅ Filled ContentUrl: https://www.youtube.com/embed/ecOpVk3eAto...
📷 Found image: 0 (1).jpg for episode 1
📤 Attempting to upload image: 0 (1).jpg
✅ Clicked upload button
✅ Image path sent: 0 (1).jpg
✅ Image upload completed for episode 1
  ✅ Image uploaded successfully
💾 Clicking Save button...
✅ Save successful - redirected from copy page
✅ Successfully processed episode 665 (Episode 1)
Post-Run Verification
After script completion:

Check CMS for accuracy:

Verify all episodes were created

Confirm titles and content URLs are correct

Ensure thumbnails are properly uploaded

Check episode numbering sequence

Review logs:

Check episode_automation.log for any errors

Verify success count matches expected episodes

Troubleshooting
Common Issues:
Login Failures:

Verify credentials are correct

Check internet connection

Ensure portal URL is accessible

Form Loading Issues:

Check if episode ID exists in CMS

Verify permissions for episode access

Increase wait times in script if needed

Save Failures:

Check for "Failed to save episode information" errors

Verify all required fields are filled

Ensure file uploads complete before saving

Image Upload Issues:

Confirm images are in Downloads folder

Verify naming convention matches episode numbers

Check image file formats (jpg, png, jpeg)

Debug Mode:
Run with headless=False to see the browser in action and debug issues visually.

Script Features
✅ Automatic login with session management

✅ Form filling with error handling

✅ Image upload with multiple fallback strategies

✅ Save operation with success/failure detection

✅ Error dialog handling

✅ Progress logging and status updates

✅ Rate limiting to avoid server overload

✅ Retry logic for failed operations

Support
If issues persist:

Check the log file for detailed error messages

Verify all setup steps were followed correctly

Ensure episode IDs follow the correct sequence

Confirm image naming matches episode numbers exactly

This automation handles the complete workflow from login to episode creation, making bulk content management efficient and reliable.

This response is AI-generated, for reference only.
