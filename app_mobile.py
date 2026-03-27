from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
from coeur_sauvegarde import IASauvegarde 

app = Flask(__name__)
ia = IASauvegarde() # Ton intelligence reste la même

@app.route('/identifier', methods=['POST'])
def identifier():
    # 1. On récupère les données JSON envoyées par React
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"objet": "Erreur", "status": "pas_d_image"})

    # 2. Décodage de l'image Base64 vers OpenCV
    img_data = base64.b64decode(data['image'])
    npimg = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # 3. Ton IA analyse l'image exactement comme avant
    resultat = ia.instinct_reconnaissance(frame)
    
    # 4. On renvoie le nom de l'objet à l'iPhone
    return jsonify({
        "objet": resultat if resultat else "Inconnu",
        "status": "trouvé" if resultat else "pas_trouvé"
    })

if __name__ == '__main__':
    print("\n[SERVEUR HYBRIDE] En attente de l'iPhone...")
    # L'IP de ton PC à la Réunion (ex: 192.168.1.12)
    app.run(host='0.0.0.0', port=5000, debug=False)