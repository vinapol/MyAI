import cv2
import os
import json

def restaurer_et_synchroniser():
    fichier_json = "memoire_enfant.json"
    
    if not os.path.exists(fichier_json):
        print("[ERREUR] Le fichier JSON est introuvable.")
        return

    # 1. On utilise enfin la variable pour lire ta mémoire
    with open(fichier_json, 'r', encoding='utf-8') as f:
        memoire = json.load(f)

    print(f"--- Analyse de {len(memoire)} souvenirs pour Moïse ---")

    for chemin_image in memoire.keys():
        # On vérifie si le fichier existe avant de le transformer
        if os.path.exists(chemin_image):
            img = cv2.imread(chemin_image)
            if img is None: continue

            # Transformation en Gris + Flou (Standardisation)
            img_grise = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_restauree = cv2.GaussianBlur(img_grise, (5, 5), 0)

            # Sauvegarde par-dessus l'ancienne
            cv2.imwrite(chemin_image, img_restauree)
            print(f"[SYNCHRO] {chemin_image} est maintenant optimisé.")
        else:
            print(f"[ALERTE] {chemin_image} est dans le JSON mais introuvable sur le disque.")

    print("--- Mémoire parfaitement synchronisée et convertie ! ---")

if __name__ == "__main__":
    restaurer_et_synchroniser()