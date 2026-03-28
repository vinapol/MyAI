import React, { useState, useRef } from 'react';
import { StyleSheet, View, Text, PanResponder, TextInput, Dimensions, TouchableOpacity, Animated } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import Svg, { Rect } from 'react-native-svg';
import * as Speech from 'expo-speech';
import * as Haptics from 'expo-haptics';

const { width, height } = Dimensions.get('window');

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [mode, setMode] = useState('ANALYSE'); // ANALYSE ou APPRENDRE
  const [resultat, setResultat] = useState("Prêt");
  const [label, setLabel] = useState(""); 
  const [rect, setRect] = useState({ x: 0, y: 0, w: 0, h: 0, active: false });
  const cameraRef = useRef(null);

  const parler = (texte) => {
  const options = {
    language: 'fr-FR', // Miku qui parle français
    pitch: 20.0,       // On monte le ton très haut (Hatsune Miku est vers 1.4 - 1.6)
    rate: 1.1,        // On accélère un peu le débit pour le côté "pop"
  };
  Speech.speak(texte, options);
};

  const declencherIA = async () => {
    if (!cameraRef.current) return;
    
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy); 
    parler("J'analyse ce que je vois..."); // L'IA annonce son action
    setResultat("Traitement...");

    try {
      const photo = await cameraRef.current.takePictureAsync({ 
        base64: true, 
        quality: 0.3,
        skipProcessing: true // Accélère la capture
      });

      const endpoint = mode === 'APPRENDRE' ? '/apprendre' : '/identifier';
      
      const response = await fetch(`http://192.168.1.143:5001${endpoint}`, {
        method: 'POST',
        body: JSON.stringify({ 
          image: photo.base64, 
          label: mode === 'APPRENDRE' ? label.trim() : "" 
        }),
        headers: { 'Content-Type': 'application/json' },
      });
      
      const data = await response.json();

      if (mode === 'APPRENDRE') {
          parler(data.message); // Lit "Merci Moïse..."
          setLabel("");
    } else {
          setResultat(data.objet);
          parler(data.message_vocal); // Lit "Je vois un..." ou "Mes capteurs sont perplexes..."
    }
    } catch (e) {
      setResultat("Erreur de liaison");
      console.log(e);
    }
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        const { locationX, locationY } = evt.nativeEvent;
        setRect({ x: locationX, y: locationY, w: 0, h: 0, active: true });
      },
      onPanResponderMove: (evt, gestureState) => {
        setRect(prev => ({ ...prev, w: gestureState.dx, h: gestureState.dy }));
      },
      onPanResponderRelease: () => {
        // On ne déclenche plus l'IA au lâcher de doigt pour éviter les bugs
        // L'utilisateur doit maintenant appuyer sur le gros bouton blanc
      },
    })
  ).current;

  if (!permission?.granted) return <View style={styles.container}><Text onPress={requestPermission} style={styles.statusText}>Activer Caméra</Text></View>;

  return (
    <View style={styles.container}>
      <CameraView style={StyleSheet.absoluteFill} ref={cameraRef} facing="back" />

      {/* Zone de dessin du rectangle */}
      <View style={StyleSheet.absoluteFill} {...panResponder.panHandlers}>
        {rect.active && (
          <Svg height="100%" width="100%">
            <Rect
              x={rect.w > 0 ? rect.x : rect.x + rect.w}
              y={rect.h > 0 ? rect.y : rect.y + rect.h}
              width={Math.abs(rect.w)}
              height={Math.abs(rect.h)}
              fill="rgba(0, 255, 0, 0.1)"
              stroke="#00FF00"
              strokeWidth="2"
            />
          </Svg>
        )}
      </View>

      {/* Interface type Apple */}
      <View style={styles.overlay} pointerEvents="box-none">
        <View style={styles.topInfo}>
          <Text style={styles.resultText}>{resultat}</Text>
        </View>

        <View style={styles.bottomControls}>
          {mode === 'APPRENDRE' && (
            <TextInput
              style={styles.input}
              placeholder="Nom de l'objet..."
              placeholderTextColor="#999"
              value={label}
              onChangeText={setLabel}
            />
          )}

          {/* Sélecteur de mode coulissant */}
          <View style={styles.selector}>
            <TouchableOpacity onPress={() => setMode('ANALYSE')}>
              <Text style={[styles.modeText, mode === 'ANALYSE' && styles.modeActive]}>ANALYSE</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setMode('APPRENDRE')} style={{ marginLeft: 20 }}>
              <Text style={[styles.modeText, mode === 'APPRENDRE' && styles.modeActive]}>APPRENDRE</Text>
            </TouchableOpacity>
          </View>

          {/* Bouton de capture blanc (Style iOS) */}
          <TouchableOpacity style={styles.captureBtn} onPress={declencherIA}>
            <View style={styles.captureInternal} />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'black' },
  overlay: { ...StyleSheet.absoluteFillObject, justifyContent: 'space-between', paddingVertical: 60 },
  topInfo: { alignItems: 'center' },
  resultText: { color: '#00FF00', fontSize: 18, fontWeight: 'bold', backgroundColor: 'rgba(0,0,0,0.6)', padding: 10, borderRadius: 10 },
  bottomControls: { alignItems: 'center', width: '100%' },
  input: { backgroundColor: 'rgba(255,255,255,0.2)', color: 'white', width: '80%', padding: 15, borderRadius: 10, marginBottom: 20, textAlign: 'center' },
  selector: { flexDirection: 'row', marginBottom: 20 },
  modeText: { color: 'white', fontWeight: 'bold', fontSize: 14, opacity: 0.5 },
  modeActive: { color: '#FFD700', opacity: 1 }, // Jaune pour le mode actif
  captureBtn: { width: 80, height: 80, borderRadius: 40, borderWidth: 4, borderColor: 'white', justifyContent: 'center', alignItems: 'center' },
  captureInternal: { width: 65, height: 65, borderRadius: 32.5, backgroundColor: 'white' }
});