import os
import sys
import uuid
import wave # For creating a dummy WAV file
import assemblyai as aai
from unittest.mock import MagicMock, patch

# MoviePy imports
from moviepy.video.tools.subtitles import SubtitlesClip
# from moviepy.editor import TextClip # Removed to avoid ImageMagick/moviepy.editor issues

# --- Global settings and paths ---
ROOT_DIR = os.getcwd() 
MP_DIR = os.path.join(ROOT_DIR, ".mp")
DUMMY_AUDIO_FILENAME = "dummy_audio_core_v3.wav" # New name
DUMMY_AUDIO_PATH = os.path.join(MP_DIR, DUMMY_AUDIO_FILENAME)
DUMMY_SRT_CONTENT = """1
00:00:00,100 --> 00:00:00,800
Hello from test v3
"""

# --- Mocking AssemblyAI ---
aai.settings.api_key = "DUMMY_KEY_FOR_TEST"

mock_transcript_export = MagicMock(return_value=DUMMY_SRT_CONTENT)
mock_transcript = MagicMock()
mock_transcript.export_subtitles_srt = mock_transcript_export

mock_transcriber_instance = MagicMock()
mock_transcriber_instance.transcribe.return_value = mock_transcript

# --- Helper function to create dummy WAV ---
def create_dummy_wav(path, duration_s=1, sample_rate=44100, num_channels=1, sample_width=2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        num_frames = int(duration_s * sample_rate)
        silence = b'\x00' * (num_frames * num_channels * sample_width)
        wf.writeframes(silence)
    print(f"Dummy WAV created at: {path}")

# --- Minimal YouTube class for this test ---
class MinimalYouTube:
    def __init__(self):
        print("MinimalYouTube instance created.")

    def generate_subtitles(self, audio_path: str) -> str:
        print(f"MinimalYouTube.generate_subtitles called with audio_path: {audio_path}")
        os.makedirs(MP_DIR, exist_ok=True)
        
        transcriber = aai.Transcriber() 
        transcript = transcriber.transcribe(audio_path)
        subtitles_srt_content = transcript.export_subtitles_srt()

        srt_path = os.path.join(MP_DIR, str(uuid.uuid4()) + ".srt")
        with open(srt_path, "w") as file:
            file.write(subtitles_srt_content)
        print(f"Subtitles written to {srt_path} with content:\n{subtitles_srt_content}")
        return srt_path

# --- Test Execution ---
@patch('assemblyai.Transcriber', return_value=mock_transcriber_instance) 
def main(mock_aai_transcriber_class): 
    print("Starting test_subtitle_core.py")

    create_dummy_wav(DUMMY_AUDIO_PATH)
    youtube_instance = MinimalYouTube()

    print(f"Calling generate_subtitles with: {DUMMY_AUDIO_PATH}")
    srt_path = ""
    try:
        srt_path = youtube_instance.generate_subtitles(DUMMY_AUDIO_PATH)
        print(f"generate_subtitles returned: {srt_path}")
    except Exception as e:
        print(f"Error calling generate_subtitles: {e}")
        return

    if not srt_path or not os.path.exists(srt_path):
        print(f"SRT file not created at expected path: {srt_path}")
        return
    print(f"SRT file created successfully: {srt_path}")
    with open(srt_path, 'r') as f:
        content = f.read()
        if content.strip() == DUMMY_SRT_CONTENT.strip():
            print("SRT file content matches dummy content.")
        else:
            print(f"SRT file content mismatch. Got:\n{content}\nExpected:\n{DUMMY_SRT_CONTENT}")
            return

    # Test SubtitlesClip with an enhanced dummy generator
    def dummy_generator(txt):
        print(f"Dummy generator called with text: '{txt}'")
        mock_clip = MagicMock()
        mock_clip.text = txt # Store the text for potential inspection
        mock_clip.duration = 0.7 # srt line is 0.7s long (0.8 - 0.1)
        mock_clip.start = 0 # Relative start, SubtitlesClip will set actual start
        
        # SubtitlesClip will call set_start and set_pos on the generated clip
        mock_clip.set_start = MagicMock(return_value=mock_clip) 
        mock_clip.set_position = MagicMock(return_value=mock_clip) # Changed from set_pos
        mock_clip.set_pos = MagicMock(return_value=mock_clip) # Keep set_pos as well, moviepy uses it.


        # Make it an iterable (list of itself) if SubtitlesClip expects make_frame to return a list of clips
        # From MoviePy source, it seems make_frame should return a list of clips.
        # However, the generator for SubtitlesClip is usually expected to return a single clip per text.
        # The error "max() arg is an empty sequence" usually happens if the internal `self.clips` list in SubtitlesClip is empty
        # or if the durations are not being set/found correctly.
        # Let's ensure the mock_clip itself is returned, and SubtitlesClip handles it.
        return mock_clip

    print("Attempting to create SubtitlesClip with enhanced dummy_generator...")
    subtitles_clip = None
    try:
        subtitles_clip = SubtitlesClip(srt_path, dummy_generator)
        print("SubtitlesClip created successfully with enhanced dummy_generator.")
        
        if subtitles_clip.subtitles and len(subtitles_clip.subtitles) > 0:
            print(f"SubtitlesClip loaded {len(subtitles_clip.subtitles)} subtitle segment(s).")
            first_segment = subtitles_clip.subtitles[0]
            print(f"First segment data (type {type(first_segment)}): {first_segment}")
            if len(first_segment) == 2:
                 print(f"  Times: {first_segment[0]}")
                 print(f"  Content object type: {type(first_segment[1])}")
                 
                 actual_start_time, actual_end_time = first_segment[0]
                 expected_start_time = 0.1
                 expected_end_time = 0.8
                 
                 if abs(actual_start_time - expected_start_time) < 0.001 and \
                    abs(actual_end_time - expected_end_time) < 0.001:
                     print(f"First segment times ({actual_start_time}, {actual_end_time}) match expected dummy SRT.")
                 else:
                     print(f"First segment times ({actual_start_time}, {actual_end_time}) MISMATCH from expected ({expected_start_time}, {expected_end_time}).")

                 # Check if the mock clip from generator has its text attribute set
                 if hasattr(first_segment[1], 'text'):
                     print(f"  Mock clip text: '{first_segment[1].text}'")


        else:
            print("SubtitlesClip loaded, but no subtitle segments found within it (this is unexpected).")

    except Exception as e:
        print(f"Error creating or processing SubtitlesClip: {e}")
        
    print("test_subtitle_core.py finished.")

if __name__ == "__main__":
    os.makedirs(MP_DIR, exist_ok=True)
    main()
