import whisper
import os

class TetoAudition:
    def __init__(self):
        # Le modèle 'base' est idéal pour le Mac Mini M-Series
        self.model = whisper.load_model("base")

    def transcrire(self, audio_path):
        if not os.path.exists(audio_path):
            return None
        result = self.model.transcribe(audio_path)
        return result["text"].strip().lower()