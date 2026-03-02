import os
import sys
import json
import time
import random
import requests
import threading
import textwrap
from datetime import datetime
from pathlib import Path

# Internal imports from our package
from .config import CONFIG, PERSONAS, C, possible_paths
from .utils import _print_banner, _typing_indicator, _get_terminal_width
from . import FerretAIInit

# Clipboard support
try:
    import pyperclip
    CLIPBOARD_ENABLED = True
except ImportError:
    CLIPBOARD_ENABLED = False

# --- FERRET AI CLASS ---
class FerretAI(FerretAIInit):
    # --- TEXT CHUNKING ---
    def _chunk_text(self, text, size=1200, overlap=200):
        chunks, start = [], 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start += size - overlap
        return chunks

    # --- PERSONA SELECTION ---
    def _select_persona(self):
        print("\nSelect AI persona or number:")
        for i, (key, desc) in enumerate(PERSONAS.items(), start=1):
            print(f"  {i} - {key} : {desc}")
        
        choice = input("Persona/Number: ").strip().lower()

        # Map numbers to persona keys
        persona_keys = list(PERSONAS.keys())
        if choice in PERSONAS:
            selected_persona = choice
        elif choice.isdigit() and 1 <= int(choice) <= len(persona_keys):
            selected_persona = persona_keys[int(choice)-1]
        else:
            print("Invalid input, defaulting to first persona")
            selected_persona = persona_keys[0]

        # Save the description in CONFIG, but return the name
        CONFIG["persona"] = PERSONAS[selected_persona]
        self.messages.append({"role": "system", "content": CONFIG["persona"]})

        print(f"{C['ai']}Persona set: {selected_persona}{C['reset']}\n")

    # --- HELP MENU ---
    def _show_help(self):
        print(f"""
{C['brand']}{C['bold']}Ferret AI Help Menu{C['reset']}

{C['info']}Core Commands:{C['reset']}
  /help                     Show this menu
  /clear                    Reset conversation context
  /exit                     Quit application
  /code <lang>              Enter multi-line code mode
  /copy <num>               Copy AI code block by number

{C['info']}File Commands:{C['reset']}
  /f | /file <path>              Send file to AI
  /f | /file --summary <path>    Get concise summary
  /f | /file --explain <path>    Detailed explanation
  /f | /file --refactor <path>   Improve and return full code

{C['info']}Project Commands:{C['reset']}
  /p | /project add <folder>     Index project directory
  /p | /project list             Show indexed files
  /p | /project remove           Unload project
  /p | /project ask <question>   Ask question about project

{C['yellow']}Examples:{C['reset']}
  /file main.py | /f main.py
  /file --refactor app.js | /f --refactor app.js
  /project add ./my_app | /p add ./my_app
  /project ask how login works? | /p ask how login works?
""")

    
    # Clean tertminal
    def clear_terminal_full(self):
        if os.name == 'nt':
            os.system('cls')
            # ANSI escape for scrollback buffer clear (Windows Terminal supports this)
            sys.stdout.write("\033[3J")
            sys.stdout.flush()
        else:
            # Clear scrollback, move cursor home, clear screen
            sys.stdout.write("\033[3J\033[H\033[2J")
            sys.stdout.flush()

    # --- ENVIRONMENT SETUP ---
    def _setup_env(self):
        # Ensure log directory exists
        if not os.path.exists(CONFIG["log_dir"]):
            os.makedirs(CONFIG["log_dir"])

        # Clear the terminal and show banner
        self.clear_terminal_full()
        _print_banner()

        # Environment info
        print(f"{C['cyan']}─────────────────────────── Environment ───────────────────────────{C['reset']}")
        print(f"● {C['context']}Model:{C['reset']} {CONFIG['model']}")
        print(f"● {C['info']}Commands:{C['reset']} /clear {C['info']}|{C['reset']} /exit {C['info']}|{C['reset']} /code {C['info']}|{C['reset']} /copy <num> {C['info']}|{C['reset']} /help {C['info']}|{C['reset']} /resetlog")
        print(f"● {C['info']}File:{C['reset']} /file <path> {C['info']}|{C['reset']} --summary {C['info']}|{C['reset']} --explain {C['info']}|{C['reset']} --refactor")
        print(f"● {C['info']}Project:{C['reset']} /project add <dir> {C['info']}|{C['reset']} remove {C['info']}|{C['reset']} list {C['info']}|{C['reset']} ask <question>")
        print(f"● {C['context']}Logs:{C['reset']} saving to {CONFIG['log_dir']}")
        print(f"● {C['yellow']}Tip:{C['reset']} Use '/clear' to reset context without clearing logs")
        print(f"{C['cyan']}────────────────────────────────────────────────────────────────────{C['reset']}\n")

        # Friendly greeting
        greetings = [
            "Hey there! 👋 Ready to code?", 
            "What's up? 😎 Let's make some magic!", 
            "Hello, human! 🤖 Ferret AI at your service!",
            "Greetings! 🌟 How can I assist today?",
            "Hi there! 🐾 Let's get to work!"
        ]
        print(f"{C['ai']}{random.choice(greetings)}{C['reset']}\n")

    # --- LOGGING ---
    def log_interaction(self, user_text, ai_text):
        with open(self.log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{timestamp}] USER: {user_text}\n[{timestamp}] AI: {ai_text}\n{'-'*30}\n")

    # --- CONTEXT BAR ---
    def _context_bar(self, ctx_size):
        ratio = min(ctx_size / CONFIG["max_context_messages"], 1.0)
        bar_length = 12
        filled = int(bar_length * ratio)
        empty = bar_length - filled
        bar = "█" * filled + "░" * empty
        color = C['context'] if ratio <= 0.4 else C['info'] if ratio <= 0.75 else C['error']
        return f"{color}[{bar}] {int(ratio*100)}%{C['reset']}"

    # --- CODE BLOCK RENDERING ---
    def _render_code_block(self, code_text, show_gutter=True):
        lines = code_text.strip().split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        term_width = _get_terminal_width()
        gutter = f"{C['code']}│{C['reset']}"
        max_line_width = term_width - len(gutter) - 5
        wrapped_lines = []

        for line in lines:
            wrapped_lines.extend(textwrap.wrap(line, width=max_line_width) or [""])

        if show_gutter:
            for idx, line in enumerate(wrapped_lines, start=1):
                number_str = str(idx).rjust(3)
                print(f"{gutter} {number_str} {C['light_yellow']}{line.ljust(max_line_width)}{C['reset']}")
        return "\n".join(wrapped_lines)

    # --- PYTHON SYMBOL EXTRACTION ---
    def _extract_python_blocks(self, content):
        blocks = []
        lines = content.splitlines()
        current_block, current_name = [], None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                if current_block:
                    blocks.append((current_name, "\n".join(current_block)))
                    current_block = []
                current_name = stripped.split("(")[0].replace("def ", "").replace("class ", "").strip()
                current_block.append(line)
            elif current_block:
                current_block.append(line)
        if current_block:
            blocks.append((current_name, "\n".join(current_block)))
        return blocks

    def _extract_imports(self, content):
        imports = []
        for line in content.splitlines():
            if line.strip().startswith(("import ", "from ")):
                imports.append(line.strip())
        return imports

    def _score_block(self, question, block_text, block_name=None):
        score = 0
        q_words = question.lower().split()
        text = block_text.lower()
        for word in q_words:
            score += text.count(word) * 2
            if block_name and word in block_name.lower():
                score += 5
        if "traceback" in question.lower():
            score += text.count("raise") * 3
        return score

    def _detect_traceback_target(self, question):
        if "Traceback" not in question:
            return None
        lines = question.splitlines()
        for line in lines:
            if ".py" in line and "File" in line:
                try:
                    file_part = line.split('"')[1]
                    return os.path.basename(file_part)
                except:
                    pass
        return None

    # --- MAIN CHAT LOOP ---
    def chat(self):
        short_commands = {
            "/p": "/project",
            "/f": "/file",
            "/h": "/help",
            "/rl": "/resetlog"
        }
        while True:
            try:
                ctx_size = len(self.messages) - 1
                prompt = f"{self._context_bar(ctx_size)}\n{C['prompt']} λ{C['reset']} "
                first_line = input(prompt).strip()
                if not first_line:
                    continue

                # Replace short commands with full commands
                for short, full in short_commands.items():
                    if first_line.startswith(short):
                        first_line = first_line.replace(short, full, 1)
                        break

                cmd = first_line.lower()

                # --- EXIT ---
                if cmd == '/exit':
                    print(f"{C['yellow']}Signing off.{C['reset']}")
                    break

                # --- HELP ---
                if cmd == '/help':
                    self._show_help()
                    continue

                # --- REBUILD THE LOG ---
                if cmd == '/resetlog':
                    if not os.path.exists(CONFIG["log_dir"]):
                        os.makedirs(CONFIG["log_dir"])
                        print(f"\n{C['brand']}● {self.log_file} {C['ai']}~> rebuilded\n")
                    continue

                # --- CLEAR CONTEXT ---
                if cmd == '/clear':
                    self.messages = [{"role": "system", "content": CONFIG["persona"]}]
                    self.code_blocks = []
                    self._setup_env()
                    print(f"{C['brand']}🗑️ Context purged. Memory fresh.{C['reset']}\n")
                    continue

                # --- CODE MODE ---
                if cmd.startswith('/code'):
                    parts = first_line.split()
                    lang = parts[1] if len(parts) > 1 else ""

                    question = input(f"\n{C['yellow']}<Question> {C['reset']}")

                    print(f"\n{C['brand']}Entering code mode. Type '/end' to send.{C['reset']}\n")
                    lines = []
                    while True:
                        line = input(f"{C['code']}... {C['reset']}")
                        if line.strip().lower() == "/end":
                            break
                        lines.append(line)

                    if not lines:
                        print(f"{C['yellow']}No code entered.{C['reset']}")
                        continue

                    user_input = f"Question: {question}\nCode ({lang}):\n" + "\n".join(lines) + "\n"

                # --- COPY CODE BLOCK ---
                elif cmd.startswith('/copy'):
                    if len(cmd.split()) == 2 and cmd.split()[1].isdigit():
                        idx = int(cmd.split()[1]) - 1
                        if 0 <= idx < len(self.code_blocks):
                            if CLIPBOARD_ENABLED:
                                pyperclip.copy(self.code_blocks[idx])
                                print(f"{C['green']}Copied code block {idx+1} ✅{C['reset']}")
                            else:
                                print(f"{C['yellow']}pyperclip not installed.{C['reset']}")
                        else:
                            print(f"{C['yellow']}Invalid code block number.{C['reset']}")
                    else:
                        print(f"{C['yellow']}Usage: /copy <number>{C['reset']}")
                    continue

                # --- PROJECT COMMANDS ---
                elif cmd.startswith('/project'):
                    parts = first_line.split(maxsplit=2)
                    if len(parts) == 1:
                        print(f"{C['yellow']}Usage: /project add|remove|list|ask{C['reset']}")
                        continue
                    sub = parts[1]

                    # --- ADD PROJECT ---
                    if sub == "add":
                        if len(parts) < 3:
                            print(f"{C['yellow']}Usage: /project add <folder>{C['reset']}")
                            continue
                        folder = parts[2].strip('"')
                        if not os.path.isdir(folder):
                            print(f"{C['error']}Directory not found.{C['reset']}")
                            continue
                        self.project_root = folder
                        self.project_index = {}
                        self.project_chunks = []
                        self.project_blocks = []
                        self.symbol_index = {}
                        print(f"{C['info']}Indexing project with symbol extraction...{C['reset']}")
                        allowed_ext = (".py", ".js", ".jsx", ".ts", ".html", ".css", ".json", ".lua", ".c", ".cpp", ".md")
                        for root, _, files in os.walk(folder):
                            for file in files:
                                if not file.endswith(allowed_ext):
                                    continue
                                path = os.path.join(root, file)
                                rel = os.path.relpath(path, folder)
                                try:
                                    with open(path, "r", encoding="utf-8") as f:
                                        content = f.read()
                                except:
                                    continue

                                imports = self._extract_imports(content)
                                blocks = self._extract_python_blocks(content) if file.endswith(".py") else [("file_scope", content[:8000])]
                                self.project_index[rel] = {"chunks": self._chunk_text(content), "size": len(content), "blocks": blocks, "imports": imports}

                                for name, block in blocks:
                                    self.project_blocks.append((rel, block, name))
                                    if name:
                                        self.symbol_index.setdefault(name, []).append((rel, block))
                                for chunk in self.project_index[rel]["chunks"]:
                                    self.project_chunks.append((rel, chunk))

                        print(f"{C['green']}Indexed {len(self.project_index)} files, {len(self.project_blocks)} code blocks.{C['reset']}")
                        continue

                    # --- REMOVE PROJECT ---
                    elif sub == "remove":
                        self.project_root = None
                        self.project_index = {}
                        self.project_chunks = []
                        self.project_blocks = []
                        self.symbol_index = {}
                        print(f"{C['brand']}Project removed.{C['reset']}")
                        continue

                    # --- LIST PROJECT FILES ---
                    elif sub == "list":
                        if not self.project_index:
                            print(f"{C['yellow']}No project loaded.{C['reset']}")
                        else:
                            print(f"{C['info']}Project files:{C['reset']}")
                            for file in self.project_index.keys():
                                print(f" - {file}")
                        continue

                    # --- ASK PROJECT ---
                    elif sub == "ask":
                        if not self.project_blocks:
                            print(f"{C['yellow']}No project loaded.{C['reset']}")
                            continue
                        if len(parts) < 3:
                            print(f"{C['yellow']}Usage: /project ask <question>{C['reset']}")
                            continue
                        question = parts[2]
                        traceback_file = self._detect_traceback_target(question)
                        scored = []

                        for path, block, name in self.project_blocks:
                            score = self._score_block(question, block, name)
                            if traceback_file and traceback_file in path:
                                score += 20
                            if score > 0:
                                scored.append((score, path, block, name))

                        if not scored:
                            print(f"{C['yellow']}No strong matches found. Using top blocks.{C['reset']}")
                            scored = [(1, p, b, n) for p, b, n in self.project_blocks[:5]]

                        scored.sort(reverse=True, key=lambda x: x[0])
                        MAX_CONTEXT = 12000
                        used = 0
                        injection = ""
                        used_files = set()
                        for score, path, block, name in scored:
                            if used + len(block) > MAX_CONTEXT:
                                break
                            injection += f"\n[File: {path} | Symbol: {name} | Score: {score}]\n```\n{block}\n```\n"
                            used += len(block)
                            used_files.add(path)

                        print(f"{C['info']}Using {len(used_files)} files ({used} chars).{C['reset']}")
                        user_input = f"Answer using the relevant project code below. You can to read the files.\n{injection}\nQuestion: {question}\n"

                # --- FILE COMMANDS ---
                elif cmd.startswith('/file'):
                    parts = first_line.split()
                    if len(parts) < 2:
                        print(f"{C['yellow']}Usage: /file <path>{C['reset']}")
                        continue
                    mode, file_path = ("normal", "")
                    if parts[1].startswith("--"):
                        mode = parts[1][2:]
                        if len(parts) < 3:
                            print(f"{C['yellow']}Missing file path.{C['reset']}")
                            continue
                        file_path = parts[2]
                    else:
                        file_path = parts[1]
                    file_path = file_path.strip('"')
                    if not os.path.exists(file_path):
                        print(f"{C['error']}File not found: {file_path}{C['reset']}")
                        continue
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        print(f"{C['error']}Could not read file: {e}{C['reset']}")
                        continue
                    max_chars = 15000
                    if len(content) > max_chars:
                        print(f"{C['yellow']}File too large. Truncating to {max_chars} characters.{C['reset']}")
                        content = content[:max_chars]
                    filename = os.path.basename(file_path)
                    if mode == "summary":
                        prompt_prefix = "Provide a concise summary of this file."
                    elif mode == "explain":
                        prompt_prefix = "Explain in detail what this file does, including architecture and logic."
                    elif mode == "refactor":
                        prompt_prefix = (
                            "Refactor and improve this file. "
                            "Improve readability, structure, and performance. "
                            "Return the improved full code."
                        )
                    else:
                        prompt_prefix = f"Here is the content of file `{filename}`:"
                    user_input = f"{prompt_prefix}\n\nFile name: `{filename}`\n\n```\n{content}\n```"
                    print(f"{C['green']}Loaded file: {filename} ({len(content)} chars) | Mode: {mode}{C['reset']}")

                else:
                    user_input = first_line

                # --- SEND TO AI ---
                self.messages.append({"role": "user", "content": user_input})
                stop_event = threading.Event()
                spinner_thread = threading.Thread(target=_typing_indicator, args=(stop_event,))
                spinner_thread.start()

                try:
                    response = requests.post(
                        CONFIG["url"],
                        json={"model": CONFIG["model"], "messages": self.messages, "stream": True},
                        stream=True,
                        timeout=20
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    stop_event.set()
                    spinner_thread.join()
                    print(f"\n{C['error']}Network error: {e}{C['reset']}")
                    continue

                stop_event.set()
                spinner_thread.join()
                print(f"\n{C['ai']}•ᴗ•{C['reset']} ", end="")

                full_response = ""
                in_code_block = False
                code_buffer = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    content = chunk.get("message", {}).get("content", "")
                    full_response += content
                    while content:
                        if content.startswith("```"):
                            in_code_block = not in_code_block
                            content = content[3:]
                            if not in_code_block and code_buffer:
                                code_text = "```\n" + code_buffer + "\n```"
                                self._render_code_block(code_text)
                                self.code_blocks.append(self._render_code_block(code_text, show_gutter=False))
                                code_buffer = ""
                            continue
                        if in_code_block:
                            newline_pos = content.find("\n")
                            if newline_pos != -1:
                                code_buffer += content[:newline_pos] + "\n"
                                content = content[newline_pos+1:]
                            else:
                                code_buffer += content
                                content = ""
                        else:
                            for char in content:
                                sys.stdout.write(char)
                                sys.stdout.flush()
                                time.sleep(CONFIG["typing_speed"])
                            content = ""

                if code_buffer.strip():
                    code_text = "```\n" + code_buffer.strip() + "\n```"
                    self._render_code_block(code_text)
                    self.code_blocks.append(self._render_code_block(code_text, show_gutter=False))

                print("\n")
                self.log_interaction(user_input, full_response)
                self.messages.append({"role": "assistant", "content": full_response})

            except KeyboardInterrupt:
                print(f"\n{C['yellow']}Interrupted.{C['reset']}")
                break
            except Exception as e:
                print(f"\n{C['error']}Fault: {e}{C['reset']}\n")
# ur own AI, made by Mathus Souza, GitHub: https://github.com/PinkMath
