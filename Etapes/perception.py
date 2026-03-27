import cv2
import os

class EnfantVision:
    def __init__(self):
        # La mémoire visuelle de l'IA
        self.album_souvenirs = {} 

    def observer_image(self, chemin_image):
        if not os.path.exists(chemin_image):
            print("Erreur : Image introuvable.")
            return

        print(f"\n[OEIL] Analyse de l'image : {chemin_image}")
        
        # L'IA vérifie si elle a déjà "vu" cette image exacte
        if chemin_image not in self.album_souvenirs:
            self.appel_a_moise(chemin_image)
        else:
            print(f"[ETAT] Cohérence visuelle stable. Je reconnais : {self.album_souvenirs[chemin_image]}")

    def appel_a_moise(self, chemin_image):
        print(f"[ALERTE STRESS] Entropie visuelle ! Objet inconnu détecté.")
        print(f"--- APPEL À L'ADULTE (MOÏSE) ---")
        
        # Ici, l'IA affiche l'image pour que tu l'aides
        img = cv2.imread(chemin_image)
        cv2.imshow("Qu'est-ce que c'est ?", img)
        cv2.waitKey(1) # Affiche l'image brièvement
        
        nom_objet = input(f"Moïse, comment nommes-tu cet objet ? : ")
        
        # Enregistrement du lien dans le Graphe (mémoire)
        self.album_souvenirs[chemin_image] = nom_objet
        print(f"[MEMOIRE] Lien créé : Image <-> {nom_objet}. Stress apaisé.")
        cv2.destroyAllWindows()

# Initialisation
ia_enfant = EnfantVision()
ia_enfant.observer_image('pomme.jpg')