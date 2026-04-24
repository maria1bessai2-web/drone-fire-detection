from ultralytics import YOLO  # Importation de la bibliothèque YOLOv8 pour la détection d'objets (feu ici)
import cv2  # OpenCV pour capturer et manipuler les images de la caméra
import requests  # Pour envoyer des requêtes HTTP (POST) vers le serveur
import serial  # Pour la communication série avec le module GPS
import time  # Pour gérer les délais
import re  # Pour le traitement des chaînes (extraction des coordonnées GPS)
from datetime import datetime  # Pour générer un timestamp dans le nom de l'image

# Chargement du modèle YOLOv8 entraîné pour détecter les incendies
model = YOLO("best.pt")
# Initialisation de la caméra (0 pour une webcam USB branchée sur le Raspberry Pi)
cap = cv2.VideoCapture(0)
# Ouverture du port série pour lire les données du module GPS M8N
gps_port = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
# Adresse du serveur Flask qui va recevoir l’image et les coordonnées (via M2M)
alert_url = 'http://192.168.1.91:5000/alert'  # À remplacer par l’IP réelle de ton serveur
# Fonction qui lit les trames NMEA du GPS et extrait la latitude et la longitude
def get_gps_coords():
    while True:
        line = gps_port.readline().decode('ascii', errors='replace')  # Lire une ligne GPS
        if "$GPGGA" in line:  # Chercher la trame contenant les infos de position
            match = re.match(r".*?,(\d{2})(\d{2}\.\d+),[NS],(\d{3})(\d{2}\.\d+),[EW],.*", line)
            if match:
                lat = float(match.group(1)) + float(match.group(2)) / 60.0  # Conversion en degrés décimaux
                lon = float(match.group(3)) + float(match.group(4)) / 60.0
                return round(lat, 6), round(lon, 6)  # Retourne les coordonnées arrondies
        time.sleep(0.5)  # Attente avant de relire une nouvelle ligne
# Boucle principale : capture d’images, détection, envoi
while True:
    ret, frame = cap.read()  # Capture une image depuis la caméra
    if not ret:
        print(" Impossible de lire la caméra.")
        break  # Sort de la boucle si problème avec la caméra
    # Lancement de la détection avec YOLOv8
    results = model(frame)
    # Affichage du résultat avec les boîtes annotées
    annotated_frame = results[0].plot()
    cv2.imshow("Fire Detection (Drone)", annotated_frame)
    # Si un feu est détecté (présence de boîtes)
    if len(results[0].boxes) > 0:
        print(" Feu détecté ! Envoi de l'alerte...")
        # Enregistre l'image avec un nom basé sur le timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = f"fire_{timestamp}.jpg"
        cv2.imwrite(image_path, frame)
        # Lecture des coordonnées GPS actuelles
        try:
            lat, lon = get_gps_coords()
        except Exception as e:
            print(" Erreur GPS, envoi avec coordonnées par défaut.")
            lat, lon = 36.7525, 3.0423  # Coordonnées par défaut (Alger)
        # Préparation des données à envoyer : image + latitude + longitude
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            data = {'lat': str(lat), 'lon': str(lon)}
            try:
                # Envoi des données au serveur via HTTP POST (M2M)
                response = requests.post(alert_url, files=files, data=data)
                print(" Alerte envoyée :", response.status_code)
            except Exception as e:
                print(" Erreur d’envoi M2M :", e)
    # Sortie de la boucle si l’utilisateur appuie sur 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# Libération des ressources à la fin du programme
cap.release()
cv2.destroyAllWindows()

