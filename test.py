from make_audio import make_audio 

# --- Function Call Example ---
# The make_audio function processes text, generates audio using the XTTS model, 
# and saves the output, handling text splitting and temporary files internally.

make_audio(
    # Argument 1: text (string)
    # The actual text to be converted into speech.
    "This is only a test", 

    # Argument 2: output_file (string)
    # The path where the final, merged audio file will be saved. 
    # The tilde (~) will be expanded to the user's home directory.
    "~/Downloads/bebe34.mp3", 

    # Argument 3: sample_file (string)
    # The path to the audio file used as a voice reference (speaker clone).
    # This determines the voice style, gender, and accent.
    "female.wav", 

    # Argument 4: language (string, optional)
    # The language of the text. This must match the language model used 
    # by XTTS (e.g., 'en' for English, 'pt' for Portuguese).
    # The Default is english
    language='en', 

    # Argument 5: speed (float, optional)
    # Controls the speed of speech generation (1.0 is normal).
    # e.g., 1.5 would be 50% faster, 0.8 would be slower.
    speed=1.0, 

    # Argument 6: max_chars (integer, optional)
    # The maximum number of characters per chunk used when splitting 
    # long texts before generating audio for each part and after concatenated
    max_chars=2000
)