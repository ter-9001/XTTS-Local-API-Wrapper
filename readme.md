
## 🚀 XTTS Local API Wrapper

This is a simple **API Wrapper** project in Python designed to integrate the _Text-to-Speech_ (TTS) functionality of the XTTS-v2 model into your projects, **by leveraging an existing local installation** of the [XTTS-WebUI](https://github.com/daswer123/xtts-webui).

The main advantage of this wrapper is that it allows you to use the virtual environment (`venv`) and the models already configured in your XTTS installation. It robustly manages the audio processing in the _background_ (text splitting, part generation, and merging).

### ✨ Features

-   **Installation Reuse:** Uses the Python environment (`venv/bin/python3`) and model weights (`models/v2.0.2/`) from your local XTTS installation (Default configuration in [XTTS-WebUI](https://github.com/daswer123/xtts-webui) ).
    
-   **Robust Processing:** Splits long texts into smaller chunks, generates audio for each part, and merges them back together, adding short pauses between chunks for naturalness.
    
-   **Simplified Configuration:** Stores the path to your XTTS installation in a `database.json` file, prompting you for it only on the first run.
    
-   **Full Control:** Allows control over the text, voice sample file (`sample_file`), language (`language`), and speed (`speed`) via command line or API calls.
    

----------

## ⚙️ Initial Setup

For this project to work, you must have the XTTS-WebUI repository installed and configured on your machine, matching the expected folder structure.

### 1. Requirements

1.  **XTTS-WebUI Installed:** You must have a functional installation of XTTS-WebUI (e.g., `xtts-webui-v1_0-portable/webui/`).
    
2.  **Python Modules:**
    
    Bash
    
    ```
    pip install pydub
    # If you are using 'core.py' from your virtual environment, 
    # ensure that all XTTS dependencies are installed there.
    
    ```
    
3.  **FFmpeg:** `pydub` (used for merging audios) requires FFmpeg to be installed and accessible in your system's `PATH`.
    

### 2. Expected Folder Structure

The wrapper expects the root path of your XTTS installation to contain the following structure:

```
[xtts_folder]
├── venv/                      # Where the Python virtual environment is located (venv/bin/python3)
└── models/
    └── v2.0.2/
        ├── config.json
        ├── vocab.json
        └── model.pth          # The main checkpoint file

```

## 💻 How to Use

This wrapper works best when executed as a _sub-process_, calling a script (`core.py`) within your XTTS environment.

### 1. File Preparation

Download all this project and keep the files together. 

Ensure you have the __four__ main files in your project API:

-   `make_audio.py` (Contains the functions `make_audio`, `split_text_into_chunks`, `merge_audios`, `get_xtts_folder_path`, etc.)
    
-   `core.py` (The script that performs the actual TTS inference, usually derived from the XTTS inference example)exemple

- `test.py` Contains a example about how the API is used and how to integrated into your code.

- `database.json` File where is the configurations of the program ( __You will set the initiate folder on the first start up__, read next chapter  )

###  2. Path Configuration (First Run)

The first time you execute the main function (`make_audio` or the script calling it), the system will look for the `database.json` file. If the file or the `xtts_folder` key is missing, it will prompt you for the path to your XTTS folder:

1.  **Prompt:** The following message will be displayed:
    
    > **Please enter the absolute path to your webui of the XTTS installation folder (e.g., ~/my/xtts/webui):**
    
2.  **Enter the path:** Type the full path to the root folder of your __webui__ of XTTS installation (e.g., `/home/user/xtts-webui-v1_0-portable/webui`).
    
3.  **Storage:** The path will be saved in `database.json`.
    

### 2. Usage Example (Via API or Script)

You can call the `make_audio` function from your Python code, passing the required arguments.

Python

```
# Your main API code (e.g., app.py)
from make_audio import make_audio 

# --- Audio Generation Request Example ---
try:
    success = make_audio(
        text="This is a test run of the XTTS local API wrapper, providing robust text-to-speech generation.", 
        output_file="./audio_results/test_output.mp3", 
        sample_file="~/xtts-webui-v1_0-portable/webui/speakers/sample_voice.wav", 
        language='en', 
        speed=1.0, 
        max_chars=2000
    )
    if success:
        print("API successfully generated audio.")
    else:
        print("API failed to generate audio.")

except Exception as e:
    print(f"An error occurred: {e}")

```

### 3. Subprocess Execution

The wrapper uses the `generate_audio_chunk` function to execute the `core.py` script (which should be inside your XTTS, or a script you configured for this purpose) **directly** using the Python interpreter from your `venv`:

Python

```
command = [
    # Absolute path to the python binary in the XTTS venv
    /path/to/xtts/venv/bin/python3, 
    # Your inference script
    core.py, 
    # Arguments...
    "The text to be spoken",
    "output_part.mp3",
    # ...
]

subprocess.run(command, ...)

```