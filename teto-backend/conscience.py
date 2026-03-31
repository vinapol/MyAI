import threading
import time
import random

class TetoConscience:
    def __init__(self, memory, speech, callback_question):
        self.memory = memory
        self.speech = speech
        self.callback_question = callback_question # Pour mettre à jour le contexte dans app.py
        self.running = True
    
    def explorer(self):
        print("🧠 Teto : Mode introspection activé.")
        while self.running:
            # On attend entre 2 et 5 minutes
            time.sleep(random.randint(60, 180))
            
            try:
                self.analyser_memoire()
            except Exception as e:
                print(f"❌ Erreur lors de la réflexion : {e}")

    def analyser_memoire(self):
        print("🔍 Teto examine son graphe de connaissances...")
        with self.memory.driver.session() as session:
            # SCÉNARIO 1 : Chercher un objet connu visuellement mais sans nom (Vibration)
            query_objet = """
                MATCH (o:ObjetPhysique)
                WHERE NOT (o)-[:NOMME]->(:Vibration)
                RETURN o.nom AS nom, elementId(o) as id LIMIT 1
            """
            res = session.run(query_objet).single()

            if res:
                objet_nom = res['nom']
                objet_id = res['id']
                question = f"Moïse, je reconnais l'objet {objet_nom}, mais je n'ai pas de mot associé. C'est quoi ?"
                
                # Teto parle
                self.speech.parler(question)
                
                # On informe le backend via le callback pour l'affichage Front
                self.callback_question(question, objet_id=objet_id, type_sujet="objet")
                return

            # SCÉNARIO 2 : Chercher des vibrations orphelines (mots sans liens)
            # On peut ajouter d'autres scénarios ici plus tard

    def start(self):
        thread = threading.Thread(target=self.explorer, daemon=True)
        thread.start()

    def stop(self):
        self.running = False