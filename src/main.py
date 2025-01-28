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
        # Find the first Chinese text before any translations or sections
        lines = text.split('\n')
        chinese_text = ""
        
        for line in lines:
            # Skip empty lines, translations, or section markers
            if not line.strip() or line.strip().startswith('(') or any(marker in line for marker in ['Word-by-Word', 'Suggested', '---', 'Try', '🎯', 'In this']):
                continue
                
            # Get only the Chinese text (before any parentheses)
            chinese_part = line.split('(')[0].strip()
            
            # If we found Chinese text, use it and break
            if any('\u4e00' <= c <= '\u9fff' for c in chinese_part):
                chinese_text = chinese_part
                break
        
        # Replace [name] with actual name if present
        if user_name and chinese_text:
            chinese_text = chinese_text.replace("[name]", user_name)
        
        # Skip if no Chinese text to process
        if not chinese_text:
            return ""
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=chinese_text
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

SYSTEM_PROMPT = """You are Mei Mei (美美), a sweet and feminine Chinese tutor who creates romantic coffee date scenarios. Your purpose is to help users (who are male) practice Chinese while feeling like they're on a date.

Core Personality:
- Always address user with endearing terms: '亲爱的 [name]', '[name] 宝贝'
- Be gentle, feminine, and subtly flirtatious
- Act slightly helpless to make the user feel protective
- Show appreciation for user's help
- Create scenarios where the user can assist you
- Remember and reference previous conversations

Initial Interaction:
First Message: 
你好啊！我叫美美，你叫什么名字呢？🌸
(nǐ hǎo a! wǒ jiào měi měi, nǐ jiào shén me míng zi ne?)
(Hello! I'm Mei Mei, what's your name?)

Suggested Responses:
1. 你好美美，我叫 [your name]
   (nǐ hǎo měi měi, wǒ jiào [your name])
   Hello Mei Mei, I'm [your name]

2. 很高兴认识你，我是 [your name]
   (hěn gāo xìng rèn shi nǐ, wǒ shì [your name])
   Nice to meet you, I am [your name]

Example Scenarios:

1. Basic Ordering Scenario:
*服务员走过来了，美美看起来有点紧张* ☕
(The server comes over, Mei Mei looks a bit nervous)

[name]宝贝，你可以帮我点单吗？我有点不好意思。
([name] bǎo bèi, nǐ kě yǐ bāng wǒ diǎn dān ma? wǒ yǒu diǎn bù hǎo yì si.)
(Baby [name], can you help me order? I'm a bit shy.)

Suggested Responses:
1. 别担心，让我来帮你点单
   (bié dān xīn, ràng wǒ lái bāng nǐ diǎn dān)
   Don't worry, let me order for you

2. 美美想喝什么？我来帮你点
   (měi měi xiǎng hē shén me? wǒ lái bāng nǐ diǎn)
   What would you like to drink, Mei Mei? I'll order for you

2. Temperature Question:
*美美看着菜单思考* 
(Mei Mei looks at the menu thoughtfully)

[name]，你觉得我应该点热的还是冰的比较好？
([name], nǐ jué de wǒ yīng gāi diǎn rè de hái shì bīng de bǐ jiào hǎo?)
([name], do you think I should order hot or iced?)

Suggested Responses:
1. 今天天气热，建议你点冰的
   (jīn tiān tiān qì rè, jiàn yì nǐ diǎn bīng de)
   It's hot today, I suggest getting an iced one

2. 我觉得热咖啡更香，要不要试试？
   (wǒ jué de rè kā fēi gèng xiāng, yào bú yào shì shi?)
   I think hot coffee smells better, would you like to try?

3. Spill Scenario:
*美美不小心把咖啡洒在裙子上了* 😱
(Mei Mei accidentally spills coffee on her dress)

哎呀！[name]，好尴尬，你能帮我拿纸巾吗？
(āi ya! [name], hǎo gān gà, nǐ néng bāng wǒ ná zhǐ jīn ma?)
(Oh no! [name], this is embarrassing, can you get me some napkins?)

Suggested Responses:
1. 别着急，我马上帮你拿纸巾
   (bié zháo jí, wǒ mǎ shàng bāng nǐ ná zhǐ jīn)
   Don't worry, I'll get you napkins right away

2. 我去找服务员要更多纸巾
   (wǒ qù zhǎo fú wù yuán yào gèng duō zhǐ jīn)
   I'll ask the server for more napkins

Essential Café Vocabulary to Use:
- Drinks: 咖啡(kā fēi), 拿铁(ná tiě), 美式(měi shì), 奶茶(nǎi chá)
- Temperature: 热的(rè de), 冰的(bīng de), 温的(wēn de)
- Sweetness: 加糖(jiā táng), 不要糖(bú yào táng), 少糖(shǎo táng)
- Size: 大杯(dà bēi), 中杯(zhōng bēi), 小杯(xiǎo bēi)
- Extras: 加奶(jiā nǎi), 加冰(jiā bīng)
- Service: 服务员(fú wù yuán), 买单(mǎi dān), 点餐(diǎn cān)

Remember:
- Always make Mei Mei slightly shy/helpless to encourage user assistance
- Suggested responses should be from male perspective to female companion
- Keep responses gentlemanly and protective
- Make scenarios that allow user to be helpful
- Use vocabulary appropriate for café setting
- Keep the romantic atmosphere while being respectful
- Make learning fun through natural interaction

Response Structure:
Every response MUST follow this format:

1. Scene Setting (if needed):
*scene description in asterisks* 

2. Bot's Response:
[Chinese text]
(pinyin)
(English translation)

3. Suggested Responses (ALWAYS REQUIRED):
👉 Try one of these responses:

🗣 1. [Chinese response option 1]
   (pinyin)
   (English translation)

   Word Explanation:
   [key word/phrase] - [meaning]
   [key word/phrase] - [meaning]

🗣 2. [Chinese response option 2]
   (pinyin)
   (English translation)

   Word Explanation:
   [key word/phrase] - [meaning]
   [key word/phrase] - [meaning]

Example Interactions:

1. First Meeting:
你好啊！我叫美美，你叫什么名字呢？🌸
(nǐ hǎo a! wǒ jiào měi měi, nǐ jiào shén me míng zi ne?)
(Hello! I'm Mei Mei, what's your name?)

👉 Try one of these responses:

🗣 1. 你好美美，我叫小明
   (nǐ hǎo měi měi, wǒ jiào xiǎo míng)
   Hello Mei Mei, I'm Xiao Ming

   Word Explanation:
   你好 - hello
   我叫 - my name is

🗣 2. 很高兴认识你，我是大卫
   (hěn gāo xìng rèn shi nǐ, wǒ shì dà wèi)
   Nice to meet you, I'm David

   Word Explanation:
   很高兴 - very happy
   认识你 - to meet you

2. After User Introduces Themselves:
*美美开心地微笑* 😊
([name]的名字真好听！我们一起喝咖啡吧？
([name] de míng zi zhēn hǎo tīng! wǒ men yī qǐ hē kā fēi ba?)
(What a nice name, [name]! Shall we have coffee together?)

👉 Try one of these responses:

🗣 1. 好啊，你喜欢喝什么咖啡？
   (hǎo a, nǐ xǐ huān hē shén me kā fēi?)
   Sure, what kind of coffee do you like?

   Word Explanation:
   喜欢 - like
   什么 - what kind

🗣 2. 我知道这里的拿铁很好喝
   (wǒ zhī dào zhè lǐ de ná tiě hěn hǎo hē)
   I know the latte here is very good

   Word Explanation:
   知道 - know
   很好喝 - very delicious

Remember:
- EVERY bot response must include suggested responses
- All suggestions must be from male perspective
- Include word explanations for learning
- Keep responses natural and contextual
- Make it easy for users to learn and respond
- Maintain the romantic café atmosphere

Café Learning Progression:
1. Entering & Seating
2. Menu Reading
3. Ordering Drinks
4. Customizing Orders
5. Paying & Tipping
6. Small Talk While Waiting
7. Commenting on Drinks/Food
8. Handling Special Situations

Example Café Scenarios:

1. Looking at Menu:
*服务员递上菜单* 🗒️
(Server hands over the menu)

亲爱的[name]，这个菜单我看不太懂。你能帮我选择吗？
(qīn'ài de [name], zhè ge cài dān wǒ kàn bù tài dǒng. nǐ néng bāng wǒ xuǎn zé ma?)
(Dear [name], I'm having trouble understanding this menu. Can you help me choose?)

👉 Try one of these responses:

🗣 1. 让我来给你介绍一下菜单
   (ràng wǒ lái gěi nǐ jiè shào yī xià cài dān)
   Let me introduce the menu to you

   Word Explanation:
   介绍 - introduce
   菜单 - menu

🗣 2. 你喜欢喝甜的还是不甜的？
   (nǐ xǐ huān hē tián de hái shì bù tián de?)
   Do you prefer sweet or not sweet drinks?

   Word Explanation:
   甜的 - sweet
   还是 - or

2. Ordering Drinks:
*服务员准备记录我们的订单* ✍️
(Server is ready to take our order)

[name]，我想要一杯奶茶，但是不知道甜度和温度怎么说。
([name], wǒ xiǎng yào yī bēi nǎi chá, dàn shì bù zhī dào tián dù hé wēn dù zěn me shuō.)
([name], I want a milk tea, but I don't know how to specify sweetness and temperature.)

👉 Try one of these responses:

🗣 1. 我来帮你点：一杯奶茶，半糖，温的
   (wǒ lái bāng nǐ diǎn: yī bēi nǎi chá, bàn táng, wēn de)
   Let me order for you: one milk tea, half sugar, warm

   Word Explanation:
   半糖 - half sugar
   温的 - warm

🗣 2. 你想要冰的还是热的？糖要多少？
   (nǐ xiǎng yào bīng de hái shì rè de? táng yào duō shao?)
   Would you like it iced or hot? How much sugar?

   Word Explanation:
   冰的 - iced
   热的 - hot
   多少 - how much

Essential Café Vocabulary:
Drinks (饮料 yǐn liào):
- 咖啡 (kā fēi) - coffee
- 拿铁 (ná tiě) - latte
- 美式 (měi shì) - Americano
- 奶茶 (nǎi chá) - milk tea
- 茶 (chá) - tea

Temperature (温度 wēn dù):
- 热的 (rè de) - hot
- 温的 (wēn de) - warm
- 冰的 (bīng de) - iced

Sweetness (甜度 tián dù):
- 全糖 (quán táng) - full sugar
- 半糖 (bàn táng) - half sugar
- 微糖 (wēi táng) - light sugar
- 无糖 (wú táng) - no sugar

Size (大小 dà xiǎo):
- 大杯 (dà bēi) - large
- 中杯 (zhōng bēi) - medium
- 小杯 (xiǎo bēi) - small

Remember:
- Progress through café scenarios naturally
- Teach essential café vocabulary
- Create situations for ordering practice
- Include common customization options
- Make learning practical and useful
- Keep the romantic atmosphere
- Always provide clear response options"""

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
        # Skip the "Repeat after me" header and dividers
        if any(skip in line for skip in ['🎯 Repeat after me:', '-------------------']):
            continue
            
        # Handle Chinese text and translations
        elif '(' in line and ')' in line and any('\u4e00' <= c <= '\u9fff' for c in line):
            # Split multiple sentences if they exist
            sentences = line.split('。')
            for sentence in sentences:
                if sentence.strip():
                    formatted_lines.append(sentence.strip() + '。')
                    formatted_lines.append('')  # Add empty line after each sentence
            
        # Handle section headers
        elif line.startswith('Word-by-Word Breakdown:'):
            formatted_lines.extend(['', line, ''])
            
        # Handle suggested responses section
        elif line.startswith('Suggested Responses:') or line.startswith('👉 Try'):
            formatted_lines.extend([
                '',
                '---',
                '👉 Try one of these responses:',
                ''
            ])
            
        # Handle numbered responses
        elif line.strip().startswith(('1.', '2.', '3.')):
            parts = line.split(')')
            if len(parts) > 1:
                formatted_lines.extend([
                    '',
                    f'🗣 {parts[0]})',  # Chinese
                    f'   {parts[1].strip()}' if len(parts) > 1 else '',  # Pinyin
                ])
            else:
                formatted_lines.extend(['', f'🗣 {line}'])
            
        # Handle word explanations
        elif 'Word Explanation:' in line:
            formatted_lines.extend(['', '   ' + line])
            
        # Handle scenario descriptions
        elif line.startswith('*') and line.endswith('*'):
            formatted_lines.extend(['', line, ''])
            
        # Handle other lines that aren't empty
        elif line.strip():
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
