import cv2
import speech_recognition as sr
import json
import os
import pyttsx3
import unicodedata

# --- INITIALISATION DU MOTEUR VOCAL ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if "French" in voice.name or "fr" in voice.id:
        engine.setProperty('voice', voice.id)
        break
engine.setProperty('rate', 150)

def parler(texte):
    print(f"[VOIX] {texte}")
    engine.say(texte)
    engine.runAndWait()

class IASauvegarde:
    def __init__(self):
        self.fichier_memoire = "memoire_enfant.json"
        self.memoire = self.charger_memoire()
        self.reconnaissance = sr.Recognizer()
        # Initialisation ORB Haute Sensibilité pour les détails fins
        self.orb = cv2.ORB_create(nfeatures=5000, scaleFactor=1.1, nlevels=10)
        if not os.path.exists("collection"):
            os.makedirs("collection")
        print(f"\n[SYSTEME] IA-SAUVEGARDE activée. Mode : Haute Précision.")

    def charger_memoire(self):
        if os.path.exists(self.fichier_memoire):
            with open(self.fichier_memoire, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def sauvegarder(self):
        with open(self.fichier_memoire, 'w', encoding='utf-8') as f:
            json.dump(self.memoire, f, indent=4, ensure_ascii=False)

    def ecouter(self):
        try:
            with sr.Microphone(device_index=1) as source:
                self.reconnaissance.adjust_for_ambient_noise(source, duration=0.5)
                print(f"[OUIE] J'écoute...")
                audio = self.reconnaissance.listen(source, timeout=7, phrase_time_limit=4)
            return self.reconnaissance.recognize_google(audio, language="fr-FR").lower()
        except:
            return None

    def cycle_apprentissage(self, chemin_temporaire):
        """Mémorise un nouvel objet en haute définition."""
        parler("Quel est le nom de cet objet ?")
        mot_entendu = self.ecouter()

        if not mot_entendu:
            mot_entendu = input("[CLAVIER] Écris le nom : ").strip()

        if not mot_entendu:
            if os.path.exists(chemin_temporaire): os.remove(chemin_temporaire)
            return

        nom_nettoye = "".join(c for c in unicodedata.normalize('NFD', mot_entendu)
                              if unicodedata.category(c) != 'Mn').lower().replace(" ", "_")

        nouveau_chemin = f"collection/{nom_nettoye}.jpg"
        parler(f"J'enregistre {nom_nettoye}. Tape 'verite' pour confirmer.")
        
        if input("Confirmation (verite) : ").lower() == "verite":
            img = cv2.imread(chemin_temporaire)
            if img is None: return

            # Passage en gris pour l'empreinte vectorielle
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(nouveau_chemin, gris)
            
            self.memoire[nouveau_chemin] = {"nom": nom_nettoye}
            self.sauvegarder()
            print(f"[SUCCÈS] Empreinte de '{nom_nettoye}' mémorisée.")
            parler("C'est fait.")
        
        if os.path.exists(chemin_temporaire): os.remove(chemin_temporaire)

    def instinct_reconnaissance(self, frame_actuelle):
        """Analyse vectorielle avec Ratio Test pour éviter les erreurs."""
        if not self.memoire: return None

        gris_cam = cv2.cvtColor(frame_actuelle, cv2.COLOR_BGR2GRAY)
        kp_cam, des_cam = self.orb.detectAndCompute(gris_cam, None)

        if des_cam is None: return None

        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        meilleur_objet = None
        max_bons_points = 0

        for chemin, infos in self.memoire.items():
            if os.path.exists(chemin):
                template = cv2.imread(chemin, 0)
                if template is None: continue
                
                kp_mem, des_mem = self.orb.detectAndCompute(template, None)
                if des_mem is None: continue

                # Comparaison KNN pour le Ratio Test
                matches = bf.knnMatch(des_cam, des_mem, k=2)
                
                # Filtrage de précision (Lowe's Ratio Test)
                bons_matches = []
                for m_list in matches:
                    if len(m_list) == 2:
                        m, n = m_list
                        if m.distance < 0.75 * n.distance:
                            bons_matches.append(m)
                
                score = len(bons_matches)
                if score > max_bons_points and score > 15:
                    max_bons_points = score
                    meilleur_objet = infos.get("nom")

        return meilleur_objet

    def vision_directe(self):
        """Mode PC classique (iVCam) pour tests rapides."""
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret: break

            cv2.imshow("IA-SAUVEGARDE", frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('a'):
                cv2.imwrite("temp.jpg", frame)
                self.cycle_apprentissage("temp.jpg")
            elif key == ord('i'):
                res = self.instinct_reconnaissance(frame)
                if res: parler(f"C'est {res}")
                else: parler("Inconnu")
            elif key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    brain = IASauvegarde()
    brain.vision_directe()