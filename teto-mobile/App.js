import React, { useState, useRef, useEffect } from 'react';
import { 
  StyleSheet, View, Text, TouchableOpacity, 
  TextInput, KeyboardAvoidingView, Button, ActivityIndicator, ScrollView 
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';
import { Audio } from 'expo-av';
import { TetoAudioService } from './tetoAudioService.js';

// ADRESSE IP DE TON MAC MINI (À vérifier avec ifconfig)
const MAC_MINI_URL = "http://192.168.1.143:5001";

export default function App() {
  // --- ÉTATS ---
  const [permission, requestPermission] = useCameraPermissions();
  const [recording, setRecording] = useState();
  const [mode, setMode] = useState('ANALYSE'); // ANALYSE ou APPRENDRE
  const [resultat, setResultat] = useState("Teto : Prête");
  const [loading, setLoading] = useState(false);
  const cameraRef = useRef(null);

  // --- ÉTATS DU TISSAGE (CHAMPS DE TEXTE) ---
  const [label, setLabel] = useState("");
  const [category, setCategory] = useState("");
  const [relation, setRelation] = useState("EST_UN");
  const [isListening, setIsListening] = useState(false);

  // --- 1. GESTION DE L'ÉCOUTE CONTINUE (LE BÉBÉ) ---
  useEffect(() => {
    return () => {
      TetoAudioService.stopEveil();
    };
  }, []);

  const toggleContinuousListening = async () => {
    if (isListening) {
      await TetoAudioService.stopEveil();
      setIsListening(false);
      setResultat("Oreille passive : OFF");
    } else {
      const perm = await Audio.requestPermissionsAsync();
      if (perm.status === 'granted') {
        setIsListening(true);
        setResultat("Teto écoute la maison...");
        TetoAudioService.startEveil();
      } else {
        setResultat("Permission micro requise");
      }
    }
  };

  // --- 2. GESTION DE L'AUDITION MANUELLE (MICRO) ---
  async function startRecording() {
    try {
      const perm = await Audio.requestPermissionsAsync();
      if (perm.status === 'granted') {
        await Audio.setAudioModeAsync({ 
          allowsRecordingIOS: true, 
          playsInSilentModeIOS: true 
        });
        const { recording } = await Audio.Recording.createAsync(
          Audio.RecordingOptionsPresets.HIGH_QUALITY
        );
        setRecording(recording);
        setResultat("Teto écoute...");
      }
    } catch (err) {
      console.error('Erreur Micro:', err);
    }
  }

  async function stopRecording() {
    if (!recording) return;
    setRecording(undefined);
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();

    setResultat("Transcription...");
    const formData = new FormData();
    formData.append('audio', { uri, type: 'audio/x-wav', name: 'vibration.wav' });

    try {
      const res = await fetch(`${MAC_MINI_URL}/api/listen`, {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = await res.json();
      setResultat(`Entendu : "${data.vibration}"`);
      setLabel(data.vibration); // Remplit le champ nom automatiquement
    } catch (e) {
      setResultat("Erreur Mac (Micro)");
    }
  }

  // --- 3. GESTION DE LA VISION (ANALYSE & COLLECTE) ---
  const executerAction = async () => {
    if (!cameraRef.current || loading) return;
    setLoading(true);
    setResultat("Teto réfléchit...");

    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.5 });
      
      // On choisit la route selon le mode
      const route = mode === 'ANALYSE' ? 'identifier' : 'collect';

      const response = await fetch(`${MAC_MINI_URL}/${route}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: photo.base64,
          label: label,
          category: category,
          relation: relation,
        }),
      });

      const data = await response.json();
      const messageFinal = data.message || data.nom || "Analyse terminée";
      
      setResultat(messageFinal);
      Speech.speak(messageFinal, { language: 'fr' });
    } catch (e) {
      setResultat("Erreur Mac (Vision)");
      console.log(e);
    } finally {
      setLoading(false);
    }
  };

  // --- RENDU UI ---
  if (!permission) return <View style={styles.container}><ActivityIndicator size="large" /></View>;
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Button title="Donner la Vue à Teto" onPress={requestPermission} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView behavior="padding" style={{flex: 1}}>
      <CameraView style={styles.camera} ref={cameraRef}>
        <View style={styles.overlay}>
          
          {/* ÉCRAN DE RÉSULTAT */}
          <View style={styles.header}>
            <Text style={styles.resText}>{resultat}</Text>
          </View>

          <View style={styles.footer}>
            {/* BOUTON BÉBÉ (ÉCOUTE CONTINUE) */}
            <TouchableOpacity 
              onPress={toggleContinuousListening}
              style={[styles.babyBtn, {backgroundColor: isListening ? '#4CAF50' : '#1f2937'}]}
            >
              <Text style={styles.babyBtnText}>
                {isListening ? "🟢 OREILLE ACTIVE" : "⚪ RÉVEILLER L'OREILLE"}
              </Text>
            </TouchableOpacity>

            {/* FORMULAIRE (Visible seulement en mode APPRENDRE) */}
            {mode === 'APPRENDRE' && (
              <View style={styles.form}>
                <TextInput style={styles.input} placeholder="Nom de l'objet" value={label} onChangeText={setLabel} placeholderTextColor="#999" />
                <TextInput style={styles.input} placeholder="Catégorie (ex: Outil)" value={category} onChangeText={setCategory} placeholderTextColor="#999" />
                <TextInput style={styles.input} placeholder="Relation (ex: EST_UN)" value={relation} onChangeText={setRelation} placeholderTextColor="#999" />
              </View>
            )}

            {/* BOUTONS D'ACTION */}
            <View style={styles.controls}>
              {/* MICRO MANUEL */}
              <TouchableOpacity 
                style={[styles.micBtn, recording && {backgroundColor: '#ef4444'}]} 
                onPressIn={startRecording} 
                onPressOut={stopRecording}
              >
                <Text style={{fontSize: 28}}>{recording ? "🛑" : "🎤"}</Text>
              </TouchableOpacity>

              {/* DÉCLENCHEUR PHOTO */}
              <TouchableOpacity style={styles.shutter} onPress={executerAction}>
                {loading ? <ActivityIndicator color="black" /> : <View style={styles.shutterInner} />}
              </TouchableOpacity>
            </View>

            {/* SÉLECTEUR DE MODE */}
            <View style={styles.selector}>
              <TouchableOpacity onPress={() => setMode('ANALYSE')}>
                <Text style={mode === 'ANALYSE' ? styles.activeMode : styles.inactiveMode}>ANALYSE</Text>
              </TouchableOpacity>
              <View style={styles.separator} />
              <TouchableOpacity onPress={() => setMode('APPRENDRE')}>
                <Text style={mode === 'APPRENDRE' ? styles.activeMode : styles.inactiveMode}>APPRENDRE</Text>
              </TouchableOpacity>
            </View>

          </View>
        </View>
      </CameraView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'black', justifyContent: 'center' },
  camera: { flex: 1 },
  overlay: { flex: 1, justifyContent: 'space-between', padding: 20 },
  header: { marginTop: 40 },
  resText: { color: 'white', backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: 18, borderRadius: 12, textAlign: 'center', fontWeight: 'bold', fontSize: 16, borderWeight: 1, borderColor: '#3b82f6' },
  footer: { marginBottom: 20, alignItems: 'center', width: '100%' },
  babyBtn: { paddingVertical: 10, paddingHorizontal: 20, borderRadius: 20, marginBottom: 15, borderWeight: 1, borderColor: '#374151' },
  babyBtnText: { color: 'white', fontSize: 11, fontWeight: '800', letterSpacing: 1 },
  form: { width: '100%', marginBottom: 15, gap: 8 },
  input: { backgroundColor: 'white', padding: 12, borderRadius: 8, color: 'black', fontSize: 16 },
  controls: { flexDirection: 'row', alignItems: 'center', marginBottom: 25 },
  micBtn: { width: 70, height: 70, borderRadius: 35, backgroundColor: '#374151', justifyContent: 'center', alignItems: 'center', marginRight: 40, elevation: 5 },
  shutter: { width: 85, height: 85, borderRadius: 42.5, borderWidth: 6, borderColor: 'white', justifyContent: 'center', alignItems: 'center' },
  shutterInner: { width: 60, height: 60, borderRadius: 30, backgroundColor: 'white' },
  selector: { flexDirection: 'row', backgroundColor: 'rgba(17, 24, 39, 0.8)', paddingVertical: 12, paddingHorizontal: 25, borderRadius: 30, alignItems: 'center' },
  separator: { width: 1, height: 20, backgroundColor: '#374151', mx: 15 },
  activeMode: { color: '#3b82f6', fontWeight: '900', fontSize: 14, marginHorizontal: 15 },
  inactiveMode: { color: 'white', fontWeight: '400', fontSize: 14, marginHorizontal: 15 }
});