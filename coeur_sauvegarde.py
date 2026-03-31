import cv2
import json
import os
import unicodedata
from neo4j import GraphDatabase
from protocole_apprentissage import ProtocoleApprentissage

class MemoireGraphe:
    def __init__(self, uri="neo4j://127.0.0.1:7687", user="neo4j", password="Vinapol175#"):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("[NEO4J] ✅ Connexion au graphe établie.")
        except Exception as e:
            print(f"[NEO4J] ❌ ERREUR CONNEXION : {e}")
            self.driver = None

    def apprendre_objet(self, nom_objet, categorie="Inconnu"):
        if not self.driver:
            print("[NEO4J] ⚠️ Abandon : Driver non connecté.")
            return

        with self.driver.session() as session:
            try:
                # Utilisation de CREATE pour l'objet et MERGE pour la catégorie
                query = """
                MERGE (c:Categorie {nom: $cat})
                MERGE (o:Objet {nom: $nom, date: datetime()})
                CREATE (o)-[:APPARTIENT_A]->(c)
                RETURN o.nom
                """
                session.run(query, nom=nom_objet, cat=categorie)
                print(f"[NEO4J] 🚀 BULLE CRÉÉE : {nom_objet} -> {categorie}")
            except Exception as e:
                print(f"[NEO4J] ❌ ERREUR TRANSACTION : {e}")
                
    def obtenir_infos(self, nom_objet):
        if not self.driver: return "Inconnu"
    
    # Sécurité : on s'assure de n'avoir que le nom (le deuxième élément du tuple)
        if isinstance(nom_objet, (list, tuple)):
            # Si c'est ('CERTITUDE', 'micro'), on prend 'micro'
            cible = nom_objet[1] if len(nom_objet) > 1 else nom_objet[0]
        else:
            cible = nom_objet

        with self.driver.session() as session:
            # On force en minuscules pour correspondre au graphe
            query = "MATCH (o:Objet {nom: $nom})-[:APPARTIENT_A]->(c:Categorie) RETURN c.nom AS cat"
            res = session.run(query, nom=str(cible).lower())
            record = res.single()
        return record["cat"] if record else "Inconnue"
    
    def renforcer_apprentissage(self, nom_objet, est_correct=True):
        if not self.driver: return
    
        with self.driver.session() as session:
            # On ajoute ou augmente une propriété 'confiance' sur l'objet
            query = """
            MATCH (o:Objet {nom: $nom})
            SET o.confiance = coalesce(o.confiance, 0) + (case when $win then 1 else -1 end)
            RETURN o.nom, o.confiance
             """
            session.run(query, nom=nom_objet.lower(), win=est_correct)
            print(f"[REFORCEMENT] Confiance de {nom_objet} mise à jour.")
    def tisser_lien(self, depart, arrivee, relation="LIE_A"):
        if not self.driver: return
        with self.driver.session() as session:
            query = f"MATCH (a) WHERE a.nom = $dep MATCH (b) WHERE b.nom = $arr MERGE (a)-[r:{relation}]->(b)"
            session.run(query, dep=depart.lower(), arr=arrivee.lower())

    def suggerer_liaisons_categories(self):
        if not self.driver: return None
        with self.driver.session() as session:
            query = """
            MATCH (c1:Categorie) WHERE NOT (c1)-[:SOUS_CATEGORIE_DE]->(:Categorie)
            MATCH (c2:Categorie) WHERE c1 <> c2
            RETURN c1.nom AS enfant, c2.nom AS parent LIMIT 1
            """
            resultat = session.run(query)
            record = resultat.single()
            return [record["enfant"], record["parent"]] if record else None

    def analyser_mots_communs(self):
        if not self.driver: return None
        with self.driver.session() as session:
            # 1. Récupérer TOUS les objets pour trouver des points communs
            res = session.run("MATCH (o:Objet) RETURN o.nom AS nom")
            noms = [record["nom"] for record in res]

            for i in range(len(noms)):
                for j in range(i + 1, len(noms)):
                    n1, n2 = noms[i].lower(), noms[j].lower()
                
                    # On sépare les mots et on garde ceux de plus de 2 lettres
                    mots1 = {m for m in n1.split('_') if len(m) > 2} | {m for m in n1.split() if len(m) > 2}
                    mots2 = {m for m in n2.split('_') if len(m) > 2} | {m for m in n2.split() if len(m) > 2}
                
                    communs = mots1.intersection(mots2)

                    if communs:
                        mot = list(communs)[0]
                    
                        # On vérifie si l'un de ces deux objets n'est pas encore lié à la catégorie 'mot'
                        # (Même si l'objet s'appelle lui-même 'bureau')
                        check_query = """
                        MATCH (o:Objet {nom: $nom})-[:APPARTIENT_A]->(c:Categorie {nom: $m})
                        RETURN o
                        """
                        lie_1 = session.run(check_query, nom=noms[i], m=mot).single()
                        lie_2 = session.run(check_query, nom=noms[j], m=mot).single()
                    
                        # Si l'un des deux (ou les deux) n'a pas encore ce lien, on propose !
                        if not lie_1 or not lie_2:
                            cat_existe = session.run("MATCH (c:Categorie {nom: $m}) RETURN c", m=mot).single() is not None
                            return {
                                 "objets": [noms[i], noms[j]],
                                "mot_commun": mot,
                                "categorie_existe": cat_existe
                            }   
            return None
class IASauvegarde:
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.fichier_memoire = "memoire_objets.json"
        
        # Initialisation de la mémoire locale
        if os.path.exists(self.fichier_memoire):
            with open(self.fichier_memoire, 'r', encoding='utf-8') as f:
                self.memoire = json.load(f)
        else:
            self.memoire = {}
            
        # Connexion au graphe
        self.graphe = MemoireGraphe()
        self.protocole = ProtocoleApprentissage()

    def sauvegarder_image_et_graphe(self, img_np, nom_objet, categorie="Inconnu"):
        print(f"[IA] Début sauvegarde pour : {nom_objet}")
        
        # Nettoyage du nom
        nom_nettoye = "".join(c for c in unicodedata.normalize('NFD', nom_objet)
                              if unicodedata.category(c) != 'Mn').lower().replace(" ", "_")
        
        # 1. Image
        if not os.path.exists("collection"): os.makedirs("collection")
        chemin = f"collection/{nom_nettoye}.jpg"
        cv2.imwrite(chemin, cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY))
        
        # 2. JSON
        self.memoire[chemin] = {"nom": nom_nettoye}
        with open(self.fichier_memoire, 'w', encoding='utf-8') as f:
            json.dump(self.memoire, f, indent=4)
            
        # 3. NEO4J (Le moment crucial)
        if self.graphe:
            self.graphe.apprendre_objet(nom_nettoye, categorie)
        else:
            print("[IA] ⚠️ Alerte : Graphe non initialisé, saut de l'étape Neo4j.")
            
        return nom_nettoye

    def instinct_reconnaissance(self, frame):
        if not self.memoire: 
            return "VIDE", None

        gris_cam = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp_cam, des_cam = self.orb.detectAndCompute(gris_cam, None)
        if des_cam is None: 
            return "ERREUR_VISION", None

        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        liste_scores = []

        # On scanne TOUTE la mémoire pour comparer
        for chemin, infos in self.memoire.items():
            if os.path.exists(chemin):
                img_mem = cv2.imread(chemin, 0)
                kp_m, des_m = self.orb.detectAndCompute(img_mem, None)
                if des_m is None: continue
            
                matches = bf.knnMatch(des_cam, des_m, k=2)
                # Filtre de Lowe pour ne garder que les points distinctifs
                bons = [m for m, n in matches if m.distance < 0.75 * n.distance]
            
                # On stocke le score de chaque objet
                liste_scores.append({
                    "nom": infos["nom"],
                    "score": len(bons)
                })

        # On envoie cette liste brute au protocole qui gère le Stress/Doute
        return self.protocole.analyser_incertitude(liste_scores)