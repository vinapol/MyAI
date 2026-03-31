import math

class ProtocoleApprentissage:
    def __init__(self, seuil_perplexite=0.20):
        # Le seuil (20%) définit à quel point Teto est "sensible" au doute
        self.seuil_perplexite = seuil_perplexite

    def analyser_incertitude(self, scores):
        """
        Applique le principe d'Énergie Libre : 
        Si l'écart entre les deux meilleures hypothèses est trop faible, 
        le stress augmente et l'IA suspend son calcul.
        """
        if not scores:
            return "CHAOS", None

        # Tri des scores par importance (nombre de points ORB)
        scores_tries = sorted(scores, key=lambda x: x['score'], reverse=True)
        
        meilleur = scores_tries[0]
        
        # 1. Cas du Chaos : Pas assez de points du tout
        if meilleur['score'] < 15:
            return "INCONNU", None

        # 2. Cas de la Perplexité : Conflit entre deux chemins logiques
        if len(scores_tries) > 1:
            second = scores_tries[1]
            # Calcul de la marge de confiance
            marge = (meilleur['score'] - second['score']) / meilleur['score']
            
            if marge < self.seuil_perplexite:
                return "PERPLEXE", [meilleur['nom'], second['nom']]

        # 3. Cas de la Cohérence : L'IA est sûre d'elle
        return "CERTITUDE", meilleur['nom']