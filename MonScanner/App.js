import React, { useState, useRef } from 'react';
import { StyleSheet, View, Text, PanResponder } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import Svg, { Rect } from 'react-native-svg';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [resultat, setResultat] = useState("Glissez pour tracer un rectangle");
  
  // Coordonnées du rectangle
  const [rect, setRect] = useState({ x: 0, y: 0, w: 0, h: 0, active: false });
  const startPos = useRef({ x: 0, y: 0 });
  const cameraRef = useRef(null);

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        // Point de départ du toucher
        const { locationX, locationY } = evt.nativeEvent;
        startPos.current = { x: locationX, y: locationY };
        setRect({ x: locationX, y: locationY, w: 0, h: 0, active: true });
      },
      onPanResponderMove: (evt, gestureState) => {
        // Mise à jour de la taille pendant le glissement
        setRect(prev => ({
          ...prev,
          w: gestureState.dx,
          h: gestureState.dy
        }));
      },
      onPanResponderRelease: () => {
        // Analyse quand on lâche le doigt
        scannerObjet();
        // Optionnel : on cache le rectangle après 1 seconde
        setTimeout(() => setRect(prev => ({ ...prev, active: false })), 1000);
      },
    })
  ).current;

  const scannerObjet = async () => {
    if (cameraRef.current) {
      setResultat("Analyse de la zone...");
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.5 });
      
      try {
        // Vérifie bien que ton Python utilise /identifier ou /scanner
        let response = await fetch('http://192.168.1.12:5000/identifier', {
          method: 'POST',
          body: JSON.stringify({ image: photo.base64 }),
          headers: { 'Content-Type': 'application/json' },
        });
        let data = await response.json();
        setResultat(data.objet);
      } catch (e) {
        setResultat("Erreur Connexion PC");
      }
    }
  };

  if (!permission?.granted) return <View style={styles.container}><Text onPress={requestPermission}>Activer Caméra</Text></View>;

  return (
    <View style={styles.container} {...panResponder.panHandlers}>
      <CameraView style={styles.camera} ref={cameraRef} facing="back">
        
        {/* Affichage du rectangle SVG */}
        {rect.active && (
          <Svg height="100%" width="100%" style={styles.svg}>
            <Rect
              x={rect.w > 0 ? rect.x : rect.x + rect.w}
              y={rect.h > 0 ? rect.y : rect.y + rect.h}
              width={Math.abs(rect.w)}
              height={Math.abs(rect.h)}
              fill="rgba(0, 255, 0, 0.2)"
              stroke="#00FF00"
              strokeWidth="2"
            />
          </Svg>
        )}
        
        <View style={styles.overlay}>
          <Text style={styles.text}>{resultat}</Text>
        </View>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'black' },
  camera: { flex: 1 },
  svg: { position: 'absolute', top: 0, left: 0 },
  overlay: { flex: 1, justifyContent: 'flex-start', alignItems: 'center', paddingTop: 60 },
  text: { fontSize: 18, color: 'white', padding: 12, backgroundColor: 'rgba(0,0,0,0.8)', borderRadius: 15, textAlign: 'center' },
});