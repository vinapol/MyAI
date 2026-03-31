import { Audio } from 'expo-av';

// Remplace par l'IP de ton Mac Mini
const TETO_MAC_URL = "http://192.168.1.143:5001/api/continu";

export const TetoAudioService = {
  isListening: false,
  recording: null,

  startEveil: async function() {
    if (this.isListening) return;
    this.isListening = true;
    console.log("Teto : Oreille activée.");
    this.boucleEcoute();
  },

  stopEveil: async function() {
    this.isListening = false;
    console.log("Teto : Oreille mise en sommeil.");
    if (this.recording) {
      try {
        await this.recording.stopAndUnloadAsync();
      } catch (e) {
        // Déjà arrêté
      }
      this.recording = null;
    }
  },

  boucleEcoute: async function() {
    while (this.isListening) {
      try {
        // 1. Configurer l'audio pour l'enregistrement
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
        });

        // 2. DÉMARRER L'ENREGISTREMENT (La syntaxe correcte est ici)
        const { recording } = await Audio.Recording.createAsync(
          Audio.RecordingOptionsPresets.HIGH_QUALITY
        );
        this.recording = recording;

        console.log("Teto enregistre une séquence de 10s...");

        // 3. Attendre 10 secondes
        await new Promise(resolve => setTimeout(resolve, 10000));

        if (!this.isListening) break;

        // 4. Arrêter l'enregistrement
        await this.recording.stopAndUnloadAsync();
        const uri = this.recording.getURI();
        this.recording = null;

        // 5. Envoyer au Mac Mini
        this.propagerVibration(uri);

      } catch (error) {
        console.error("Erreur dans la boucle de Teto:", error);
        this.isListening = false; // Arrêt de sécurité en cas d'erreur
      }
    }
  },

  propagerVibration: async function(uri) {
    const formData = new FormData();
    formData.append('audio', {
      uri: uri,
      type: 'audio/x-wav',
      name: 'vibration_continue.wav',
    });

    try {
      const response = await fetch(TETO_MAC_URL, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      const data = await response.json();
      console.log("Mac Mini a reçu la vibration :", data.texte || "Silence");
    } catch (e) {
      console.log("Erreur d'envoi au Mac Mini (Vérifie l'IP et le port 5001)");
    }
  }
};