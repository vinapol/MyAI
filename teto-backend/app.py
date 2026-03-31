from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np  # <--- AJOUTE CETTE LIGNE
import base64
import cv2
from core.memory import TetoMemory
from core.vision import TetoVision
from services.speech import TetoVoice
import config
import os
import whisper
import tempfile
from conscience import TetoConscience

def nettoyer_et_decouper(phrase):
    # Liste des mots inutiles à ignorer
    stop_words = ["le", "la", "les", "un", "une", "des", "est", "sont", "fait", "avec", "dans", "pour", "euh", "ah"]
    
    # Nettoyage : minuscule et retrait de la ponctuation
    mots = phrase.lower().replace(".", "").replace(",", "").replace("!", "").split()
    
    # On ne garde que les mots de plus de 3 lettres qui ne sont pas dans la liste
    return [m for m in mots if len(m) > 3 and m not in stop_words]

app = Flask(__name__)
CORS(app)

# Initialisation des modules (Mac Mini)
memory = TetoMemory(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PWD)
vision = TetoVision(config.COLLECTION_PATH)
speech = TetoVoice()
print("[TETO] 🧠 Chargement du modèle auditif...")
audio_model = whisper.load_model("base") # 'base' est rapide et précis sur M1/M2
model = whisper.load_model("base") 
print("Teto est prête à écouter.")
SILENCE_THRESHOLD = 0.1
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECTION_PATH = os.path.abspath(os.path.join(BASE_DIR, '../collection'))

contexte_teto = {"en_attente": False, "objet_id": None, "vibration_id": None}

@app.route('/collect', methods=['POST'])
def collect():
    try:
        data = request.json
        img_b64 = data.get('image')
        nom = data.get('label', 'inconnu')
        cat = data.get('category', 'Objet')
        rel = data.get('relation', 'EST_UN')

        # 1. Sauvegarde l'image via Vision
        path, name = vision.save_instance(img_b64, nom)

        # 2. Ajout au monde Physique
        memory.add_physical_object(name, path, confidence=100)

        # 3. Ajout au monde Langage (La catégorie)
        memory.add_concept(cat, definition="Validé par Moïse sur le terrain")

        # 4. Création du lien entre les deux mondes
        memory.link_physique_to_langage(name, cat, rel)

        return jsonify({
            "status": "succes", 
            "message": f"Teto : {name} enregistré comme {cat}."
        })
    except Exception as e:
        return jsonify({"status": "erreur", "message": str(e)}), 500
    
    
@app.route('/identifier', methods=['POST'])
def identifier():
    data = request.json
    # 1. Simulation du score de confiance (issu de vision.py)
    # Dans la vraie version, ce score vient du nombre de matches ORB
    score_confiance = data.get('score', 0.5) 
    
    # 2. Calcul du STRESS (Énergie Libre)
    # Plus le score est bas, plus le stress est haut
    stress = 1.0 - score_confiance
    
    # 3. Logique de l'ENTITÉ
    if stress > 0.6: # Seuil de Perplexité
        # Teto tente une ANALOGIE au lieu de dire "Inconnu"
        suggestion = memory.chercher_analogie(data.get('label', ''))
        
        if suggestion:
            msg = f"Je suis perplexe (Stress: {int(stress*100)}%). Cela ressemble à un {suggestion['suggestion']}."
            etat = "DOUTE"
        else:
            msg = "Je ne connais pas cette forme. Mon énergie libre est trop haute. Enseigne-moi."
            etat = "STRESS_MAX"
    else:
        msg = "Objet identifié avec succès."
        etat = "STABLE"
        # DOPAMINE : On renforce le lien car la prédiction était bonne
        memory.appliquer_oubli() # L'entité profite de la stabilité pour trier ses souvenirs

    return jsonify({
        "message": msg,
        "etat": etat,
        "stress_level": stress
    })
    
@app.route('/graph', methods=['GET'])
def get_graph():
    with memory.driver.session() as session:
        query = """
        MATCH (o:ObjetPhysique)-[r]->(c:Concept)
        RETURN o.nom as objet, type(r) as relation, c.terme as concept, o.image_path as img
        """
        results = session.run(query)
        
        nodes = []
        edges = []
        seen_nodes = set()

        for record in results:
            obj_id = record['objet']
            con_id = record['concept']

            # Ajouter le nœud Objet s'il n'existe pas encore
            if obj_id not in seen_nodes:
                nodes.append({"id": obj_id, "label": obj_id, "type": "objet", "img": record['img']})
                seen_nodes.add(obj_id)

            # Ajouter le nœud Concept s'il n'existe pas encore
            if con_id not in seen_nodes:
                nodes.append({"id": con_id, "label": con_id, "type": "concept"})
                seen_nodes.add(con_id)

            # Ajouter le lien
            edges.append({
                "id": f"e-{obj_id}-{con_id}",
                "source": obj_id,
                "target": con_id,
                "label": record['relation']
            })
        
        return jsonify({"nodes": nodes, "edges": edges})

@app.route('/api/images/<filename>', methods=["GET"])
def serve_image(filename):
    """Sert les images du dossier collection au frontend"""
    # Debug : affiche dans le terminal du Mac ce que React demande
    print(f"🔍 Teto cherche le spécimen : {filename}")
    return send_from_directory(COLLECTION_PATH, filename)

@app.route('/test')
def test():
    return "zgeg"

@app.route('/api/listen', methods=['POST'])
def listen():
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "Aucun son reçu"}), 400
    
    audio_file = request.files['audio']
    
    # 1. Traitement Temporaire
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        audio_file.save(temp_audio.name)
        
        # 2. Transcription (La Vibration devient Mot)
        result = audio_model.transcribe(temp_audio.name)
        vibration = result["text"].strip().lower()
        
    os.remove(temp_audio.name) # Nettoyage

    # 3. Mémoire : Teto enregistre ce qu'il a entendu
    # On crée un nœud de type 'Vibration' non relié (Doute initial)
    memory.add_vibration(vibration) 
    
    return jsonify({
        "status": "success", 
        "vibration": vibration,
        "message": "J'ai entendu une nouvelle vibration."
    })
@app.route('/api/dopamine', methods=['GET'])
def flux_dopamine():
    """
    Cette route simule le 'sentiment de réussite' de l'entité.
    Elle renvoie les derniers succès d'apprentissage autonome.
    """
    # Teto cherche les liens dont le poids a augmenté récemment sans intervention humaine directe
    success_auto = memory.recuperer_succes_analogiques()
    
    if success_auto:
        return jsonify({
            "statut": "EUREKA",
            "gain": "0.85",
            "message": f"Teto a stabilisé le lien : {success_auto['label']} -> {success_auto['concept']}",
            "energie_libre": "Basse (Stabilité)"
        })
    return jsonify({"statut": "REPOS", "message": "Teto observe et attend."})

@app.route('/api/ambiance', methods=['POST'])
def ecoute_ambiance():
    if 'audio' not in request.files:
        return jsonify({"erreur": "Pas de son reçu"}), 400
        
    audio_file = request.files['audio']
    path = "temp_vibration.wav"
    audio_file.save(path)
    
    try:
        # 1. TRANSCRIPTION (Le son devient Vibration)
        # On force la langue en français pour éviter que Teto confonde les mots
        result = model.transcribe(path, language="fr")
        vibration = result['text'].strip().lower()
        
        if not vibration:
            return jsonify({"etat": "SILENCE", "message": "J'écoute..."})

        # 2. ENREGISTREMENT DANS NEO4J
        # On crée le lien dans le graphe
        memory.enregistrer_vibration_passive(vibration)
        
        print(f"Teto a entendu : {vibration}")
        
        return jsonify({
            "etat": "ÉVEIL",
            "vibration": vibration,
            "message": f"J'ai perçu la vibration : {vibration}"
        })
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500
    finally:
        if os.path.exists(path):
            os.remove(path) # On nettoie le fichier temporaire
    
@app.route('/api/continu', methods=['POST'])
def flux_continu():
    if 'audio' not in request.files:
        return jsonify({"status": "erreur"}), 400
        
    audio = request.files['audio']
    temp_path = "stream_audio.wav"
    audio.save(temp_path)

    # 1. Transcription par Whisper
    result = model.transcribe(temp_path, language="fr", fp16=False)
    phrase_complete = result['text'].strip()

    # 2. On découpe la phrase en mots-clés
    mots_cles = nettoyer_et_decouper(phrase_complete)

    if not mots_cles:
        return jsonify({"status": "ignore", "reason": "pas de mots significatifs"})

    # 3. Pour chaque mot, on met à jour la mémoire (Incrémentation du compteur)
    for mot in mots_cles:
        memory.enregistrer_vibration_passive(mot)
    memory.lier_mots_cooccurrence(mots_cles)
    print(f"👂 Teto a entendu les concepts : {mots_cles}")

    return jsonify({
        "status": "PROCESS",
        "mots": mots_cles,
        "phrase_originale": phrase_complete
    })
    
    
@app.route('/api/graph', methods=['GET'])
def get_full_graph():
    with memory.driver.session() as session:
        # 1. On récupère d'abord les nœuds valides (mature ou objet)
        nodes_query = """
        MATCH (n)
        WHERE (n:Vibration AND n.iterations >= 3) OR NOT n:Vibration
        RETURN n
        """
        nodes_res = session.run(nodes_query)
        
        nodes = []
        node_ids = set()
        
        for record in nodes_res:
            node = record['n']
            nid = str(node.element_id)
            label = node.get('nom') or node.get('terme') or node.get('texte') or "Inconnu"
            
            nodes.append({
                "id": nid,
                "type": 'vibrationNode' if 'Vibration' in node.labels else 'default',
                "data": { "label": label, "poids": node.get('poids', 0.1) },
                "position": {"x": int(np.random.randint(100, 600)), "y": int(np.random.randint(100, 400))}
            })
            node_ids.add(nid)

        # 2. On récupère TOUS les liens entre ces nœuds spécifiques
        edges = []
        if node_ids:
            edges_query = """
            MATCH (n)-[r]->(m)
            WHERE elementId(n) IN $ids AND elementId(m) IN $ids
            RETURN r, elementId(n) as source, elementId(m) as target
            """
            edges_res = session.run(edges_query, ids=list(node_ids))
            
            for record in edges_res:
                edges.append({
                    "id": f"e-{str(record['r'].element_id)}",
                    "source": record['source'],
                    "target": record['target'],
                    "label": record['r'].type,
                    "animated": True
                })
        
        return jsonify({
        "nodes": nodes,
        "edges": edges,
        "conversation": {
            "attente_reponse": contexte_teto["en_attente"],
            "derniere_question": contexte_teto.get("derniere_question")
        }
    })

@app.route('/api/retroaction', methods=['POST'])
def traiter_retroaction():
    global contexte_teto
    
    # 1. Vérifier si on a un fichier audio
    if 'audio' not in request.files:
        return jsonify({"status": "erreur", "message": "Pas de fichier audio"})

    audio_file = request.files['audio']
    
    # On sauvegarde temporairement le fichier pour Whisper
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        audio_file.save(temp_audio.name)
        # On utilise audio_model (ton instance Whisper chargée ligne 46)
        result = audio_model.transcribe(temp_audio.name)
        response_text = result["text"].lower().strip()
    
    # 2. Vérifier si Teto attendait une réponse
    # Correction de la faute de frappe : contexts_teto -> contexte_teto
    if not contexte_teto.get("en_attente") or not response_text:
        return jsonify({"status": "ignore"})
        
    print(f"[TETO] Réponse reçue : {response_text}")

    # 3. Logique de confirmation
    mots_cles_oui = ["oui", "correct", "c'est ça", "exact", "ouais", "effectivement"]
    confirmation = any(word in response_text for word in mots_cles_oui)
    
    if confirmation:
        # Validation dans Neo4j
        memory.valider_apprentissage(
            contexte_teto.get("objet_id"), 
            contexte_teto.get("vibration_id")
        )
        speech.parler("D'accord, c'est enregistré dans ma mémoire.")
        contexte_teto = {"en_attente": False}
        return jsonify({"status": "valide", "reponse": response_text})
    
    else:
        # On supprime ou on ignore le lien
        # Note: Assure-toi que memory.supprimer_lien existe dans memory.py
        speech.parler("D'accord, j'ai annulé l'association.")
        contexte_teto = {"en_attente": False}
        return jsonify({"status": "annule", "reponse": response_text})

# NOUVELLE FONCTION (Interne) : Teto pose une question
def teto_pose_question(objet_nom, vibration_texte, objet_id, vibration_id):
    global contexte_teto
    question = f"J'ai reconnu un {objet_nom}, est-ce que c'est bien un {vibration_texte} ?"
    speech.parler(question) # Teto parle !
    
    contexte_teto = {
        "en_attente": True,
        "derniere_question": question,
        "objet_id": objet_id,
        "vibration_id": vibration_id
    }
def mettre_a_jour_contexte(question, objet_id=None, type_sujet=None):
    global contexte_teto
    contexte_teto = {
        "en_attente": True,
        "derniere_question": question,
        "objet_id": objet_id,
        "type": type_sujet
    }
conscience = TetoConscience(memory, speech, mettre_a_jour_contexte)
conscience.start()

if __name__ == '__main__':
    # On vérifie si on est dans le processus principal pour ne pas lancer 
    # la conscience deux fois à cause du debug reloader de Flask
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        conscience.start()
        print("[TETO] 🧠 Conscience activée et en veille...")
        
    app.run(host='0.0.0.0', port=5001, debug=True)