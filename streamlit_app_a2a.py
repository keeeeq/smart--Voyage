# -*- coding: utf-8 -*-
"""
SmartVoyage - Immersive Experience (Chinese)
"""

import streamlit as st
import requests
import uuid

# 全局配置
st.set_page_config(
    page_title="智行天下",
    layout="wide",
    page_icon="🎐",
    initial_sidebar_state="collapsed"
)

API_GATEWAY = "http://localhost:8000"

# --- 深度定制 CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Proza+Libre:wght@400;500&display=swap');

/* 重置 Streamlit 默认样式 */
.stApp {
    background-color: #fcfcfc;
    background-image: 
        radial-gradient(at 80% 0%, hsla(189,100%,56%,0.1) 0px, transparent 50%),
        radial-gradient(at 0% 50%, hsla(355,100%,93%,0.3) 0px, transparent 50%),
        radial-gradient(at 80% 50%, hsla(340,100%,76%,0.1) 0px, transparent 50%),
        radial-gradient(at 0% 100%, hsla(22,100%,77%,0.1) 0px, transparent 50%),
        radial-gradient(at 80% 100%, hsla(242,100%,70%,0.1) 0px, transparent 50%),
        radial-gradient(at 0% 0%, hsla(343,100%,76%,0.1) 0px, transparent 50%);
    font-family: 'Noto Serif SC', serif; /* 使用思源宋体 */
}

header, footer, #MainMenu {visibility: hidden;}
.block-container {
    padding-top: 0;
    padding-left: 0;
    padding-right: 0;
    max-width: 100%;
}

/* 布局容器 */
.layout-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
    padding: 60px 20px;
}

/* 标题区域 - 杂志排版 */
.header-section {
    text-align: center;
    margin-bottom: 60px;
    position: relative;
    padding-top: 40px;
}
.brand-title {
    font-family: 'Noto Serif SC', serif;
    font-size: 4.5rem;
    font-weight: 700;
    color: #2c3e50;
    letter-spacing: 0.2em; /* 增加字间距 */
    line-height: 1.2;
    margin-bottom: 15px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.05);
}
.brand-subtitle {
    font-family: 'Proza Libre', sans-serif;
    font-size: 0.9rem;
    color: #7f8c8d;
    letter-spacing: 0.4em;
    text-transform: uppercase;
    margin-top: 10px;
    font-weight: 500;
}
.divider-line {
    width: 1px;
    height: 50px;
    background: linear-gradient(to bottom, #2c3e50, transparent);
    margin: 30px auto 0;
    opacity: 0.3;
}

/* 聊天画板 */
.chat-board {
    width: 100%;
    max-width: 800px;
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 24px;
    padding: 50px;
    box-shadow: 
        0 30px 60px -15px rgba(0,0,0,0.04),
        0 0 0 1px rgba(255,255,255,0.4) inset;
    margin-bottom: 40px;
}

/* 消息样式优化 */
.msg-wrapper {
    display: flex;
    flex-direction: column;
    gap: 28px;
}

.msg-item {
    display: flex;
    gap: 20px;
    align-items: flex-start;
    animation: fadeSlideUp 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    opacity: 0;
    transform: translateY(15px);
}
@keyframes fadeSlideUp {
    to { opacity: 1; transform: translateY(0); }
}

.msg-item.user {
    flex-direction: row-reverse;
}

.avatar-box {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    color: #7f8c8d;
    border: 1px solid rgba(0,0,0,0.03);
    border-radius: 50%;
    background: rgba(255,255,255,0.8);
    font-family: 'Noto Serif SC', serif;
}

.content-box {
    max-width: 78%;
    padding-top: 2px;
}

.content-text {
    font-size: 1.05rem;
    line-height: 1.8;
    color: #444;
    font-weight: 400;
    letter-spacing: 0.02em;
}
.content-text.user {
    color: #2c3e50;
    text-align: right;
    font-weight: 500;
}

/* 快捷菜单 */
.menu-nav {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 30px;
}
.menu-link {
    font-size: 0.9rem;
    color: #95a5a6;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.3s;
    background: none;
    border: none;
    padding: 5px 10px;
    font-family: 'Noto Serif SC', serif;
    position: relative;
}
.menu-link:hover {
    color: #2c3e50;
}
.menu-link::after {
    content: '';
    position: absolute;
    width: 0;
    height: 1px;
    bottom: 0;
    left: 50%;
    background-color: #2c3e50;
    transition: all 0.3s;
}
.menu-link:hover::after {
    width: 100%;
    left: 0;
}

/* 输入框改造 */
.input-area-wrapper {
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
    position: relative;
}
.stTextInput > div > div > input {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid #dcdcdc !important;
    border-radius: 0 !important;
    padding: 15px 5px !important;
    font-size: 1.1rem !important;
    color: #2c3e50 !important;
    text-align: center;
    font-family: 'Noto Serif SC', serif !important;
    transition: border-color 0.3s;
}
.stTextInput > div > div > input:focus {
    border-color: #2c3e50 !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: #bdc3c7;
    font-style: italic;
}

/* 按钮样式覆盖 */
button[kind="primary"] { display: none; }
div.stButton > button {
    border: none;
    background: transparent;
    color: #95a5a6;
    font-size: 0.9rem;
    padding: 0;
    font-family: 'Noto Serif SC', serif;
}
div.stButton > button:hover {
    color: #2c3e50;
    background: transparent;
}
</style>
""", unsafe_allow_html=True)

# --- 逻辑层 ---

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def call_api(msg):
    try:
        res = requests.post(
            f"{API_GATEWAY}/chat",
            json={"message": msg, "session_id": st.session_state.session_id},
            timeout=30
        )
        return res.json().get("response", "系统正在维护中...")
    except:
        return "网络连接已断开，请检查服务状态。"

# --- 页面结构 ---

# 1. 顶部 Header
st.markdown("""
<div class="layout-container">
    <div class="header-section">
        <div class="brand-title">智 行 天 下</div>
        <div class="brand-subtitle">THE ART OF EXPLORATION</div>
        <div class="divider-line"></div>
    </div>
""", unsafe_allow_html=True)

# 2. 聊天展示区
st.markdown('<div class="chat-board"><div class="msg-wrapper">', unsafe_allow_html=True)

# 默认欢迎语
if not st.session_state.messages:
    st.markdown("""
    <div class="msg-item">
        <div class="avatar-box">智</div>
        <div class="content-box">
            <div class="content-text">
                午安。无论是去往巴黎的航班，还是今晚的音乐会，<br>智行 随时为您安排。
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    
    if role == "user":
        st.markdown(f"""
        <div class="msg-item user">
            <div class="avatar-box">我</div>
            <div class="content-box">
                <div class="content-text user">{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 格式化内容，处理换行
        formatted_content = content.replace("\n", "<br>")
        st.markdown(f"""
        <div class="msg-item">
            <div class="avatar-box">智</div>
            <div class="content-box">
                <div class="content-text">{formatted_content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# 3. 底部输入 & 导航
col1, col2 = st.columns([6, 1])

# 快捷菜单
st.markdown('<div class="menu-nav">', unsafe_allow_html=True)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    if st.button("东京天气"):
        prompt = "东京天气如何"
        st.session_state.messages.append({"role": "user", "content": prompt})
        resp = call_api(prompt)
        st.session_state.messages.append({"role": "assistant", "content": resp})
        st.rerun()
with col_m2:
    if st.button("巴黎航班"):
        prompt = "北京去巴黎的航班"
        st.session_state.messages.append({"role": "user", "content": prompt})
        resp = call_api(prompt)
        st.session_state.messages.append({"role": "assistant", "content": resp})
        st.rerun()
with col_m3:
    if st.button("近期演出"):
        prompt = "最近的演唱会"
        st.session_state.messages.append({"role": "user", "content": prompt})
        resp = call_api(prompt)
        st.session_state.messages.append({"role": "assistant", "content": resp})
        st.rerun()
with col_m4:
    if st.button("重新开始"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 输入框
prompt = st.chat_input("下一站去哪里？", key="main_input")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    resp = call_api(prompt)
    st.session_state.messages.append({"role": "assistant", "content": resp})
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
