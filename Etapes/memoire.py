import json
import os

class EnfantMemoire:
    def __init__(self, fichier_memoire="memoire_enfant.json"):
        self.fichier_memoire = fichier_memoire
        self.memoire = self.charger_memoire()

    def charger_memoire(self):
        # L'IA vérifie si elle a déjà des souvenirs
        if os.path.exists(self.fichier_memoire):
            with open(self.fichier_memoire, 'r', encoding='utf-8') as f:
                print("[MEMOIRE] Chargement des souvenirs passés...")
                return json.load(f)
        else:
            print("[MEMOIRE] Tabula Rasa. Aucun souvenir trouvé.")
            return {}

    def sauvegarder_souvenir(self, concept, definition):
        # Loi de Hebb simplifiée : on crée ou on renforce le lien
        if concept in self.memoire:
            self.memoire[concept]["confiance"] += 0.1
            print(f"[DOPAMINE] Lien renforcé pour '{concept}'.")
        else:
            self.memoire[concept] = {"definition": definition, "confiance": 0.1}
            print(f"[APPRENTISSAGE] Nouveau concept enregistré : '{concept}'.")
        
        # Écriture physique sur le disque
        with open(self.fichier_memoire, 'w', encoding='utf-8') as f:
            json.dump(self.memoire, f, indent=4, ensure_utf8=False)

    def saluer_tuteur(self):
        nb_souvenirs = len(self.memoire)
        if nb_souvenirs > 0:
            print(f"\n[SUJET] Bonjour Moïse. Je possède {nb_souvenirs} concepts dans mon graphe.")
            print(f"Derniers souvenirs : {list(self.memoire.keys())}")
        else:
            print("\n[SUJET] Bonjour Moïse. Je suis prêt à apprendre.")

# --- TEST ---
ia = EnfantMemoire()
ia.saluer_tuteur()

# On simule un apprentissage
objet = input("\nQuel objet vois-tu ? : ")
sens = input(f"Quelle est la signification de '{objet}' ? : ")
ia.sauvegarder_souvenir(objet, sens)