import os
import sys
import site

from config import ROOT_DIR
# from TTS.utils.manage import ModelManager # Guarded import
# from TTS.utils.synthesizer import Synthesizer # Guarded import

class TTS:
    """
    Class for Text-to-Speech using Coqui TTS.
    """
    def __init__(self, model_name="tts_models/en/ljspeech/tacotron2-DDC_ph", use_local_tts=True) -> None: # Added parameters with defaults
        """
        Initializes the TTS class.

        Args:
            model_name (str): Name of the TTS model to use.
            use_local_tts (bool): Whether to use local TTS or not. If False, TTS specific imports are skipped.
        Returns:
            None
        """
        self.use_local_tts = use_local_tts
        if not self.use_local_tts:
            # Skip TTS specific initializations if not using local TTS (mocking scenario)
            self._synthesizer = None
            return

        from TTS.utils.manage import ModelManager # Moved import here
        from TTS.utils.synthesizer import Synthesizer # Moved import here
        
        # Detect virtual environment site packages
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # We're in a virtual environment
            site_packages = site.getsitepackages()[0]
        else:
            # We're not in a virtual environment, use the user's site packages
            site_packages = site.getusersitepackages()

        # Path to the .models.json file
        models_json_path = os.path.join(
            site_packages,
            "TTS",
            ".models.json",
        )

        # Create directory if it doesn't exist
        tts_dir = os.path.dirname(models_json_path)
        if not os.path.exists(tts_dir):
            os.makedirs(tts_dir)

        # Initialize the ModelManager
        self._model_manager = ModelManager(models_json_path)

        # Download tts_models/en/ljspeech/fast_pitch
        self._model_path, self._config_path, self._model_item = \
            self._model_manager.download_model(model_name) # Use passed model_name

        # Download vocoder_models/en/ljspeech/hifigan_v2 as our vocoder
        voc_path, voc_config_path, _ = self._model_manager. \
            download_model("vocoder_models/en/ljspeech/univnet") # Consider making vocoder configurable too
        
        # Initialize the Synthesizer
        self._synthesizer = Synthesizer(
            tts_checkpoint=self._model_path,
            tts_config_path=self._config_path,
            vocoder_checkpoint=voc_path,
            vocoder_config=voc_config_path
        )

    @property
    def synthesizer(self) -> 'Synthesizer': # Use string literal for type hint
        """
        Returns the synthesizer.

        Returns:
            Synthesizer: The synthesizer.
        """
        if not self.use_local_tts:
            # Return a mock or raise an error if called when use_local_tts is False
            # For now, returning None as it's consistent with __init__
            return None 
        return self._synthesizer

    def synthesize(self, text: str, output_file: str = os.path.join(ROOT_DIR, ".mp", "audio.wav")) -> str:
        if not self.use_local_tts:
            # Create a dummy wav file if not using local TTS
            with open(output_file, "w") as f:
                f.write("dummy audio content")
            return output_file
        """
        Synthesizes the given text into speech.

        Args:
            text (str): The text to synthesize.
            output_file (str, optional): The output file to save the synthesized speech. Defaults to "audio.wav".

        Returns:
            str: The path to the output file.
        """
        # Synthesize the text
        outputs = self.synthesizer.tts(text)

        # Save the synthesized speech to the output file
        self.synthesizer.save_wav(outputs, output_file)

        return output_file

