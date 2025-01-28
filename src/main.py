import os
import json
import streamlit as st
from openai import OpenAI
import base64
import requests
from streamlit.components.v1 import html
import streamlit.components.v1 as components
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ No OpenAI API key found. Please check your .env file.")
    st.stop()

# Initialize OpenAI client with API key
client = OpenAI(api_key=api_key)

# Silently test the connection
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
except Exception as e:
    st.error(f"❌ API Error: {str(e)}")
    st.stop()

def text_to_speech(text, user_name=None):
    """Convert text to speech using OpenAI's TTS - Chinese only"""
    try:
        # Get only the first Chinese sentence (before any English or newlines)
        first_line = text.split('\n')[0]
        main_text = first_line.split('(')[0] if '(' in first_line else first_line
        
        # Clean up the text and keep only Chinese characters and user's name
        cleaned_text = ""
        
        # Replace {name} placeholder with actual user name if present
        if user_name:
            main_text = main_text.replace("[name]", user_name)
        
        # Process the main text
        words = main_text.split()
        for word in words:
            # Keep the word if it's the user's name
            if user_name and user_name.lower() in word.lower():
                cleaned_text += user_name + " "
            # Keep the word if it contains Chinese characters or specific punctuation
            elif any('\u4e00' <= c <= '\u9fff' for c in word) or any(c in '，。！？' for c in word):
                cleaned_text += word + " "
            # Keep emojis if present
            elif any(c for c in word if c in '☕🌸💕💖'):
                cleaned_text += word + " "
        
        # Skip if no Chinese text to process
        if not cleaned_text.strip():
            return ""
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=cleaned_text.strip()
        )
        
        # Save the audio to a temporary file
        audio_file_path = "temp_audio.mp3"
        response.stream_to_file(audio_file_path)
        
        # Read the audio file and create a base64 string
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # Remove temporary file
        os.remove(audio_file_path)
        
        # Create HTML audio element with subtle styling
        audio_html = f"""
            <div style="margin: 0;">
                <audio controls style="height: 30px; width: 180px;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
            </div>
            """
        return audio_html
    except Exception as e:
        return f"Error generating audio: {str(e)}"

# Load custom avatars
working_dir = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(working_dir, "assets")

# Create assets directory if it doesn't exist
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# Define avatar paths
TUTOR_AVATAR = os.path.join(ASSETS_DIR, "tutor_avatar.png")
USER_AVATAR = os.path.join(ASSETS_DIR, "user_avatar.png")

# After ASSETS_DIR definition, add:
MP4_DIR = os.path.join(ASSETS_DIR, "mp4")
KISSY_VIDEO = os.path.join(MP4_DIR, "kissy.mp4")

# Add chat styling
st.markdown("""
    <style>
        /* Main container adjustments */
        .stChatFloatingInputContainer {
            padding-bottom: 60px;
        }
        
        /* Message container */
        .stChatMessage {
            width: 85% !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
            position: relative !important;
        }
        
        /* Assistant messages - left aligned */
        div[data-testid="assistant-message"] {
            margin-right: auto !important;
            margin-left: 0 !important;
            background-color: #f0f2f6 !important;
            border-radius: 15px 15px 15px 0 !important;
        }
        
        /* User messages - right aligned */
        div[data-testid="user-message"] {
            margin-left: auto !important;
            margin-right: 0 !important;
            background-color: #2e7bf6 !important;
            color: white !important;
            border-radius: 15px 15px 0 15px !important;
        }
        
        /* Message content alignment */
        div[data-testid="assistant-message"] > div {
            text-align: left !important;
        }
        
        div[data-testid="user-message"] > div {
            text-align: right !important;
        }
        
        /* Audio player styling */
        audio {
            width: 100% !important;
            max-width: 200px !important;
            margin-top: 8px !important;
        }
        
        /* Avatar adjustments */
        .stChatMessage .stAvatar {
            margin: 0 5px !important;
        }
        
        /* Hide default message margins */
        .stMarkdown {
            margin: 0 !important;
        }
        
        /* Typing indicator container */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            background: #f0f2f6;
            border-radius: 15px;
            width: fit-content;
            margin: 0;
        }
        
        /* Typing dots */
        .typing-dot {
            width: 6px;
            height: 6px;
            background: #666;
            border-radius: 50%;
            animation: typing-dot 1.4s infinite;
            opacity: 0.3;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing-dot {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }
    </style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are Mei Mei, a sweet and feminine Chinese tutor who creates romantic coffee date scenarios. Your purpose is to help users practice Chinese while feeling like they're on a date.

Core Personality:
- Always address user with endearing terms: '亲爱的 [name]', '[name] 宝贝', or just '亲爱的/宝贝'
- Be gentle, nurturing, and subtly flirtatious
- Act slightly helpless to make the user feel protective and needed
- Show genuine interest in user's responses
- Create scenarios where the user can be heroic
- Remember and reference previous conversations

Initial Interaction Flow:
1. First Message: Ask for name
   Example:
   你好啊！我叫美美，你叫什么名字呢？
   (Hello! I'm Mei Mei, what's your name?) 🌸
   
2. Second Message: Ask about Chinese level
   Example:
   亲爱的[name]，你的中文水平怎么样？
   (Dear [name], how's your Chinese level?)
   - 基础 (Basic)
   - 中级 (Intermediate)
   - 流利 (Fluent)

Response Structure:
1. Chinese Text (Pinyin)
(English Translation) + Emoji

2. Word-by-Word Breakdown:
[Each word with pinyin and meaning]

3. Suggested Responses:
[2-3 simple options with pinyin and translation]

Level-Based Guidelines:
- Basic: Max 10 words, full breakdown
- Intermediate: 10-20 words, key phrases explained
- Fluent: Natural conversation

Café Scenario Examples:
1. Ordering Help:
亲爱的[name]，你能帮我点咖啡吗？☕
(Dear [name], can you help me order coffee?)

2. Menu Confusion:
[name]宝贝，这个菜单太难懂了。
(Baby [name], this menu is too hard to understand.)

3. Temperature Issues:
啊，我的咖啡好烫！你能帮我吹吹吗？
(Ah, my coffee is too hot! Can you help cool it down?)

Key Interaction Rules:
1. Every response must:
   - Use endearing terms
   - Create a scenario needing help
   - Keep Chinese text concise
   - Include clear response options
   - Make user feel needed/masculine
   - End with a question or choice
   - Use emojis for warmth

2. Café Topics to Cover:
   - Ordering drinks/food
   - Coffee/tea preferences
   - Café atmosphere
   - Pastries and desserts
   - Weather small talk
   - Prices and numbers
   - Table manners

Example Response Format:
亲爱的[name]宝贝，你能帮我点咖啡吗？☕
(Dear [name], can you help me order coffee?)

Would you like to choose a coffee for us? It's so sweet of you to help me! 🌸💕

Word-by-Word Breakdown:
亲爱的 (qīn'ài de) - dear
[name]宝贝 ([name] bǎo bèi) - [name] darling
你能 (nǐ néng) - can you
帮我 (bāng wǒ) - help me
点 (diǎn) - order
咖啡 (kā fēi) - coffee

Suggested Responses:
1. 当然，我来帮你选择。
   (dāng rán, wǒ lái bāng nǐ xuǎn zé.)
   Of course, I'll help you choose.

2. 我们一起看看菜单吧。
   (wǒ men yī qǐ kàn kàn cài dān ba.)
   Let's look at the menu together.

3. 你喜欢什么口味的咖啡？
   (nǐ xǐ huān shén me kǒu wèi de kā fēi?)
   What flavor of coffee do you like?

Try practicing these responses to improve your Chinese! Each response includes pinyin and translation to help you learn. 💪"""

# Initialize session state with user info
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": None,
        "proficiency": None
    }

# Initialize chat history with first message if empty
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
    # Separate the video and text content
    video_html = """
        <div style="margin-bottom: 1rem;">
            <video width="320" height="240" autoplay loop muted playsinline style="border-radius: 10px;">
                <source src="https://i.imgur.com/lNH72gk.mp4" type="video/mp4">
            </video>
        </div>
    """
    
    text_content = """
欢迎光临！(huān yíng guāng lín!) 
请问你叫什么名字呢？(qǐng wèn nǐ jiào shén me míng zi ne?)
(Welcome to our café! What's your name?) 🌸

Try saying:
我叫... (wǒ jiào...) - My name is...

---
Word-by-Word Breakdown:
欢迎 (huān yíng) - welcome
光临 (guāng lín) - to visit/attend
请问 (qǐng wèn) - may I ask
你 (nǐ) - you
叫 (jiào) - called
什么 (shén me) - what
名字 (míng zi) - name
呢 (ne) - question particle

Type your name using: 
我叫 [your name] (wǒ jiào [your name])
"""
    
    # Generate audio for Chinese text only
    audio_html = text_to_speech("欢迎光临！请问你叫什么名字呢？")
    message_id = len(st.session_state.chat_history)
    
    # Store the first message with all components
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": text_content,
        "id": message_id,
        "video_html": video_html  # Store video HTML separately
    })
    st.session_state.audio_elements = {message_id: audio_html}

# Add these constants at the top of the file with other constants
REACTION_VIDEOS = {
    "appreciation": "https://i.imgur.com/kDA2aub.mp4",
    "crying": "https://i.imgur.com/CjCaHt2.mp4",
    "cheering": "https://i.imgur.com/cMD0EoE.mp4",
    "sighing": "https://i.imgur.com/E0rQas1.mp4",
    "thinking": "https://i.imgur.com/KPxXcZA.mp4"
}

def should_show_video(message_count):
    """Determine if we should show a video based on message count"""
    # Show video every 3-5 messages (randomly)
    return message_count % random.randint(3, 5) == 0

def get_appropriate_video(message_content):
    """Select appropriate video based on message content"""
    # Check message content for relevant keywords/sentiment
    content_lower = message_content.lower()
    
    if any(word in content_lower for word in ["谢谢", "thank", "great", "good job", "well done", "很好"]):
        return REACTION_VIDEOS["appreciation"]
    elif any(word in content_lower for word in ["对不起", "sorry", "sad", "难过"]):
        return REACTION_VIDEOS["crying"]
    elif any(word in content_lower for word in ["太棒了", "wonderful", "amazing", "excellent", "开心"]):
        return REACTION_VIDEOS["cheering"]
    elif any(word in content_lower for word in ["哎呀", "唉", "difficult", "hard", "不好"]):
        return REACTION_VIDEOS["sighing"]
    elif any(word in content_lower for word in ["让我想想", "think", "考虑", "interesting", "hmm"]):
        return REACTION_VIDEOS["thinking"]
    
    # Default to thinking video if no specific sentiment is matched
    return REACTION_VIDEOS["thinking"]

def create_video_html(video_url):
    """Create HTML for video display"""
    return f"""
        <div style="margin-bottom: 1rem;">
            <video width="320" height="240" autoplay loop muted playsinline style="border-radius: 10px;">
                <source src="{video_url}" type="video/mp4">
            </video>
        </div>
    """

# Process user response and update user_info
def process_user_response(message):
    if not st.session_state.user_info["name"]:
        st.session_state.user_info["name"] = message
        name_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": f"""
你好，{message}！(nǐ hǎo, {message}!) ✨

今天想喝点什么呢？(jīn tiān xiǎng hē diǎn shén me ne?)
(What would you like to drink today?) ☕

Try these phrases:
我想要一杯... (wǒ xiǎng yào yī bēi...) - I would like a cup of...

---
Word-by-Word Breakdown:
你好 (nǐ hǎo) - hello
今天 (jīn tiān) - today
想 (xiǎng) - want to
喝点 (hē diǎn) - drink something
什么 (shén me) - what
呢 (ne) - question particle
我 (wǒ) - I
想要 (xiǎng yào) - would like
一 (yī) - one
杯 (bēi) - cup (measure word)

Common orders:
1. 我想要一杯咖啡 
   (wǒ xiǎng yào yī bēi kā fēi)
   I would like a coffee

2. 我想要一杯茶 
   (wǒ xiǎng yào yī bēi chá)
   I would like a tea

3. 我想要一杯热巧克力
   (wǒ xiǎng yào yī bēi rè qiǎo kè lì)
   I would like a hot chocolate

Type your order using one of these phrases!
"""}
            ]
        )
        name_message = name_response.choices[0].message.content
        
        # Generate audio for the greeting and question
        audio_html = text_to_speech(
            f"你好，{message}！今天想喝点什么呢？", 
            user_name=message
        )
        message_id = len(st.session_state.chat_history)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": name_message,
            "id": message_id
        })
        st.session_state.audio_elements[message_id] = audio_html
        return "continue_chat"
    elif not st.session_state.user_info["proficiency"]:
        st.session_state.user_info["proficiency"] = message.lower()
        return "normal_chat"
    return "normal_chat"

# Display chat history
for message in st.session_state.chat_history:
    avatar = TUTOR_AVATAR if message["role"] == "assistant" else USER_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        # Display video only for the first message
        if message["role"] == "assistant" and "video_html" in message:
            components.html(message["video_html"], height=300)
        st.markdown(message["content"])
        # Display audio for assistant messages
        if message["role"] == "assistant" and "id" in message and message["id"] in st.session_state.audio_elements:
            st.markdown(st.session_state.audio_elements[message["id"]], unsafe_allow_html=True)

# Add function to show typing indicator
def show_typing_indicator():
    """Show typing indicator in chat"""
    placeholder = st.empty()
    with placeholder.container():
        with st.chat_message("assistant", avatar=TUTOR_AVATAR):
            st.markdown("""
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            """, unsafe_allow_html=True)
    return placeholder

# Add this function before the chat handling code
def format_message_content(content):
    """Format the message content with proper spacing"""
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        if line.startswith('Word-by-Word Breakdown:'):
            # Add extra newline before breakdown section
            formatted_lines.extend(['', line, ''])
        elif ' - ' in line and '(' in line and ')' in line:
            # This is a breakdown line, add proper spacing
            formatted_lines.append(line)
        elif line.startswith('Suggested Responses:'):
            # Add extra newline and formatting for suggested responses
            formatted_lines.extend([
                '',
                '---',
                '👉 Try one of these responses:',
                ''
            ])
        elif line.strip().startswith(('1.', '2.', '3.')):
            # Format numbered responses with emojis and better spacing
            formatted_lines.extend(['', f'🗣 {line}'])
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

# Update the chat input handling section
if prompt := st.chat_input("Type your message here...", key="main_chat_input"):
    # Add user message to chat
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Show typing indicator while processing
    typing_placeholder = show_typing_indicator()
    
    # Process response based on conversation state
    chat_state = process_user_response(prompt)
    
    # Prepare system message with user context
    system_message = SYSTEM_PROMPT
    if st.session_state.user_info["name"]:
        system_message += f"\nUser's name: {st.session_state.user_info['name']}"
    if st.session_state.user_info["proficiency"]:
        system_message += f"\nProficiency level: {st.session_state.user_info['proficiency']}"
    
    # Get assistant response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            *[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
        ]
    )
    
    # Remove typing indicator before showing response
    typing_placeholder.empty()
    
    # Generate a unique ID for this message
    message_id = len(st.session_state.chat_history)
    
    # Get assistant response content
    assistant_response = response.choices[0].message.content
    
    # Determine if we should show a video
    should_include_video = should_show_video(message_id)
    
    # Create message data
    message_data = {
        "role": "assistant",
        "content": assistant_response,
        "id": message_id
    }
    
    # Add video if appropriate
    if should_include_video:
        video_url = get_appropriate_video(assistant_response)
        message_data["video_html"] = create_video_html(video_url)
    
    # Display message with video if present
    with st.chat_message("assistant", avatar=TUTOR_AVATAR):
        if should_include_video:
            components.html(message_data["video_html"], height=300)
        
        # Format the content before displaying
        formatted_content = format_message_content(assistant_response)
        st.markdown(formatted_content)
        
        # Generate and display audio for the first Chinese sentence only
        audio_html = text_to_speech(
            assistant_response, 
            user_name=st.session_state.user_info["name"]
        )
        if audio_html:
            st.session_state.audio_elements[message_id] = audio_html
            st.markdown(audio_html, unsafe_allow_html=True)
    
    # Add response to chat history
    st.session_state.chat_history.append(message_data)

# Add this JavaScript to automatically scroll to the latest message
st.markdown("""
<script>
function scrollToBottom() {
    const messages = document.querySelector('.stChatMessageContainer');
    if (messages) {
        messages.scrollTop = messages.scrollHeight;
    }
}
// Call scrollToBottom when new content is added
const observer = new MutationObserver(scrollToBottom);
observer.observe(
    document.querySelector('.stChatMessageContainer'),
    { childList: true, subtree: true }
);
</script>
""", unsafe_allow_html=True)
