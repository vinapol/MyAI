import whisper
import subprocess

class TetoVoice:
    def __init__(self):
        # On garde Whisper pour l'écoute
        print("[TETO] 🔊 Initialisation de la voix (Audrey)...")
        # On ne recharge pas forcément le modèle ici si app.py le fait déjà, 
        # mais c'est plus sûr pour l'autonomie du module.
        try:
            self.model = whisper.load_model("base")
        except Exception as e:
            print(f"Note: Whisper déjà chargé ou erreur : {e}")

    def ecouter(self, audio_path):
        """Transforme le son en texte"""
        result = self.model.transcribe(audio_path)
        return result["text"].lower().strip()

    def prononcer(self, texte):
        """Fait parler le Mac avec la voix d'Audrey"""
        print(f"[TETO PARLE] : {texte}")
        
        # 'say' : commande macOS
        # '-v Audrey' : sélection de la voix
        commande = ["say", "-v", "Audrey", texte]
        
        try:
            # On lance en arrière-plan pour ne pas freezer le reste du code
            subprocess.Popen(commande)
        except Exception as e:
            print(f"❌ Erreur voix : {e}")

    # Alias pour la compatibilité avec conscience.py et app.py
    parler = prononcer