from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import os
from coeur_sauvegarde import IASauvegarde 

app = Flask(__name__)
CORS(app) # Autorise la connexion depuis l'iPhone
ia = IASauvegarde()

# Création automatique du dossier si Moïse ne l'a pas fait
if not os.path.exists("collection"):
    os.makedirs("collection")

@app.route('/identifier', methods=['POST'])
def identifier():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"objet": "Erreur", "status": "pas_d_image"})

        img_data = base64.b64decode(data['image'])
        npimg = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        resultat = ia.instinct_reconnaissance(frame) # Utilise ton coeur_sauvegarde
        
        if resultat:
            reponse = f"Je vois un {resultat}."
        else:
            reponse = "Mes capteurs sont perplexes. Est-ce un nouvel objet ?"
        
        return jsonify({
            "objet": resultat if resultat else "Inconnu",
            "message_vocal": reponse, # Nouveau champ pour la voix
            "status": "trouvé" if resultat else "pas_trouvé"
    })
    except Exception as e:
        print(f"Erreur Identification: {e}")
        return jsonify({"status": "erreur"}), 500

@app.route('/apprendre', methods=['POST'])
def apprendre():
    try:
        data = request.json
        if not data or 'image' not in data or 'label' not in data:
            return jsonify({"status": "erreur", "message": "Données incomplètes"})

        img_data = base64.b64decode(data['image'])
        nom_objet = data['label']
        
        # Conversion pour OpenCV
        npimg = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        nom_nettoye = nom_objet.lower().replace(" ", "_")
        nouveau_chemin = f"collection/{nom_nettoye}.jpg"
        cv2.imwrite(nouveau_chemin, gris)
        
        ia.memoire[nouveau_chemin] = {"nom": nom_nettoye}
        ia.sauvegarder() # Met à jour memoire_enfant.json
        
        return jsonify({
            "status": "succes", 
            "message": f"Merci Moïse. Je range l'image de ce {nom_objet} dans ma mémoire."
        })
    except Exception as e:
        print(f"Erreur Apprentissage: {e}")
        return jsonify({"status": "erreur"}), 500

if __name__ == '__main__':
    print("\n[SERVEUR HYBRIDE] En attente de l'iPhone sur le port 5001...")
    # 0.0.0.0 est vital pour que l'iPhone trouve le Mac
    app.run(host='0.0.0.0', port=5001, debug=True)