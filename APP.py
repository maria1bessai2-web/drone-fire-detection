from flask import Flask, request, redirect  # Flask pour créer le serveur web
import os  # Pour gérer les fichiers et les répertoires
import pygame  # Pour jouer un son d’alerte
from datetime import datetime  # Pour horodater les alertes
import json  # Pour stocker les alertes en format JSON

# Initialisation de l’application Flask
app = Flask(__name__)

# Chemin vers le dossier où seront enregistrées les images des alertes
ALERT_FOLDER = "static/alerts"
# Fichier JSON qui stockera les données des alertes
DATA_FILE = "static/data.json"

# Créer le dossier s’il n’existe pas déjà
os.makedirs(ALERT_FOLDER, exist_ok=True)

# Initialisation du module audio pour jouer l’alarme
pygame.mixer.init()
pygame.mixer.music.load("static/alarme.mp3")  # Charger le fichier audio

# Fonction pour enregistrer une alerte dans le fichier JSON
def save_alert(image_filename, lat, lon):
    if not os.path.exists(DATA_FILE):  # Si le fichier n'existe pas, on le crée
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(DATA_FILE, 'r') as f:
        alerts = json.load(f)  # Charger les alertes existantes

    # Créer une nouvelle alerte
    alert_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Date et heure
        "image": image_filename,  # Nom du fichier image
        "lat": lat,  # Latitude
        "lon": lon   # Longitude
    }
    alerts.append(alert_data)  # Ajouter l’alerte à la liste

    # Enregistrer la liste mise à jour dans le fichier
    with open(DATA_FILE, 'w') as f:
        json.dump(alerts, f, indent=4)

# Route pour renvoyer le fichier JSON des données à l’interface web
@app.route('/data.json')
def data():
    return app.send_static_file('data.json')
# Route pour recevoir une alerte envoyée par le Raspberry Pi
@app.route('/alert', methods=['POST'])
def alert():
    lat = request.form.get('lat')  # Récupérer la latitude
    lon = request.form.get('lon')  # Récupérer la longitude
    image = request.files['image']  # Récupérer l’image

    # Vérifier si toutes les données sont présentes
    if not lat or not lon or not image:
        return "Requête invalide", 400

    # Générer un nom unique pour l’image avec timestamp
    filename = datetime.now().strftime("fire_%Y%m%d_%H%M%S.jpg")
    filepath = os.path.join(ALERT_FOLDER, filename)
    image.save(filepath)  # Sauvegarder l’image dans le dossier des alertes
    save_alert(filename, lat, lon)  # Enregistrer l’alerte dans le fichier JSON
    pygame.mixer.music.play()  # Jouer le son d’alarme
    return "Alerte reçue"
# Route principale redirigeant vers le tableau de bord
@app.route('/')
def index():
    return redirect("/dashboard")

# Route qui affiche la page web du tableau de bord
@app.route('/dashboard')
def dashboard():
    return app.send_static_file("serv.html")

# Lancer le serveur sur toutes les interfaces, en mode debug
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
