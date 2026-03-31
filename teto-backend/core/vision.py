import cv2
import numpy as np # Import indispensable ici
import base64
import os
import uuid

class TetoVision:
    def __init__(self, collection_path="collection/"):
        self.orb = cv2.ORB_create()
        self.collection_path = collection_path
        if not os.path.exists(self.collection_path):
            os.makedirs(self.collection_path)

    def save_instance(self, img_b64, label):
        """Décode et sauvegarde l'image sans UUID"""
        img_data = base64.b64decode(img_b64)
        npimg = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        # --- MODIFICATION ICI ---
        # On utilise juste le label, en minuscule, pour le nom du fichier
        clean_label = label.lower().strip()
        filename = f"{clean_label}.jpg"
        filepath = os.path.join(self.collection_path, filename)
        
        cv2.imwrite(filepath, frame)
        
        # On retourne le chemin relatif pour Neo4j
        return filename, clean_label

    # --- LA FONCTION MANQUANTE ---
    def identifier_objet(self, frame):
        """Compare la vue actuelle avec les images dans collection/"""
        # Conversion en gris pour le matching
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp_cam, des_cam = self.orb.detectAndCompute(gray, None)
        if des_cam is None: return None

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        meilleur_nom = None
        max_matches = 0

        for fichier in os.listdir(self.collection_path):
            if not fichier.endswith(".jpg"): continue
            
            img_mem = cv2.imread(os.path.join(self.collection_path, fichier), 0)
            if img_mem is None: continue
            
            kp_m, des_m = self.orb.detectAndCompute(img_mem, None)
            if des_m is None: continue

            matches = bf.match(des_cam, des_m)
            # On ne garde que les points très proches
            bons_matches = [m for m in matches if m.distance < 50]
            
            if len(bons_matches) > max_matches and len(bons_matches) > 15:
                max_matches = len(bons_matches)
                # On récupère le nom avant l'ID unique (ex: 'clavier' dans 'clavier_a1b2.jpg')
                meilleur_nom = fichier.split('_')[0]

        return meilleur_nom