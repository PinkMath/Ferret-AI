<div align="center">
  <img src="./static/img/icon.jpg" height="300px" width="300px">

  # 🦦 Ferret AI
  ### Local • Privacy-First • Developer-Focused AI Assistant
</div>

---

## 🚀 What is Ferret AI?

**Ferret AI** is a fully local, privacy-first coding assistant powered by `deepseek-coder:6.7b` via Ollama.

No cloud.  
No API keys.  
No telemetry.  

Just fast, offline AI designed for developers.

Optimized for:
- 🇧🇷 Portuguese (PT-BR)
- 🇺🇸 English (EN-US) ~> (mainly language)

By default, it returns properly formatted code unless explanations are explicitly requested.

---

## 🎥 Demo

### App Interface
https://github.com/user-attachments/assets/3003f325-2567-4dff-b7d6-67a3f7c21d15

### Terminal Interface
https://github.com/user-attachments/assets/e60a5257-e817-43ec-a748-0f1f58f922b7

### Log Save
https://github.com/user-attachments/assets/681d6de7-59aa-464c-b2cd-8db9d6ecbaef

---

## ✨ Features

- 🖥 100% Local AI (runs entirely on your machine)
- 🔐 Privacy-first – no external APIs
- 🤖 Powered by DeepSeek-Coder 6.7B
- 📦 Automatic model detection & download
- 🎨 Color-coded terminal interface
- 🌎 Multi-language support (PT-BR & EN-US)
- 💻 Built for coding, snippets & dev assistance
- 🧠 Uses Ollama CLI for model management
- 📃Conversation_log auto-save


---

## ⚡ Quick Start (Recommended)

```bash
git clone https://github.com/PinkMath/Ferret-AI.git
cd Ferret-AI
python installer.py
```

> ⚠ This installer automatically checks dependencies, installs Ollama if needed (Linux), and downloads the deepseek-coder:6.7b model.

- Once installed;
```bash
python app.py
```

- Or terminal mode:
```bash
python terminalAI/main.py
```

---

# 🛠 Installation

## Option 1 — Installer (In Development)

```bash
git clone https://github.com/PinkMath/Ferret-AI.git
cd Ferret-AI
python installer.py
```

### The installer will:
- ✔ Check Python version
- ✔ Install `requests` if missing
- ✔ Check if Ollama CLI is installed
- ✔ Auto-install Ollama (Linux)
- ✔ Prompt manual install (Windows)
- ✔ Pull `deepseek-coder:6.7b` if missing

Run the app after installation:

```bash
python app.py
```

Terminal mode:

```bash
python terminalAI/main.py
```

---

## Option 2 — Manual Installation

### Step 1 — Install Python (3.8+)

**Linux (apt):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Linux (pacman):**
```bash
sudo pacman -Sy
sudo pacman -S python python-pip
```

**Windows:**  
Download from: https://www.python.org/downloads/

---

### Step 2 — Install Dependencies

```bash
pip install requests flask pyperclip
```

---

### Step 3 — Install Ollama CLI

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**  
Download the official installer:  
https://ollama.com/download/windows  

Ensure `ollama.exe` is in your PATH.

---

### Step 4 — Pull the Model

```bash
ollama pull deepseek-coder:6.7b
```

---

### Step 5 — Run Ferret AI

```bash
python app.py
```

Or terminal mode:

```bash
python terminalAI/main.py
```

---

# 💻 Usage
> ⚠ These commands only works in the terminal-mode (terminalAI/main.py)!!!

<div align="center">

Commands | Shortcuts | Combo | Exec
| --- | --- | --- | --- |
/exit | none | none | Quit
/clear | none | none | Clean the chat
/code | none | none | Allow paste codes
/copy <num> | none | none | Copy the codes that the AI sent
/help | /h | none | Show  the commands
/file {path} | /f {path} | /f --summary {path} <br/> /f --explain {path} <br/> /f --refactor {path} | The AI reads that file
/project {combo} {dir} | /p {combo} {dir} | /p add {dir} <br/> /p remove <br/> /p list <br/> /p ask {question} | The AI reads a whole folder
/resetlog | /rl | none | Rebuild the folder and the log file
</div>

---

# 🧩 Tech Stack

- Python
- Ollama
- DeepSeek-Coder 6.7B
- Flask
- Requests

---

# 🐛 Troubleshooting

**Missing `requests` error**
```bash
pip install requests
```

**Ollama CLI not found**
- Ensure it is installed
- Ensure it is added to PATH

**AI not running (Windows)**
- Ensure the Ollama's running in the background

**Model missing**
```bash
ollama pull deepseek-coder:6.7b
```

**App not running**
- Ensure Python 3.8+
- Ensure virtual environment is activated (if using venv)

---

# 🛣 Roadmap

- [ ] GUI improvements
- [ ] Model selector support
- [ ] Config file system
- [ ] Plugin architecture
- [ ] Performance optimizations

---

# 🎨 Credits - Art

☁️ Made by Cloud

---

⭐ If you like the project, consider starring the repo!
