import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from src.classes.YouTube import YouTube
# from src.classes.Tts import TTS # Mocked
from src.config import initialize_config #, get_coqui_tts_model, get_local_tts_enabled # Mocked
from src.utils import rem_temp_files

def main():
    # Initialize configuration (reads config.json)
    initialize_config()

    # Clean up temp files
    if not os.path.exists(".mp"):
        os.makedirs(".mp")
    rem_temp_files()

    # Instantiate TTS - Mocked, so no instance needed
    # tts_instance = None # TTS(model_name=tts_model, use_local_tts=use_local_tts)
    # Need to import TTS class for instantiation, even if it's for mocking purposes
    from src.classes.Tts import TTS 
    tts_instance = TTS(use_local_tts=False)


    # Instantiate YouTube
    # Dummy account details from config.json are used by default if no specific account is chosen
    # Ensure 'dummy_youtube_id' from config.json is used
    youtube_account_id = "dummy_youtube_id" 
    
    # Need to fetch account details from config to pass to YouTube class
    from src.config import get_youtube_accounts
    accounts = get_youtube_accounts()
    account_details = next((acc for acc in accounts if acc['id'] == youtube_account_id), None)

    if not account_details:
        print(f"Account with ID {youtube_account_id} not found in config.json.")
        return

    youtube_instance = YouTube(
        account_uuid=account_details['id'],
        account_nickname=account_details['nickname'],
        fp_profile_path=account_details['firefox_profile_path'],
        niche=account_details['niche'],
        language=account_details['language']
    )

    # Generate video
    try:
        video_path = youtube_instance.generate_video(tts_instance)
        print(f"Video generated successfully: {video_path}")

        # Verify SRT file creation
        srt_files = [f for f in os.listdir(".mp") if f.endswith(".srt")]
        if srt_files:
            print(f"SRT file created: {os.path.join('.mp', srt_files[0])}")
        else:
            print("SRT file not created.")

    except Exception as e:
        print(f"Error during video generation: {e}")

if __name__ == "__main__":
    main()
