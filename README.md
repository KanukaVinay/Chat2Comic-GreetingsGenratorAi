# Chat2Comic-GreetingsGenratorAi
An AI-powered web app that combines Chat2Comic and Greetings Generator. It transforms chat stories into comic strips and creates stylish greeting &amp; invitation designs using AI, all in one unified, user-friendly interface.
🎨 Creative AI Studio
Creative AI Studio is a unified Streamlit application that combines two powerful creative tools: Chat2Comic and AI Card Generator. Whether you want to turn a text conversation into a visual comic strip or generate beautiful invitation cards, this app handles it all in one interface.
✨ Features
1. 🗨️ Chat2Comic
Turn your chat history into a visual comic book!
Dual User Roleplay: Interactive chat interface for "User A" and "User B" with customizable genders.
AI Emotion Detection: Uses a BERT-based model (j-hartmann/emotion-english-distilroberta-base) to automatically analyze text and detect emotions (Joy, Sadness, Anger, Fear, Surprise, etc.).
Dynamic Character Mapping: Automatically selects character images matching the user's gender and detected emotion.
Visual Comic Generation: Composites characters, speech bubbles, and backgrounds into comic panels (2 messages per page).
Export Options: Download individual pages as PNG or the full story as a PDF.
2. 💌 AI Card Generator
Create aesthetic invitations and greeting cards in seconds.
Two Modes:
Invitations: Weddings, Birthdays, Housewarming, etc.
Wishes: Festivals (Diwali, Christmas, Eid), Personal greetings.
Custom Design: Generates procedural gradient backgrounds and decorative elements based on the occasion.
Instant Download: Renders high-quality PNG cards ready for sharing.
🛠️ Installation
Prerequisites
Python 3.8+
An internet connection (for downloading the emotion detection model on the first run).
1. Clone or Download the Repository
Save the provided Python code as app.py.
2. Install Dependencies
Create a requirements.txt file or run the following command to install the necessary libraries:
code
Bash
pip install streamlit pillow transformers torch reportlab
(Note: torch is required for the HuggingFace transformers pipeline).
⚙️ Configuration (Crucial Step)
The application relies on local image assets for the Comic generator. The provided code currently points to specific paths on a local drive (e.g., C:\Users\vinay\...). You must update these paths or create a folder structure to match your environment.
1. Asset Folder Structure
It is recommended to create a folder structure like this next to your app.py:
code
Text
project_root/
│
├── app.py
└── assets/
    ├── backgrounds/
    │   ├── bg-1.jpg
    │   ├── bg-2.jpg
    │   └── ...
    └── characters/
        ├── male_joy.jpg
        ├── male_anger.jpg
        ├── female_joy.jpg
        └── ...
2. Update Path Variables
Open app.py in your code editor and look for Section 3: GLOBAL CONFIG. Update the CHARACTER_IMAGES and BACKGROUND_IMAGES dictionaries to point to your actual file locations.
Example Update:
code
Python
# In app.py

CHARACTER_IMAGES = {
    # Male character images
    "male_joy": "assets/characters/male_joy.jpg",
    "male_sadness": "assets/characters/male_sadness.jpg",
    # ... update all keys ...
}

BACKGROUND_IMAGES = [
    "assets/backgrounds/bg-1.jpg", 
    "assets/backgrounds/bg-2.jpg",
]
Note: If an image is missing, the app uses a built-in fallback drawing function, so the app won't crash, but it will look better with real images.
🚀 Usage
Run the application using Streamlit:
code
Bash
streamlit run app.py
Navigating the App
Use the Sidebar to switch between modes:
Chat2Comic Mode
Sidebar: Select the Gender for User A and User B.
Chat Interface: Type messages for User A or User B.
Emotions: Leave "Manual emotion" on auto to let AI detect the mood, or override it manually.
Generate: Every 2 messages create 1 comic page automatically on the right side.
Download: Click "Generate PDF Comic" to save your story.
Card Generator Mode
Select Type: Choose "Send Invitation" or "Send Wishes".
Fill Details: Enter event names, dates, venues, or personal messages.
Generate: Click the button to render the card.
Download: Use the download link to save the PNG image.
🧩 Technologies Used
Streamlit: For the web interface and state management.
Pillow (PIL): For image processing, drawing speech bubbles, and generating gradients.
HuggingFace Transformers: For the distilroberta emotion detection model.
ReportLab: For compiling images into a PDF document.
⚠️ Troubleshooting
Model Download: On the very first run, the app will download the emotion model (~300MB). This might take a minute.
Font Issues: The app tries to use arial.ttf. If not found (common on Linux/Cloud), it falls back to the default Pillow font. For better typography, ensure arial.ttf is available or modify the font loading code.
Image Paths: If you see "X" marks in the sidebar under "Configured Paths," it means the app cannot find your images. Check the paths in the code.
