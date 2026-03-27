import speech_recognition as sr
import cv2

class EnfantEcoute:
    def __init__(self):
        self.reconnaissance = sr.Recognizer()
        self.memoire_visuelle = {"pomme.jpg": "pomme"}

    def ecouter_tuteur(self):
        with sr.Microphone() as source:
            print("\n[OUIE] L'IA écoute... Parle à Moïse.")
            # Ajuste le bruit ambiant pour mieux entendre
            self.reconnaissance.adjust_for_ambient_noise(source)
            audio = self.reconnaissance.listen(source)

        try:
            # Transformation du son en texte (via Google Speech Recognition gratuit)
            phrase = self.reconnaissance.recognize_google(audio, language="fr-FR")
            return phrase.lower()
        except:
            print("[ERREUR] Je n'ai pas compris le son.")
            return None

    def verifier_fusion(self, chemin_image):
        print(f"\n[SYSTEME] Analyse visuelle de : {chemin_image}")
        mot_dit = self.ecouter_tuteur()
        
        if mot_dit:
            print(f"[SON] J'ai entendu : '{mot_dit}'")
            objet_vu = self.memoire_visuelle.get(chemin_image)

            if objet_vu == mot_dit:
                print("--- COHÉRENCE TOTALE ---")
                print(f"L'image et le son confirment l'entité : {objet_vu}")
            else:
                print(f"--- CONFLIT COGNITIF ---")
                print(f"Doute : Je vois '{objet_vu}' mais j'entends '{mot_dit}'.")
                # Ici, on pourrait ajouter l'appel à l'adulte pour trancher

# Lancement du test
ia = EnfantEcoute()
ia.verifier_fusion("pomme.jpg")