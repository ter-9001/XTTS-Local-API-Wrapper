import os
import soundfile as sf
import numpy as np
import noisereduce as nr
import re
import os
import sys


# Specific imports to load the model locally
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from TTS.api import TTS
import math
import torch
import torchaudio
import time

import argparse
import sys
import os
import tempfile
import glob

import os
import gc
import time
from torch import cuda



# Path to the local XTTS-v2 model directory
XTTS_DIR = "/home/user/xtts-webui-v1_0-portable/webui"
MODEL_DIR =  os.path.join(XTTS_DIR, "/models/v2.0.2/")
CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")
CHECKPOINT_PATH =  os.path.join(MODEL_DIR, "model.pth") # Assuming default name
VOCAB_PATH = os.path.join(MODEL_DIR, "vocab.json") 
SPEAKER_FILE_PATH = os.path.join(MODEL_DIR, "speakers_xtts.pth") 

# --- Output Configurations ---
TEMP_OUTPUT_PATH = "temp_output.wav" # Audio BEFORE noise reduction
FINAL_OUTPUT_PATH = "output_audio_clean.wav" # Audio AFTER noise reduction
LANGUAGE = "en"


PROGRESS = 0
TOTAL = 0


def my_model(use_cuda: bool = True):
    # Initializes and loads the XTTS model structure and weights
    device = "cuda" if use_cuda else "cpu"
    
    # 1. Load configuration
    config = XttsConfig()
    config.load_json(str(CONFIG_PATH))
    
    # 2. Initialize the model structure
    model = Xtts.init_from_config(config)
    
    # Define the vocabulary path explicitly
    VOCAB_PATH = os.path.join(MODEL_DIR, "vocab.json") 
    
    # 3. Load weights (without 'eval_model', as previously corrected)
    # We pass VOCAB_PATH explicitly
    model.load_checkpoint(
        config, 
        checkpoint_path=CHECKPOINT_PATH,
        vocab_path=VOCAB_PATH, # <--- This line resolves the join issue
        speaker_file_path=SPEAKER_FILE_PATH

    ) 
    model.to(device)
    
    print(f"Model successfully loaded on: {device.upper()}")
    return model
    


def make_audios(texto, output_file, language="en", use_cuda=True, 
                audio_sample_file="audio.mp3", speed=1.0, folder_xtts= '~/xtts-webui-v1_0-portable/webui/'):
    """
    Generates audio with speed control.
    
    Args:
        texto: Text to convert to audio
        output_file: Output file
        language: Audio language
        use_cuda: Use GPU if available
        audio_sample_file: Voice sample file
        speed: Speech speed (1.0 = normal, 1.5 = 50% faster, 0.8 = slower)
    """
    
    # Expand paths
    audio_sample_file = os.path.expanduser(audio_sample_file)
    output_file = os.path.expanduser(output_file)
    
    global MODEL
    # Model loading moved to my_model()
    MODEL = my_model()
    
    # Checks
    if not os.path.exists(audio_sample_file):
        print(f"❌ Voice file not found: {audio_sample_file}")
        return
    
    try:
        # Get latents from the reference voice
        gpt_cond_latent, speaker_embedding = MODEL.get_conditioning_latents(audio_sample_file)
        
        # Split text into parts
        MAX_CHARS = 2000
        partes_texto = []
        start_index = 0
        
        while start_index < len(texto):
            end_index = min(start_index + MAX_CHARS, len(texto))
            
            # Ensure break at a space
            if end_index < len(texto) and texto[end_index] != ' ':
                last_space = texto.rfind(' ', start_index, end_index)
                if last_space != -1:
                    end_index = last_space
            
            partes_texto.append(texto[start_index:end_index].strip())
            start_index = end_index + 1
        
        print(f"📝 Text parts: {len(partes_texto)}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 Temporary directory: {temp_dir}")
            
            for i, parte in enumerate(partes_texto):
                if not parte:
                    continue
                
                # 🔥 SPEED PARAMETER ADDED HERE
                out = MODEL.inference(
                    text=parte,
                    language=language,
                    gpt_cond_latent=gpt_cond_latent,
                    speaker_embedding=speaker_embedding,
                    speed=speed,  # 🎯 NEW PARAMETER
                    enable_text_splitting=True
                )

                
                output_part = os.path.join(temp_dir, f"part{i+1}.mp3")
                torchaudio.save(output_part, torch.tensor(out["wav"]).unsqueeze(0), 24000)
                
                print(f"✅ Part {i+1}/{len(partes_texto)} generated (speed: {speed}x)", 
                      end='\r', flush=True)
                time.sleep(1)  # Small pause between parts
            
            # Merge all parts
            merge_audio_parts_advanced(temp_dir, output_file)
            print(f"\n🎉 Final audio generated: {output_file} (speed: {speed}x)")
            
    except Exception as e:
        print(f"❌ Error: {e}")



def merge_audio_parts_advanced(tmp_dir, output_file):
    """
    More robust version for joining audio parts
    """
    
    audio_files = glob.glob(os.path.join(tmp_dir, "part*.mp3"))
    
    if not audio_files:
        print("No audio files found!")
        return False
    
    # Extract numbers from files using regex
    def extract_number(filename):
        match = re.search(r'part(\d+)\.mp3', os.path.basename(filename))
        return int(match.group(1)) if match else 0
    
    # Sort by extracted numbers
    audio_files.sort(key=extract_number)
    
    print(f"Found {len(audio_files)} files:")
    for i, file in enumerate(audio_files, 1):
        print(f"  {i:2d}. {os.path.basename(file)}")
    
    # Merge the files
    try:
        with open(output_file, 'wb') as outfile:
            for audio_file in audio_files:
                with open(audio_file, 'rb') as infile:
                    outfile.write(infile.read())
                print(f"✓ Added: {os.path.basename(audio_file)}")
        
        print(f"\n✅ Final file saved in: {output_file}")
        print(f"📁 Size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False






if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Audio generator from text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Usage examples:
    python main.py "I am the batman" batman.mp3
    python main.py "Hello world" output.wav --language en --use-cuda
    python main.py "Olá mundo" teste.mp3 --language pt --sample "voice.wav"
            """
        )
        
    # Required arguments
    parser.add_argument(
        "texto",
        type=str,
        help="Text to be converted to audio"
    )
    
    parser.add_argument(
        "output_file", 
        type=str,
        help="Name of the output file (e.g., audio.mp3)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="en",
        help="Text language (default: en)"
    )
    
    parser.add_argument(
        "--use-cuda", "-c",
        action="store_true",
        help="Use CUDA GPU if available"
    )
    
    parser.add_argument(
        "--sample", "-s",
        type=str,
        dest="audio_sample_file",
        help="Voice sample file for cloning"
    )

    parser.add_argument(
        "--speed", "-speed",
        type=str,
        dest="speed",
        help="Voice speed"
    )

    parser.add_argument(
        "--folder_xtts", "-folder_xtts",
        type=str,
        dest="folder_xtts",
        help="Location of the xtts folder"
    )
    
    # Parse arguments
    args = parser.parse_args()

    # python3 ~/Downloads/python/make_audio_novenv.py 'Hello Man, I am the Batman. You - Gabriel - are THE GOAT !!!!'  batman2.mp3 -s "~/xtts-webui-v1_0-portable/webui/speakers/Batman_voice.wav"

    
    # Expansion of ~ to home directory
    if args.audio_sample_file and args.audio_sample_file.startswith("~"):
        args.audio_sample_file = os.path.expanduser(args.audio_sample_file)
    
    # Call the make_audios function


    XTTS_DIR = os.path.expanduser(args.folder_xtts)
    MODEL_DIR =  os.path.join(XTTS_DIR, "models", "v2.0.2")
    CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")
    CHECKPOINT_PATH =  os.path.join(MODEL_DIR, "model.pth") # Assuming default name
    VOCAB_PATH = os.path.join(MODEL_DIR, "vocab.json") 
    SPEAKER_FILE_PATH = os.path.join(MODEL_DIR, "speakers_xtts.pth") 
    
    try:
        make_audios(
            texto=args.texto,
            output_file=args.output_file,
            language=args.language,
            use_cuda=args.use_cuda,
            audio_sample_file=args.audio_sample_file,
            speed = float(args.speed),
            folder_xtts = args.folder_xtts
        )
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        sys.exit(1)