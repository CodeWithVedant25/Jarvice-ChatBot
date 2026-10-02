import speech_recognition as sr
import os
import webbrowser
import datetime
import threading
import tkinter as tk
from tkinter import scrolledtext
import subprocess
import signal

from ollama import chat


# ============================================================
# JARVIS AI - VOICE + KEYBOARD + PAUSE/RESUME
# ============================================================


# ============================================================
# GLOBAL VARIABLES
# ============================================================

speech_process = None
speech_paused = False

speech_lock = threading.Lock()


# ============================================================
# SPEECH RECOGNIZER
# ============================================================

recognizer = sr.Recognizer()

recognizer.pause_threshold = 0.6
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True


# ============================================================
# TEXT TO SPEECH
# ============================================================

def say(text):

    global speech_process
    global speech_paused

    def speak():

        global speech_process
        global speech_paused

        try:

            # Stop previous speech if still running
            with speech_lock:

                if speech_process is not None:

                    try:
                        speech_process.terminate()
                        speech_process.wait(timeout=1)
                    except Exception:
                        pass

                    speech_process = None

                speech_paused = False

                # Start espeak
                speech_process = subprocess.Popen(
                    ["espeak", str(text)]
                )

            update_status("● SPEAKING...")

            # Wait until speech finishes
            speech_process.wait()

            with speech_lock:

                speech_process = None
                speech_paused = False

            root.after(
                0,
                lambda: pause_button.config(
                    text="⏸  PAUSE"
                )
            )

            update_status("● READY")

        except Exception as e:

            print(
                "TTS Error:",
                e
            )

            with speech_lock:

                speech_process = None
                speech_paused = False

            update_status("● READY")

    threading.Thread(
        target=speak,
        daemon=True
    ).start()


# ============================================================
# PAUSE / RESUME SPEECH
# ============================================================

def toggle_pause():

    global speech_process
    global speech_paused

    with speech_lock:

        if speech_process is None:

            return

        try:

            if not speech_paused:

                # Pause espeak process
                speech_process.send_signal(
                    signal.SIGSTOP
                )

                speech_paused = True

                pause_button.config(
                    text="▶  RESUME"
                )

                update_status(
                    "● PAUSED"
                )

                print(
                    "Speech paused."
                )

            else:

                # Resume espeak process
                speech_process.send_signal(
                    signal.SIGCONT
                )

                speech_paused = False

                pause_button.config(
                    text="⏸  PAUSE"
                )

                update_status(
                    "● SPEAKING..."
                )

                print(
                    "Speech resumed."
                )

        except Exception as e:

            print(
                "Pause Error:",
                e
            )


# ============================================================
# OLLAMA AI
# ============================================================

def ask_ai(question):

    try:

        response = chat(
            model="llama3.2:1b",
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        return response["message"]["content"]

    except Exception as e:

        print(
            "Ollama Error:",
            e
        )

        return (
            "Sorry, I could not connect to Ollama. "
            "Please make sure Ollama is running."
        )


# ============================================================
# ADD MESSAGE TO CHAT
# ============================================================

def add_message(sender, message):

    root.after(
        0,
        lambda: insert_message(
            sender,
            message
        )
    )


def insert_message(sender, message):

    chat_box.config(
        state=tk.NORMAL
    )

    if sender == "You":

        chat_box.insert(
            tk.END,
            "\nYOU\n",
            "user_title"
        )

        chat_box.insert(
            tk.END,
            message + "\n",
            "user_message"
        )

    else:

        chat_box.insert(
            tk.END,
            "\nJARVIS\n",
            "jarvis_title"
        )

        chat_box.insert(
            tk.END,
            message + "\n",
            "jarvis_message"
        )

    chat_box.config(
        state=tk.DISABLED
    )

    chat_box.see(
        tk.END
    )


# ============================================================
# STATUS
# ============================================================

def update_status(text):

    root.after(
        0,
        lambda: status_label.config(
            text=text
        )
    )


# ============================================================
# SPEECH RECOGNITION
# ============================================================

def takeCommand():

    update_status(
        "● LISTENING..."
    )

    try:

        with sr.Microphone() as source:

            print(
                "Listening..."
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

        update_status(
            "● PROCESSING..."
        )

        print(
            "Recognizing..."
        )

        query = recognizer.recognize_google(
            audio,
            language="en-IN"
        )

        print(
            "You said:",
            query
        )

        return query.lower()

    except sr.WaitTimeoutError:

        print(
            "No speech detected."
        )

        update_status(
            "● READY"
        )

        return ""

    except sr.UnknownValueError:

        print(
            "Could not understand."
        )

        update_status(
            "● READY"
        )

        return ""

    except sr.RequestError:

        print(
            "Google Speech Recognition service unavailable."
        )

        update_status(
            "● READY"
        )

        return ""

    except Exception as e:

        print(
            "Speech Error:",
            e
        )

        update_status(
            "● READY"
        )

        return ""


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(query):

    query = query.strip().lower()

    if query == "":

        update_status(
            "● READY"
        )

        return

    # Show user message
    add_message(
        "You",
        query
    )


    # ========================================================
    # OPEN YOUTUBE
    # ========================================================

    if "open youtube" in query:

        answer = (
            "Opening YouTube."
        )

        add_message(
            "Jarvis",
            answer
        )

        say(
            answer
        )

        webbrowser.open(
            "https://www.youtube.com"
        )


    # ========================================================
    # HOW ARE YOU
    # ========================================================

    elif "how are you" in query:

        answer = (
            "I am fine. Thank you for asking."
        )

        add_message(
            "Jarvis",
            answer
        )

        say(
            answer
        )


    # ========================================================
    # NAME
    # ========================================================

    elif (
        "what is your name" in query
        or "who are you" in query
    ):

        answer = (
            "My name is Jarvis. "
            "I am your AI personal assistant."
        )

        add_message(
            "Jarvis",
            answer
        )

        say(
            answer
        )


    # ========================================================
    # PLAY MUSIC
    # ========================================================

    elif "play music" in query:

        music_path = (
            "/home/hp/Downloads/"
            "verclub_music-future-beat-music-608978.mp3"
        )

        if os.path.exists(
            music_path
        ):

            answer = (
                "Playing music."
            )

            add_message(
                "Jarvis",
                answer
            )

            say(
                answer
            )

            os.system(
                f'xdg-open "{music_path}"'
            )

        else:

            error_message = (
                "Sorry, I could not find "
                "the music file."
            )

            add_message(
                "Jarvis",
                error_message
            )

            say(
                error_message
            )


    # ========================================================
    # TIME
    # ========================================================

    elif (
        "what is the time" in query
        or "tell me the time" in query
        or "current time" in query
    ):

        current_time = datetime.datetime.now().strftime(
            "%I:%M %p"
        )

        answer = (
            f"The current time is {current_time}."
        )

        add_message(
            "Jarvis",
            answer
        )

        say(
            answer
        )


    # ========================================================
    # DATE
    # ========================================================

    elif (
        "what is today's date" in query
        or "what is the date" in query
        or "today's date" in query
    ):

        current_date = datetime.datetime.now().strftime(
            "%d %B %Y"
        )

        answer = (
            f"Today's date is {current_date}."
        )

        add_message(
            "Jarvis",
            answer
        )

        say(
            answer
        )


    # ========================================================
    # EXIT
    # ========================================================

    elif (
        "exit" in query
        or "quit" in query
        or "goodbye" in query
    ):

        answer = (
            "Goodbye. Have a nice day."
        )

        add_message(
            "Jarvis",
            answer
        )

        say(
            answer
        )

        root.after(
            1800,
            root.destroy
        )

        return


    # ========================================================
    # OLLAMA AI
    # ========================================================

    else:

        update_status(
            "● THINKING..."
        )

        print(
            "Thinking..."
        )

        answer = ask_ai(
            query
        )

        print(
            "Jarvis:",
            answer
        )

        add_message(
            "Jarvis",
            answer
        )

        say(
            answer
        )


    update_status(
        "● READY"
    )


# ============================================================
# VOICE INPUT
# ============================================================

def start_listening():

    threading.Thread(
        target=listen_and_process,
        daemon=True
    ).start()


def listen_and_process():

    query = takeCommand()

    if query:

        process_command(
            query
        )


# ============================================================
# KEYBOARD INPUT
# ============================================================

def send_text():

    query = input_entry.get().strip()

    if query == "":
        return

    # Clear input box
    input_entry.delete(
        0,
        tk.END
    )

    # Process in background
    threading.Thread(
        target=process_command,
        args=(query,),
        daemon=True
    ).start()


# ============================================================
# PRESS ENTER
# ============================================================

def enter_pressed(event):

    send_text()


# ============================================================
# GUI
# ============================================================

root = tk.Tk()

root.title(
    "JARVIS AI"
)

root.geometry(
    "1100x700"
)

root.minsize(
    900,
    600
)

root.configure(
    bg="#05070d"
)


# ============================================================
# TOP BAR
# ============================================================

top_frame = tk.Frame(
    root,
    bg="#080b14",
    height=70
)

top_frame.pack(
    fill="x"
)

top_frame.pack_propagate(
    False
)


title_label = tk.Label(
    top_frame,
    text="J A R V I S",
    font=(
        "Helvetica",
        25,
        "bold"
    ),
    fg="#00e5ff",
    bg="#080b14"
)

title_label.pack(
    side="left",
    padx=30
)


subtitle_label = tk.Label(
    top_frame,
    text="AI PERSONAL ASSISTANT",
    font=(
        "Helvetica",
        10
    ),
    fg="#778899",
    bg="#080b14"
)

subtitle_label.pack(
    side="left",
    padx=5
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    top_frame,
    text="● READY",
    font=(
        "Helvetica",
        11,
        "bold"
    ),
    fg="#00ff99",
    bg="#080b14"
)

status_label.pack(
    side="right",
    padx=30
)


# ============================================================
# MAIN FRAME
# ============================================================

main_frame = tk.Frame(
    root,
    bg="#05070d"
)

main_frame.pack(
    fill="both",
    expand=True
)


# ============================================================
# LEFT SIDE
# ============================================================

left_frame = tk.Frame(
    main_frame,
    bg="#05070d",
    width=420
)

left_frame.pack(
    side="left",
    fill="y"
)

left_frame.pack_propagate(
    False
)


core_title = tk.Label(
    left_frame,
    text="JARVIS CORE",
    font=(
        "Helvetica",
        16,
        "bold"
    ),
    fg="#00e5ff",
    bg="#05070d"
)

core_title.pack(
    pady=(35, 10)
)


# ============================================================
# AI CORE
# ============================================================

canvas = tk.Canvas(
    left_frame,
    width=360,
    height=360,
    bg="#05070d",
    highlightthickness=0
)

canvas.pack(
    pady=5
)


canvas.create_oval(
    40,
    40,
    320,
    320,
    outline="#123c55",
    width=3
)

canvas.create_oval(
    65,
    65,
    295,
    295,
    outline="#075a70",
    width=3
)

canvas.create_oval(
    90,
    90,
    270,
    270,
    outline="#0086a3",
    width=3
)

canvas.create_oval(
    120,
    120,
    240,
    240,
    outline="#00e5ff",
    width=4
)


# ============================================================
# CENTER
# ============================================================

canvas.create_oval(
    145,
    145,
    215,
    215,
    fill="#00e5ff",
    outline=""
)

canvas.create_text(
    180,
    180,
    text="AI",
    font=(
        "Helvetica",
        18,
        "bold"
    ),
    fill="#05070d"
)


# ============================================================
# DECORATIVE LINES
# ============================================================

canvas.create_line(
    180,
    20,
    180,
    80,
    fill="#00e5ff",
    width=2
)

canvas.create_line(
    180,
    280,
    180,
    340,
    fill="#00e5ff",
    width=2
)

canvas.create_line(
    20,
    180,
    80,
    180,
    fill="#00e5ff",
    width=2
)

canvas.create_line(
    280,
    180,
    340,
    180,
    fill="#00e5ff",
    width=2
)


# ============================================================
# MICROPHONE BUTTON
# ============================================================

mic_button = tk.Button(
    left_frame,
    text="🎙  START LISTENING",
    command=start_listening,
    font=(
        "Helvetica",
        14,
        "bold"
    ),
    fg="#05070d",
    bg="#00e5ff",
    activebackground="#00bcd4",
    activeforeground="#ffffff",
    relief="flat",
    cursor="hand2",
    padx=20,
    pady=12
)

mic_button.pack(
    pady=10
)


# ============================================================
# PAUSE / RESUME BUTTON
# ============================================================

pause_button = tk.Button(
    left_frame,
    text="⏸  PAUSE",
    command=toggle_pause,
    font=(
        "Helvetica",
        12,
        "bold"
    ),
    fg="#ffffff",
    bg="#1b263b",
    activebackground="#263859",
    activeforeground="#ffffff",
    relief="flat",
    cursor="hand2",
    padx=25,
    pady=10
)

pause_button.pack(
    pady=5
)


# ============================================================
# RIGHT SIDE
# ============================================================

right_frame = tk.Frame(
    main_frame,
    bg="#080b14"
)

right_frame.pack(
    side="right",
    fill="both",
    expand=True,
    padx=(5, 25),
    pady=25
)


# ============================================================
# CHAT TITLE
# ============================================================

chat_title = tk.Label(
    right_frame,
    text="CONVERSATION",
    font=(
        "Helvetica",
        16,
        "bold"
    ),
    fg="#00e5ff",
    bg="#080b14"
)

chat_title.pack(
    anchor="w",
    padx=20,
    pady=(15, 5)
)


# ============================================================
# CHAT BOX
# ============================================================

chat_box = scrolledtext.ScrolledText(
    right_frame,
    wrap=tk.WORD,
    font=(
        "Helvetica",
        12
    ),
    bg="#05070d",
    fg="#d8faff",
    insertbackground="#00e5ff",
    relief="flat",
    padx=20,
    pady=15
)

chat_box.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


# ============================================================
# CHAT TAGS
# ============================================================

chat_box.tag_config(
    "user_title",
    foreground="#00e5ff",
    font=(
        "Helvetica",
        10,
        "bold"
    )
)

chat_box.tag_config(
    "user_message",
    foreground="#ffffff"
)

chat_box.tag_config(
    "jarvis_title",
    foreground="#00ff99",
    font=(
        "Helvetica",
        10,
        "bold"
    )
)

chat_box.tag_config(
    "jarvis_message",
    foreground="#d8faff"
)


chat_box.config(
    state=tk.DISABLED
)


# ============================================================
# KEYBOARD INPUT AREA
# ============================================================

input_frame = tk.Frame(
    right_frame,
    bg="#080b14"
)

input_frame.pack(
    fill="x",
    padx=15,
    pady=(0, 15)
)


# ============================================================
# TEXT INPUT
# ============================================================

input_entry = tk.Entry(
    input_frame,
    font=(
        "Helvetica",
        13
    ),
    bg="#05070d",
    fg="#ffffff",
    insertbackground="#00e5ff",
    relief="flat"
)

input_entry.pack(
    side="left",
    fill="x",
    expand=True,
    ipady=12,
    padx=(0, 10)
)


input_entry.bind(
    "<Return>",
    enter_pressed
)


# ============================================================
# SEND BUTTON
# ============================================================

send_button = tk.Button(
    input_frame,
    text="SEND",
    command=send_text,
    font=(
        "Helvetica",
        11,
        "bold"
    ),
    fg="#05070d",
    bg="#00e5ff",
    activebackground="#00bcd4",
    activeforeground="#ffffff",
    relief="flat",
    cursor="hand2",
    padx=20,
    pady=8
)

send_button.pack(
    side="right"
)


# ============================================================
# BOTTOM BAR
# ============================================================

bottom_frame = tk.Frame(
    root,
    bg="#080b14",
    height=45
)

bottom_frame.pack(
    fill="x"
)

bottom_frame.pack_propagate(
    False
)


model_label = tk.Label(
    bottom_frame,
    text="MODEL: llama3.2:1b",
    font=(
        "Helvetica",
        9
    ),
    fg="#778899",
    bg="#080b14"
)

model_label.pack(
    side="left",
    padx=25
)


time_label = tk.Label(
    bottom_frame,
    text="",
    font=(
        "Helvetica",
        9
    ),
    fg="#778899",
    bg="#080b14"
)

time_label.pack(
    side="right",
    padx=25
)


# ============================================================
# LIVE CLOCK
# ============================================================

def update_clock():

    current_time = datetime.datetime.now().strftime(
        "%d %B %Y  |  %I:%M:%S %p"
    )

    time_label.config(
        text=current_time
    )

    root.after(
        1000,
        update_clock
    )


# ============================================================
# WELCOME MESSAGE
# ============================================================

welcome = (
    "Hello, I am Jarvis. "
    "You can speak to me using the microphone "
    "or type your message below."
)

add_message(
    "Jarvis",
    welcome
)

say(
    "Hello, I am Jarvis"
)


# ============================================================
# START CLOCK
# ============================================================

update_clock()


# ============================================================
# START GUI
# ============================================================

root.mainloop()