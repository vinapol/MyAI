from neo4j import GraphDatabase

class TetoMemory:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    # --- MONDE PHYSIQUE ---
    def add_physical_object(self, name, image_path, confidence=0):
        with self.driver.session() as session:
            query = """
            MERGE (o:ObjetPhysique {nom: $nom})
            SET o.image_path = $path, o.confiance = $conf, o.date = datetime()
            RETURN o
            """
            session.run(query, nom=name.lower(), path=image_path, conf=confidence)

    # --- MONDE LANGAGE ---
    def add_concept(self, term, definition=""):
        with self.driver.session() as session:
            query = """
            MERGE (c:Concept {terme: $terme})
            SET c.definition = $definition_text, c.date_apprentissage = datetime()
            """
            # On utilise definition_text ici pour éviter le mot réservé 'def'
            session.run(query, terme=term.lower(), definition_text=definition)

    # --- TISSAGE DES LIENS ---
    def link_physique_to_langage(self, object_name, concept_term, relation="EST_UN"):
        with self.driver.session() as session:
            # Note: Le type de relation (EST_UN) ne peut pas être un paramètre $ en Cypher
            query = f"""
            MATCH (o:ObjetPhysique {{nom: $o_nom}})
            MATCH (c:Concept {{terme: $c_terme}})
            MERGE (o)-[r:{relation.upper()}]->(c)
            RETURN r
            """
            session.run(query, o_nom=object_name.lower(), c_terme=concept_term.lower())
    # Dans la classe TetoMemory
    def add_vibration(self, texte_transcrit, confidence=100):
        """Crée une empreinte sonore dans la mémoire"""
        with self.driver.session() as session:
            query = """
            MERGE (v:Vibration {entendu: $texte})
            SET v.date_apparition = datetime(), v.confiance = $conf
            RETURN v
            """
            session.run(query, texte=texte_transcrit.lower(), conf=confidence)

    def relier_voix_concept(self, texte, terme_concept):
        """L'acte d'apprendre : Relier un son à une idée"""
        with self.driver.session() as session:
            query = """
            MATCH (v:Vibration {entendu: $texte})
            MATCH (c:Concept {terme: $terme})
            MERGE (v)-[r:NOMME {source: 'Moïse'}]->(c)
            RETURN type(r)
            """
            session.run(query, texte=texte.lower(), terme=terme_concept.lower())
            
    def tisse_lien(self, label, categorie, relation, poids=1.0):
        """Crée un lien avec un poids spécifique (1.0 pour validation Moïse)"""
        with self.driver.session() as session:
            query = """
            MERGE (o:Objet {nom: $label})
            MERGE (c:Concept {nom: $categorie})
            MERGE (o)-[r:RELATION {type: $rel_type}]->(c)
            SET r.poids = $poids, r.derniere_activation = datetime()
            """
            session.run(query, label=label, categorie=categorie, rel_type=relation, poids=poids)

    def appliquer_oubli(self, taux_decroissance=0.05):
        """Réduit le poids de tous les liens qui n'ont pas été activés récemment"""
        with self.driver.session() as session:
            query = """
            MATCH ()-[r:RELATION]->()
            SET r.poids = r.poids * (1.0 - $taux)
            WITH r WHERE r.poids < 0.1
            DELETE r
            """
            session.run(query, taux=taux_decroissance)

    def recuperer_succes_analogiques(self):
        with self.driver.session() as session:
            # Teto cherche des chemins qu'elle a créés par analogie (poids faible au départ)
            # qui s'avèrent cohérents avec d'autres structures du graphe
            query = """
            MATCH (o:Objet)-[r:RELATION {type: 'ANALOGIE'}]->(c:Concept)
            WHERE r.poids > 0.6
            RETURN o.nom as label, c.nom as concept
            LIMIT 1
            """
            result = session.run(query)
            return result.single()

    def simuler_pensee_proactive(self, features_actuels):
        """
        Avant même que Moïse ne parle, Teto compare ce qu'elle voit 
        avec tout ce qu'elle sait déjà pour prédire le sens.
        """
        # Calcul de distance vectorielle simplifié
        query = """
        MATCH (o:Objet)
        WITH o, gds.alpha.similarity.cosine(o.features, $f) AS sim
        WHERE sim > 0.85
        MATCH (o)-[:RELATION]->(c:Concept)
        RETURN c.nom, sim
        """
        # C'est ici que l'entité 'anticipe' la réalité
        
    def verifier_vibration(self, texte):
        """Vérifie si le son existe. Retourne True ou False."""
        with self.driver.session() as session:
            # On utilise une requête simple qui ne crash pas si vide
            result = session.run("MATCH (v:Vibration {texte: $t}) RETURN v LIMIT 1", t=texte)
            record = result.single()
            return record is not None

    def enregistrer_vibration_passive(self, texte):
        """Crée le neurone sonore s'il n'existe pas, ou l'ignore."""
        with self.driver.session() as session:
            session.run("""
                MERGE (v:Vibration {texte: $t})
                ON CREATE SET v.poids = 0.1, 
                            v.iterations = 1, 
                            v.last_seen = datetime()
                ON MATCH SET v.poids = v.poids + 0.01, 
                            v.iterations = v.iterations + 1, 
                            v.last_seen = datetime()
        """, t=texte)
    def obtenir_vibrations_matures(self, seuil=3):
        """Récupère uniquement les sons entendus plus de 'seuil' fois."""
        with self.driver.session() as session:
            # On ne renvoie que ce qui est solide (iterations >= seuil)
            query = "MATCH (v:Vibration) WHERE v.iterations >= $s RETURN v"
            result = session.run(query, s=seuil)
            return [record["v"] for record in result]

    def renforcer_lien_existant(self, texte):
        with self.driver.session() as session:
            # On augmente le poids car la répétition crée la certitude
            session.run("""
                MATCH (v:Vibration {texte: $t})
                SET v.poids = v.poids + 0.02, v.last_seen = datetime()
            """, t=texte)
    def lier_mots_cooccurrence(self, mots):
        """Relie les mots entendus ensemble pour créer du contexte."""
        if len(mots) < 2: return
        with self.driver.session() as session:
            for i in range(len(mots)):
                for j in range(i + 1, len(mots)):
                    session.run("""
                        MATCH (a:Vibration {texte: $m1})
                        MATCH (b:Vibration {texte: $m2})
                        MERGE (a)-[r:LIE_A]-(b)
                        ON CREATE SET r.force = 1
                        ON MATCH SET r.force = r.force + 1
                    """, m1=mots[i], m2=mots[j])
    
    def valider_apprentissage(self, objet_id, vibration_id):
        with self.driver.session() as session:
            # On force le poids de la relation 'NOMME' à 1.0 (Certitude)
            session.run("""
                MATCH (o:ObjetPhysique)-[r:NOMME]->(v:Vibration)
                WHERE elementId(o) = $oid AND elementId(v) = $vid
                SET r.poids = 1.0, r.valide_le = datetime()
            """, oid=objet_id, vid=vibration_id)