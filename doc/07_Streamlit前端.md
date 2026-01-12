# 第七章：Streamlit 前端

## 学习目标

- 了解 Streamlit 框架的特点
- 掌握 Streamlit 常用组件
- 学会构建交互式聊天界面

## 1. Streamlit 简介

### 什么是 Streamlit？

Streamlit 是一个快速构建数据应用的 Python 框架：
- 纯 Python 代码，无需前端知识
- 自动响应式布局
- 内置丰富组件

### Hello World

```python
import streamlit as st

st.title("Hello Streamlit!")
st.write("这是我的第一个 Streamlit 应用")
```

运行：
```bash
streamlit run app.py
```

## 2. 核心概念

### 重新运行机制

Streamlit 的特点：**每次用户交互都会重新运行整个脚本**

```python
import streamlit as st

st.write("这行每次都会执行")

if st.button("点击我"):
    st.write("按钮被点击了！")  # 只在点击时显示
```

### Session State

使用 `st.session_state` 在交互间保存状态：

```python
# 初始化
if "count" not in st.session_state:
    st.session_state.count = 0

# 使用
if st.button("加一"):
    st.session_state.count += 1

st.write(f"当前计数: {st.session_state.count}")
```

## 3. 聊天组件

### chat_message

显示聊天消息：

```python
with st.chat_message("user"):
    st.write("你好！")

with st.chat_message("assistant"):
    st.write("您好，有什么可以帮助您的？")
```

### chat_input

聊天输入框：

```python
if prompt := st.chat_input("请输入消息"):
    st.write(f"你说: {prompt}")
```

## 4. 完整聊天应用示例

```python
import streamlit as st

st.title("聊天机器人")

# 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请输入"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # 生成回复
    reply = f"收到: {prompt}"
    
    with st.chat_message("assistant"):
        st.write(reply)
    
    # 保存回复
    st.session_state.messages.append({"role": "assistant", "content": reply})
```

## 5. 侧边栏和布局

### 侧边栏

```python
with st.sidebar:
    st.header("设置")
    option = st.selectbox("选择模型", ["GPT-4", "Claude"])
```

### 列布局

```python
col1, col2 = st.columns(2)

with col1:
    st.write("左侧内容")

with col2:
    st.write("右侧内容")
```

## 6. 自定义样式

```python
st.markdown("""
<style>
.main-header {
    font-size: 2rem;
    color: #1E88E5;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">标题</h1>', unsafe_allow_html=True)
```

## 知识点总结

| 概念 | 说明 |
|------|------|
| st.session_state | 跨交互保存状态 |
| st.chat_message | 聊天消息组件 |
| st.chat_input | 聊天输入框 |
| st.sidebar | 侧边栏 |
| st.columns | 列布局 |

## 项目完成

恭喜你完成了 SmartVoyage 项目的学习！

现在你已经掌握了：
- ✅ Python 虚拟环境和配置管理
- ✅ MySQL 数据库设计和操作
- ✅ Web API 调用和数据爬取
- ✅ LLM 和 Prompt Engineering
- ✅ MCP 协议和工具集成
- ✅ A2A 协议和多代理协作
- ✅ Streamlit 前端开发

开始运行你的智能旅行助手吧！🚀
