import streamlit as st
import io
import base64
import os
import textwrap
import tempfile
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from transformers import pipeline
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Creative AI Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. SESSION STATE INITIALIZATION (COMBINED)
# ==========================================
# Chat2Comic State
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'comic_pages' not in st.session_state:
    st.session_state.comic_pages = []
if 'user_genders' not in st.session_state:
    st.session_state.user_genders = {'User A': 'male', 'User B': 'female'}

# Card Generator State
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'start'
if 'card_type' not in st.session_state:
    st.session_state.card_type = None
if 'card_data' not in st.session_state:
    st.session_state.card_data = {}
if 'generated_card' not in st.session_state:
    st.session_state.generated_card = None

# ==========================================
# 3. GLOBAL CONFIG FOR COMIC APP
# ==========================================
# REPLACE WITH YOUR ACTUAL PATHS
CHARACTER_IMAGES = {
    # Male character images
    "male_joy": "C:\\Users\\vinay\\chat2comic\\WhatsApp Image 2025-07-26 at 12.19.04_d68f4b6a.jpg",
    "male_sadness": "C:\\Users\\vinay\\chat2comic\\bg-removed-1761593686230.png",
    "male_anger": "C:\\Users\\vinay\\chat2comic\\Images\\Characters\\male_angry.jpg",
    "male_fear": "C:\\Users\\vinay\\chat2comic\\Images\\Characters\\male_scared.jpg",
    "male_surprise": "C:\\Users\\vinay\\chat2comic\\Images\\Characters\\male_surprised.jpg",
    "male_disgust": "C:\\Users\\vinay\\chat2comic\\Images\\Characters\\male_disgusted.jpg",
    "male_neutral": "path/to/male_neutral.jpg",
    
    # Female character images
    "female_joy": "C:\\Users\\vinay\\chat2comic\\Images\\Girl\\Girl Joy.jpg",
    "female_sadness": "C:\\Users\\vinay\\chat2comic\\Images\\Girl\\bg-removed-1761593783820.png",
    "female_anger": "C:\\Users\\vinay\\chat2comic\\Images\\Girl\\Girl Angry.jpg",
    "female_fear": "C:\\Users\\vinay\\chat2comic\\Images\\Girl\\Girl Scared.jpg",
    "female_surprise": "C:\\Users\\vinay\\chat2comic\\Images\\Girl\\Girl Surprised.jpg",
    "female_disgust": "C:\\Users\\vinay\\chat2comic\\Images\\Girl\\Girl Disgusted.jpg",
    "female_neutral": "path/to/female_neutral.jpg",
    
    # Generic/fallback images
    "male_default": "path/to/male_default.jpg",
    "female_default": "path/to/female_default.jpg",
}

BACKGROUND_IMAGES = [
    "C:\\Users\\vinay\\chat2comic\\Images\\Background\\bg-1.jpg", 
    "C:\\Users\\vinay\\chat2comic\\Images\\Background\\bg-2.jpg",
    "C:\\Users\\vinay\\chat2comic\\Images\\Background\\bg-3.jpg",
]

# ==========================================
# 4. HELPER FUNCTIONS: CHAT2COMIC
# ==========================================

@st.cache_resource
def load_emotion_detector():
    try:
        return pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
    except Exception as e:
        st.warning(f"Could not load emotion detection model: {e}")
        return None

def detect_emotion(text):
    try:
        emotion_detector = load_emotion_detector()
        if emotion_detector:
            results = emotion_detector(text)
            return results[0]['label'].lower()
        else:
            return "neutral"
    except Exception as e:
        st.warning(f"Emotion detection failed: {e}")
        return "neutral"

def load_local_image(image_path):
    try:
        if os.path.exists(image_path):
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        else:
            return None
    except Exception as e:
        st.error(f"Error loading image {image_path}: {e}")
        return None

def create_default_background():
    img = Image.new('RGB', (800, 600), '#87CEEB')
    draw = ImageDraw.Draw(img)
    cloud_positions = [(100, 80), (300, 60), (600, 90), (150, 120)]
    for pos in cloud_positions:
        draw.ellipse([pos[0], pos[1], pos[0]+80, pos[1]+40], fill='white')
        draw.ellipse([pos[0]+20, pos[1]-10, pos[0]+100, pos[1]+30], fill='white')
        draw.ellipse([pos[0]+40, pos[1]+5, pos[0]+120, pos[1]+45], fill='white')
    draw.rectangle([0, 400, 800, 600], fill='#90EE90')
    tree_positions = [50, 200, 550, 700]
    for x in tree_positions:
        draw.rectangle([x, 350, x+20, 400], fill='#8B4513')
        draw.ellipse([x-30, 300, x+50, 370], fill='#228B22')
    return img

def get_background_image(page_number=0):
    if BACKGROUND_IMAGES:
        bg_index = page_number % len(BACKGROUND_IMAGES)
        bg_path = BACKGROUND_IMAGES[bg_index]
        image = load_local_image(bg_path)
        if image:
            return image
    return create_default_background()

def create_fallback_character(gender, emotion):
    base_colors = {'male': '#4A90E2', 'female': '#E24A90'}
    emotion_colors = {
        'joy': '#FFD93D', 'sadness': '#6C9BD1', 'anger': '#E74C3C',
        'fear': '#9B59B6', 'surprise': '#F39C12', 'disgust': '#27AE60',
        'neutral': '#95A5A6'
    }
    base_color = base_colors.get(gender, '#95A5A6')
    emotion_color = emotion_colors.get(emotion, '#95A5A6')
    
    img = Image.new('RGBA', (200, 250), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([75, 150, 125, 220], fill=base_color, outline='black', width=2)
    draw.ellipse([60, 50, 140, 130], fill=emotion_color, outline='black', width=2)
    
    if emotion == 'joy':
        draw.arc([75, 80, 85, 90], 0, 180, fill='black', width=2)
        draw.arc([115, 80, 125, 90], 0, 180, fill='black', width=2)
        draw.arc([85, 100, 115, 120], 0, 180, fill='black', width=3)
    elif emotion == 'sadness':
        draw.arc([75, 85, 85, 75], 0, 180, fill='black', width=2)
        draw.arc([115, 85, 125, 75], 0, 180, fill='black', width=2)
        draw.arc([85, 115, 115, 105], 180, 360, fill='black', width=3)
    elif emotion == 'anger':
        draw.line([(75, 75), (85, 80)], fill='black', width=3)
        draw.line([(115, 80), (125, 75)], fill='black', width=3)
        draw.rectangle([90, 110, 110, 115], fill='black')
    else:
        draw.ellipse([78, 82, 82, 86], fill='black')
        draw.ellipse([118, 82, 122, 86], fill='black')
        draw.line([(90, 110), (110, 110)], fill='black', width=2)
    return img

def get_character_image(gender, emotion):
    key = f"{gender}_{emotion}"
    if key in CHARACTER_IMAGES:
        image = load_local_image(CHARACTER_IMAGES[key])
        if image: return image
    
    fallback_key = f"{gender}_default"
    if fallback_key in CHARACTER_IMAGES:
        image = load_local_image(CHARACTER_IMAGES[fallback_key])
        if image: return image
        
    neutral_key = f"{gender}_neutral"
    if neutral_key in CHARACTER_IMAGES:
        image = load_local_image(CHARACTER_IMAGES[neutral_key])
        if image: return image
        
    return create_fallback_character(gender, emotion)

def resize_character(image, max_size=280):
    width, height = image.size
    scale = min(max_size / width, max_size / height)
    if scale < 1:
        new_width = int(width * scale)
        new_height = int(height * scale)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image

def create_speech_bubble(text, max_width=200):
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    max_chars = max(15, max_width // 10)
    wrapped_text = textwrap.fill(text, width=max_chars)
    lines = wrapped_text.split('\n')
    line_height = 20
    text_height = len(lines) * line_height
    
    max_line_width = 0
    for line in lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        max_line_width = max(max_line_width, line_width)
    
    padding = 15
    bubble_width = max_line_width + (padding * 2)
    bubble_height = text_height + (padding * 2)
    
    bubble_img = Image.new('RGBA', (bubble_width + 20, bubble_height + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bubble_img)
    draw.rounded_rectangle([10, 0, bubble_width + 10, bubble_height], radius=15, fill='white', outline='black', width=2)
    pointer_x = bubble_width // 2 + 10
    draw.polygon([(pointer_x - 10, bubble_height), (pointer_x + 10, bubble_height), (pointer_x, bubble_height + 15)], fill='white', outline='black')
    
    y_offset = padding
    for line in lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x_offset = (bubble_width - line_width) // 2 + 10
        draw.text((x_offset, y_offset), line, fill='black', font=font)
        y_offset += line_height
    return bubble_img

def create_comic_page(message_pair, page_number, user_genders):
    background = get_background_image(page_number)
    bg_width, bg_height = background.size
    target_width, target_height = 800, 600
    if bg_width != target_width or bg_height != target_height:
        background = background.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    page = background.copy()
    
    for i, (speaker, message, emotion) in enumerate(message_pair):
        gender = user_genders[speaker]
        char_image = get_character_image(gender, emotion)
        char_image = resize_character(char_image, 250)
        speech_bubble = create_speech_bubble(message, 300)
        
        if speaker == 'User A':
            char_x = 40
            char_y = target_height - char_image.size[1] - 10
            bubble_x = char_x + 30
            bubble_y = char_y - speech_bubble.size[1] - 15
        else:
            char_x = target_width - char_image.size[0] - 40
            char_y = target_height - char_image.size[1] - 10
            bubble_x = char_x - 30
            bubble_y = char_y - speech_bubble.size[1] - 15
        
        if len(message_pair) == 2 and i == 1:
            char_y = target_height - char_image.size[1] - 10
            bubble_y = char_y - speech_bubble.size[1] - 15
            if i == 1 and bubble_y < 120:
                bubble_y = 60
        
        if char_image.mode == 'RGBA':
            page.paste(char_image, (char_x, char_y), char_image)
        else:
            page.paste(char_image, (char_x, char_y))
        page.paste(speech_bubble, (bubble_x, bubble_y), speech_bubble)
    
    draw = ImageDraw.Draw(page)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
    page_text = f"Page {page_number + 1}"
    draw.text((target_width - 60, target_height - 25), page_text, fill='black', font=font)
    return page

def create_comic_pdf(pages):
    if not pages: return None
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_pdf.close()
    temp_files = []
    
    try:
        c = canvas.Canvas(temp_pdf.name, pagesize=A4)
        page_width, page_height = A4
        for i, page_img in enumerate(pages):
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_img_path = temp_img.name
            temp_img.close()
            temp_files.append(temp_img_path)
            page_img.save(temp_img_path, 'PNG')
            
            img_width, img_height = page_img.size
            aspect_ratio = img_width / img_height
            margin = 50
            max_width = page_width - (2 * margin)
            max_height = page_height - (2 * margin)
            
            if aspect_ratio > max_width / max_height:
                draw_width = max_width
                draw_height = max_width / aspect_ratio
            else:
                draw_height = max_height
                draw_width = max_height * aspect_ratio
            
            x = (page_width - draw_width) / 2
            y = (page_height - draw_height) / 2
            c.drawImage(temp_img_path, x, y, width=draw_width, height=draw_height)
            if i < len(pages) - 1:
                c.showPage()
        c.save()
        return temp_pdf.name
    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return None
    finally:
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file): os.unlink(temp_file)
            except: pass

# ==========================================
# 5. HELPER FUNCTIONS: CARD GENERATOR
# ==========================================

def get_color_scheme(occasion_type):
    color_schemes = {
        'birthday': [(255, 192, 203), (255, 105, 180), (255, 20, 147)],
        'wedding': [(255, 215, 0), (255, 228, 196), (255, 182, 193)],
        'housewarming': [(34, 139, 34), (144, 238, 144), (255, 215, 0)],
        'diwali': [(255, 215, 0), (255, 69, 0), (255, 140, 0)],
        'eid': [(0, 128, 0), (255, 215, 0), (255, 255, 255)],
        'christmas': [(255, 0, 0), (0, 128, 0), (255, 215, 0)],
        'new_year': [(255, 215, 0), (192, 192, 192), (0, 0, 0)],
        'default': [(135, 206, 235), (255, 182, 193), (255, 215, 0)]
    }
    occasion_lower = occasion_type.lower()
    for key in color_schemes:
        if key in occasion_lower:
            return color_schemes[key]
    return color_schemes['default']

def create_gradient_background(width, height, colors):
    image = Image.new('RGB', (width, height), colors[0])
    draw = ImageDraw.Draw(image)
    for i in range(height):
        ratio = i / height
        if len(colors) >= 2:
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
    return image

def add_decorative_elements(draw, width, height, card_type):
    for i in range(5):
        x = 30 + i * 8
        y = 30 + i * 8
        draw.ellipse([x-15, y-15, x+15, y+15], fill=(255, 255, 255, 100))
    for i in range(5):
        x = width - 30 - i * 8
        y = 30 + i * 8
        draw.ellipse([x-15, y-15, x+15, y+15], fill=(255, 255, 255, 100))
    draw.line([(50, height-80), (width-50, height-80)], fill=(255, 255, 255), width=3)
    if 'birthday' in card_type.lower() or 'wishes' in card_type.lower():
        for _ in range(8):
            x = random.randint(50, width-50)
            y = random.randint(50, height-100)
            size = random.randint(8, 15)
            draw.ellipse([x-size, y-size, x+size, y+size], fill=(255, 255, 255, 150))

def generate_invitation_card(data):
    width, height = 800, 1000
    colors = get_color_scheme(data.get('event_type', 'default'))
    img = create_gradient_background(width, height, colors)
    draw = ImageDraw.Draw(img, 'RGBA')
    add_decorative_elements(draw, width, height, data.get('event_type', ''))
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 32)
        body_font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    title_text = f"{data.get('event_type', 'Event').upper()} INVITATION"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, 100), title_text, fill=(255, 255, 255), font=title_font)
    
    event_name = data.get('event_name', 'Special Event')
    name_bbox = draw.textbbox((0, 0), event_name, font=subtitle_font)
    name_width = name_bbox[2] - name_bbox[0]
    draw.text(((width - name_width) // 2, 180), event_name, fill=(255, 255, 255), font=subtitle_font)
    
    y_pos = 280
    details = [
        f"📅 Date: {data.get('date_time', 'TBD')}",
        f"📍 Venue: {data.get('venue', 'TBD')}",
        f"👥 Hosted by: {data.get('host_name', 'Host')}"
    ]
    for detail in details:
        wrapped_text = textwrap.fill(detail, width=40)
        for line in wrapped_text.split('\n'):
            line_bbox = draw.textbbox((0, 0), line, font=body_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text(((width - line_width) // 2, y_pos), line, fill=(255, 255, 255), font=body_font)
            y_pos += 40
        y_pos += 20
        
    if data.get('additional_notes'):
        y_pos += 40
        notes_text = data['additional_notes']
        wrapped_notes = textwrap.fill(notes_text, width=50)
        for line in wrapped_notes.split('\n'):
            line_bbox = draw.textbbox((0, 0), line, font=small_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text(((width - line_width) // 2, y_pos), line, fill=(255, 255, 255), font=small_font)
            y_pos += 30
            
    footer_text = "✨ Your presence is our present ✨"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=small_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(((width - footer_width) // 2, height - 150), footer_text, fill=(255, 255, 255), font=small_font)
    return img

def generate_wishes_card(data):
    width, height = 800, 600
    colors = get_color_scheme(data.get('festival_name', 'default'))
    img = create_gradient_background(width, height, colors)
    draw = ImageDraw.Draw(img, 'RGBA')
    add_decorative_elements(draw, width, height, f"wishes {data.get('festival_name', '')}")
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 56)
        subtitle_font = ImageFont.truetype("arial.ttf", 32)
        body_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        
    festival_name = data.get('festival_name', 'Festival')
    greeting = f"Happy {festival_name}!"
    greeting_bbox = draw.textbbox((0, 0), greeting, font=title_font)
    greeting_width = greeting_bbox[2] - greeting_bbox[0]
    draw.text(((width - greeting_width) // 2, 80), greeting, fill=(255, 255, 255), font=title_font)
    
    y_pos = 200
    if data.get('personal_message'):
        message = data['personal_message']
    else:
        default_messages = {
            'diwali': 'May this festival of lights bring joy, prosperity and happiness to your life!',
            'eid': 'May this blessed occasion bring peace, happiness and prosperity to you!',
            'christmas': 'Wishing you a Christmas filled with joy, love and wonderful memories!',
            'new year': 'May the new year bring you happiness, success and all your heart desires!'
        }
        festival_lower = festival_name.lower()
        message = default_messages.get(festival_lower, 'Wishing you joy, happiness and wonderful celebrations!')
        
    wrapped_message = textwrap.fill(message, width=50)
    for line in wrapped_message.split('\n'):
        line_bbox = draw.textbbox((0, 0), line, font=body_font)
        line_width = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_width) // 2, y_pos), line, fill=(255, 255, 255), font=body_font)
        y_pos += 35
        
    y_pos += 60
    sender_text = f"With warm wishes,\n{data.get('sender_name', 'Your Friend')}"
    for line in sender_text.split('\n'):
        line_bbox = draw.textbbox((0, 0), line, font=subtitle_font)
        line_width = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_width) // 2, y_pos), line, fill=(255, 255, 255), font=subtitle_font)
        y_pos += 40
        
    if data.get('receiver_name'):
        receiver_text = f"To: {data['receiver_name']}"
        draw.text((50, height - 80), receiver_text, fill=(255, 255, 255), font=body_font)
    return img

def create_download_link(img, filename):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    b64 = base64.b64encode(img_bytes).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}" class="action-button">📥 Download Card</a>'
    return href

# ==========================================
# 6. APP MODULES
# ==========================================

def run_chat_to_comic():
    st.title("🗨️ Chat2Comic - Turn Conversations into Comics!")
    st.markdown("Create comic pages from your conversations with background scenes and proper positioning!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.subheader("📁 Configured Paths")
        with st.expander("Character Images"):
            for key, path in CHARACTER_IMAGES.items():
                status = "✅" if os.path.exists(path) else "❌"
                st.text(f"{status} {key}")
        
        with st.expander("Background Images"):
            for i, path in enumerate(BACKGROUND_IMAGES):
                status = "✅" if os.path.exists(path) else "❌"
                st.text(f"{status} Background {i+1}")
        
        st.divider()
        st.subheader("👥 Character Genders")
        user_a_gender = st.selectbox("User A Gender:", ["male", "female"], index=0)
        user_b_gender = st.selectbox("User B Gender:", ["male", "female"], index=1)
        
        st.session_state.user_genders = {'User A': user_a_gender, 'User B': user_b_gender}
        st.divider()
        emotion_detection = st.toggle("🧠 Enable Emotion Detection", value=True, help="Automatically detect emotions from text")
        
        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.messages = []
            st.session_state.comic_pages = []
            st.rerun()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("💬 Conversation")
        for i, (speaker, message, emotion) in enumerate(st.session_state.messages):
            with st.chat_message(speaker.lower().replace(' ', '_')):
                st.write(f"**{speaker}** *(emotion: {emotion})*")
                st.write(message)
        
        with st.form("user_a_form"):
            st.write("**User A** ({}):".format(user_a_gender.title()))
            message_a = st.text_area("Message:", key="msg_a", height=100)
            col_a1, col_a2 = st.columns(2)
            with col_a1: submit_a = st.form_submit_button("Send as User A", type="primary")
            with col_a2: manual_emotion_a = st.selectbox("Manual emotion:", ["auto", "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"], key="emotion_a")
        
        with st.form("user_b_form"):
            st.write("**User B** ({}):".format(user_b_gender.title()))
            message_b = st.text_area("Message:", key="msg_b", height=100)
            col_b1, col_b2 = st.columns(2)
            with col_b1: submit_b = st.form_submit_button("Send as User B", type="primary")
            with col_b2: manual_emotion_b = st.selectbox("Manual emotion:", ["auto", "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"], key="emotion_b")

    with col2:
        st.subheader("🎨 Comic Pages")
        if submit_a and message_a.strip():
            if manual_emotion_a != "auto": emotion = manual_emotion_a
            elif emotion_detection: emotion = detect_emotion(message_a)
            else: emotion = "neutral"
            
            st.session_state.messages.append(("User A", message_a, emotion))
            if len(st.session_state.messages) % 2 == 0:
                message_pair = st.session_state.messages[-2:]
                page_number = len(st.session_state.comic_pages)
                with st.spinner("Creating comic page..."):
                    comic_page = create_comic_page(message_pair, page_number, st.session_state.user_genders)
                    st.session_state.comic_pages.append(comic_page)
            st.rerun()
        
        if submit_b and message_b.strip():
            if manual_emotion_b != "auto": emotion = manual_emotion_b
            elif emotion_detection: emotion = detect_emotion(message_b)
            else: emotion = "neutral"
            
            st.session_state.messages.append(("User B", message_b, emotion))
            if len(st.session_state.messages) % 2 == 0:
                message_pair = st.session_state.messages[-2:]
                page_number = len(st.session_state.comic_pages)
                with st.spinner("Creating comic page..."):
                    comic_page = create_comic_page(message_pair, page_number, st.session_state.user_genders)
                    st.session_state.comic_pages.append(comic_page)
            st.rerun()
        
        if st.session_state.comic_pages:
            for i, page in enumerate(st.session_state.comic_pages):
                st.image(page, caption=f"Page {i+1}", use_container_width=True)
            
            st.subheader("📥 Download Comic")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("📖 Generate PDF Comic", type="primary"):
                    with st.spinner("Creating PDF comic..."):
                        try:
                            pdf_path = create_comic_pdf(st.session_state.comic_pages)
                            if pdf_path and os.path.exists(pdf_path):
                                with open(pdf_path, 'rb') as pdf_file: pdf_data = pdf_file.read()
                                st.download_button(label="📚 Download Comic PDF", data=pdf_data, file_name="chat2comic.pdf", mime="application/pdf")
                                try: os.unlink(pdf_path)
                                except: pass
                                st.success("PDF comic ready!")
                            else: st.error("Failed to create PDF.")
                        except Exception as e: st.error(f"Error: {e}")
            with col_d2:
                if st.button("🖼️ Download Pages as PNG"):
                    for i, page in enumerate(st.session_state.comic_pages):
                        img_buffer = io.BytesIO()
                        page.save(img_buffer, format='PNG')
                        st.download_button(label=f"Page {i+1}", data=img_buffer.getvalue(), file_name=f"comic_page_{i+1}.png", mime="image/png", key=f"download_page_{i}")
            
            if len(st.session_state.messages) % 2 == 1:
                st.info("💬 Send one more message to complete the current page!")
        else:
            st.info("Start chatting to generate your comic pages! 🗨️")

    with st.expander("📋 Setup and Usage Guide"):
        st.markdown("""
        **Setup:** Replace paths in `CHARACTER_IMAGES` and `BACKGROUND_IMAGES`.
        **Logic:** Every 2 messages = 1 comic page. User A on Left, User B on Right.
        """)

def run_card_generator():
    # CSS injection specific to card generator
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        .chat-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            color: white;
        }
        .action-button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 10px;
            font-size: 1.2rem;
            font-weight: bold;
            margin: 0.5rem;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .action-button:hover {
            transform: scale(1.05);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">🎨 AI Card Generator ✨</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Create beautiful invitations and wishes cards with AI assistance!</p>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 📋 About AI Card Generator")
        st.markdown("Create invitations and wishes cards with custom designs.")
        st.markdown("---")
        st.markdown("💡 **Tip:** Download in high quality PNG format")

    if st.session_state.current_step == 'start':
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown("### 🤖 Hi there! I'm your AI card designer. What would you like to create today?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 Send Invitation", key="invitation_btn"):
                st.session_state.card_type = 'invitation'
                st.session_state.current_step = 'collect_invitation_data'
                st.rerun()
        with col2:
            if st.button("🎉 Send Wishes", key="wishes_btn"):
                st.session_state.card_type = 'wishes'
                st.session_state.current_step = 'collect_wishes_data'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_step == 'collect_invitation_data':
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown("### 📧 Creating an Invitation Card")
        with st.form("invitation_form"):
            event_type = st.selectbox("Event Type", ["Birthday Party", "Wedding", "Housewarming", "Anniversary", "Graduation", "Baby Shower", "Engagement", "Other"])
            if event_type == "Other": event_type = st.text_input("Please specify the event type:")
            event_name = st.text_input("Event Name/Title", placeholder="e.g., Sarah's 25th Birthday Bash")
            date_time = st.text_input("Date & Time", placeholder="e.g., Saturday, Dec 25th, 2024 at 7:00 PM")
            venue = st.text_input("Venue", placeholder="e.g., 123 Main Street, City")
            host_name = st.text_input("Host Name(s)", placeholder="e.g., John & Jane Doe")
            additional_notes = st.text_area("Additional Notes (Optional)")
            if st.form_submit_button("🎨 Generate Invitation Card"):
                st.session_state.card_data = {
                    'event_type': event_type, 'event_name': event_name,
                    'date_time': date_time, 'venue': venue,
                    'host_name': host_name, 'additional_notes': additional_notes
                }
                st.session_state.current_step = 'generate_card'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_step == 'collect_wishes_data':
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown("### 🎉 Creating a Wishes Card")
        with st.form("wishes_form"):
            festival_name = st.selectbox("Festival/Occasion", ["Diwali", "Eid", "Christmas", "New Year", "Holi", "Thanksgiving", "Easter", "Other"])
            if festival_name == "Other": festival_name = st.text_input("Please specify the festival/occasion:")
            sender_name = st.text_input("Your Name", placeholder="e.g., John Doe")
            receiver_name = st.text_input("Receiver's Name (Optional)", placeholder="e.g., Dear Friends")
            personal_message = st.text_area("Personal Message (Optional)")
            if st.form_submit_button("🎨 Generate Wishes Card"):
                st.session_state.card_data = {
                    'festival_name': festival_name, 'sender_name': sender_name,
                    'receiver_name': receiver_name, 'personal_message': personal_message
                }
                st.session_state.current_step = 'generate_card'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_step == 'generate_card':
        with st.spinner('🎨 Creating your beautiful card...'):
            try:
                if st.session_state.card_type == 'invitation':
                    card_img = generate_invitation_card(st.session_state.card_data)
                else:
                    card_img = generate_wishes_card(st.session_state.card_data)
                st.session_state.generated_card = card_img
                st.session_state.current_step = 'show_card'
                st.rerun()
            except Exception as e:
                st.error(f"Error generating card: {str(e)}")

    elif st.session_state.current_step == 'show_card':
        st.markdown("### 🎉 Your Beautiful Card is Ready!")
        if st.session_state.generated_card:
            st.image(st.session_state.generated_card, caption="Your Generated Card", use_container_width=True)
            filename = f"card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            download_link = create_download_link(st.session_state.generated_card, filename)
            st.markdown(download_link, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Create Another Card"):
                    st.session_state.current_step = 'start'
                    st.session_state.card_data = {}
                    st.session_state.generated_card = None
                    st.rerun()
            with col2:
                if st.button("✏️ Edit This Card"):
                    st.session_state.current_step = 'collect_invitation_data' if st.session_state.card_type == 'invitation' else 'collect_wishes_data'
                    st.rerun()

# ==========================================
# 7. MAIN NAVIGATION
# ==========================================
def main():
    st.sidebar.title("Navigation")
    app_choice = st.sidebar.radio("Go to:", ["Chat2Comic", "AI Card Generator"])
    
    st.sidebar.markdown("---")
    
    if app_choice == "Chat2Comic":
        run_chat_to_comic()
    elif app_choice == "AI Card Generator":
        run_card_generator()
        
    st.sidebar.markdown("---")
    st.sidebar.info("Creative AI Studio | Combined App v1.0")

if __name__ == "__main__":
    main()