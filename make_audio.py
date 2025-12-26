import os
import subprocess
import tempfile
import time
from pydub import AudioSegment

import json
import os

DATABASE_FILE = "database.json"
XTTS_KEY = "xtts_folder"

def split_text_into_chunks(text, max_chars=2000):
    """
    Splits text into chunks, respecting full words and punctuation marks.
    """
    if not text or not isinstance(text, str):
        return []
    
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        
        # If not the end of the text, adjust to break at a word boundary
        if end < len(text):
            # Find the last space before the limit
            last_space = text.rfind(' ', start, end)
            
            # If a space was found, break there
            if last_space != -1 and last_space > start:
                end = last_space
            # If no space was found, look for punctuation for a better break point
            else:
                for char in ['.', '!', '?', ';', ',']:
                    last_punctuation = text.rfind(char, start, end)
                    if last_punctuation != -1:
                        end = last_punctuation + 1
                        break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end
    
    # Merge very small chunks (less than 10 chars) with the previous one
    if len(chunks) > 1:
        final_chunks = []
        for chunk in chunks:
            if len(chunk) < 10 and final_chunks:
                final_chunks[-1] = final_chunks[-1] + " " + chunk
            else:
                final_chunks.append(chunk)
        return final_chunks
    
    return chunks


def merge_audios(part_files, output_file):
    """
    Merges multiple audio files into a single one using pydub.
    """
    try:
        if not part_files:
            print("❌ No files to merge.")
            return False
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Use pydub to merge the audios
        final_audio = None
        
        for i, file in enumerate(part_files, 1):
            if not os.path.exists(file):
                print(f"❌ File not found: {file}")
                continue
            
            try:
                part_audio = AudioSegment.from_file(file)
                
                if final_audio is None:
                    final_audio = part_audio
                else:
                    # Add a small pause between chunks (0.2 seconds)
                    pause = AudioSegment.silent(duration=200)
                    final_audio = final_audio + pause + part_audio
                
                print(f"   ✅ Part {i} added ({len(part_audio)/1000:.1f}s)")
                
            except Exception as e:
                print(f"❌ Error processing part {i}: {e}")
                continue
        
        if final_audio is None:
            print("❌ No valid audio to merge.")
            return False
        
        # Export the final audio
        # Using format="mp3" and a good bitrate for quality
        final_audio.export(output_file, format="mp3", bitrate="192k")
        
        return True
        
    except Exception as e:
        print(f"❌ Error merging audios: {e}")
        return False


def make_audio(text, output_file, sample_file, language='en', speed=1.0, max_chars=2000):
    """
    Generates audio by splitting text into chunks and merging them.
    
    Args:
        text: Text to be converted to audio.
        output_file: Final output file.
        sample_file: Voice sample file.
        language: Audio language.
        speed: Speech speed.
        max_chars: Maximum characters per chunk.
    
    Returns:
        bool: True on success, False on error.
    """
    
    # 1. Split the text into chunks respecting word boundaries
    chunks = split_text_into_chunks(text, max_chars)
    
    if not chunks:
        print("❌ Empty or invalid text.")
        return False
    
    print(f"📝 Text split into {len(chunks)} chunks.")
    
    # 2. Create a temporary directory for audio parts
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Temporary directory: {temp_dir}")
        
        part_files = []
        
        # 3. Generate audio for each chunk
        for i, chunk in enumerate(chunks, 1):
            print(f"\n🎵 Generating chunk {i}/{len(chunks)}...")
            print(f"   Characters: {len(chunk)}")
            print(f"   Content: {chunk[:100]}...")
            
            part_file = os.path.join(temp_dir, f"part_{i:03d}.mp3")
            
            # Try up to 3 times for each chunk
            success = False
            for attempt in range(1, 4):
                print(f"   Attempt {attempt}/3")
                
                if generate_audio_chunk(
                    chunk, part_file, sample_file, language, speed
                ):
                    part_files.append(part_file)
                    success = True
                    break
                else:
                    time.sleep(2)  # Pause between attempts
            
            if not success:
                print(f"❌ Failed to generate chunk {i}")
                return False
        
        # 4. Merge all audios
        print(f"\n🔗 Merging {len(part_files)} audio parts...")
        
        if merge_audios(part_files, output_file):
            print(f"✅ Final audio generated: {output_file}")
            
            # Check if the final file was created
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"📊 Final size: {size} bytes")
                
                # Get duration
                try:
                    audio = AudioSegment.from_file(output_file)
                    duration = len(audio) / 1000.0
                    print(f"⏱️  Total duration: {duration:.2f} seconds")
                except:
                    pass
                
                return True
        
        return False


def generate_audio_chunk(text, output_file, sample_file, language, speed):
    """
    Generates audio for a specific chunk using the external XTTS script.
    """

    # Get the XTTS folder path from database.json
    folder_xtts = get_xtts_folder_path()

    # Expand the path (handles potential ~)
    folder_xtts_expanded = os.path.expanduser(folder_xtts)

    # 2. Construct the paths using os.path.join() for OS compatibility
    # Activation is unnecessary, so we directly use the python binary path
    python_venv = os.path.join(folder_xtts_expanded, "venv", "bin", "python3")
    script_python = os.path.expanduser("core.py")
    
    # Construct the command list for subprocess.run
    command = [
        python_venv,
        script_python,
        text,
        output_file,
        '-s',
        os.path.expanduser(sample_file),
        '-l',
        language,
        '-speed',
        str(speed),
        '-folder_xtts',
        folder_xtts_expanded

    ]

    # input(command) # Debug line removed
    
    try:
        result = subprocess.run(
            command, 
            check=True, 
            text=True, 
            capture_output=True,
            timeout=300  # 5 minutes timeout
        )
        
        # Check if the file was created and is not empty
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"✅ Chunk generated: {os.path.basename(output_file)}")
            return True
        else:
            print("❌ Audio file not created or is empty.")
            # Optional: Print script output for debugging if file is missing
            # print(f"   Script STDOUT: {result.stdout[:200]}")
            # print(f"   Script STDERR: {result.stderr[:200]}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating chunk: {e}")
        if e.stderr:
            print(f"   STDERR: {e.stderr[:200]}")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout while generating chunk.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


# --- Database Functions (From previous interactions) ---

def load_database():
    """
    Loads the database content from the JSON file.
    Returns an empty dictionary if the file does not exist.
    """
    try:
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        # Handle case where file exists but is empty or corrupt
        print(f"Warning: The file '{DATABASE_FILE}' is corrupt or empty. Starting with a new configuration.")
        return {}

def save_database(data):
    """
    Saves the provided data dictionary to the JSON file.
    """
    try:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving to '{DATABASE_FILE}': {e}")


def get_xtts_folder_path():
    """
    Consults the database for the XTTS folder path.
    If not found, it prompts the user for the location and saves it.
    
    Returns:
        str: The valid path to the XTTS installation folder.
    """
    db_data = load_database()
    xtts_folder = db_data.get(XTTS_KEY)

    # 1. Check if the variable exists and the path is valid
    # We apply expanduser() here as well, in case the stored path uses ~
    if xtts_folder and os.path.isdir(os.path.expanduser(xtts_folder)):
        # Important: Return the *expanded* path for use in the program
        expanded_path = os.path.expanduser(xtts_folder)
        print(f"Path loaded from {DATABASE_FILE}: **{expanded_path}**")
        return expanded_path
    
    # 2. Variable is missing or the path is invalid, prompt the user
    if xtts_folder:
        print(f"Stored path '{xtts_folder}' is not a valid directory. Please provide the correct path.")
    else:
        print(f"The '{XTTS_KEY}' variable was not found in '{DATABASE_FILE}'.")
        
    while True:
        user_input = input("\n**Please enter the absolute path to your webui of the XTTS installation folder (e.g., ~/my/xtts/webui):**\n> ").strip()
        
        # 1. Expand the tilde (~) to the user's home directory.
        # 2. Store the expanded path in a new variable for verification.
        checked_path = os.path.expanduser(user_input)
        
        if os.path.isdir(checked_path):
            # Path is valid, save the *original* input (e.g., "~/my/xtts")
            # This is better for portability if the user's home dir changes.
            db_data[XTTS_KEY] = user_input
            save_database(db_data)
            print(f"\n✅ Path saved successfully to {DATABASE_FILE}!")
            
            # Return the *expanded* path for immediate use by the program
            return checked_path 
        else:
            # Path is invalid, prompt again
            print("\n❌ Invalid path. The entered path is not a valid directory. Please try again.")