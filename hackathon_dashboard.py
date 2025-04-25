import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import os
import json
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Tableau de Bord d'Évaluation HACKVERSE 2025",
    page_icon="🏆",
    layout="wide"
)

# Style CSS pour améliorer l'apparence
st.markdown("""
<style>
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .team-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #dee2e6;
    }
    .score-badge {
        background-color: #007bff;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
    }
    .subtitle {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .member-card {
        background-color: #f1f3f5;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# Titre de l'application
st.markdown("<div class='title'>Tableau de Bord d'Évaluation HACKVERSE 2025</div>", unsafe_allow_html=True)

# ------ FONCTIONS DE SAUVEGARDE ET CHARGEMENT CSV ------

# Fonction pour convertir les évaluations en DataFrame plat pour export CSV
def evaluations_to_dataframe(evaluations):
    data = []
    
    for team_name, team_data in evaluations.items():
        row = {
            "team_name": team_name,
            # Données collectives
            "collective_uiDesign": team_data["collective"]["uiDesign"],
            "collective_apiImplementation": team_data["collective"]["apiImplementation"],
            "collective_database": team_data["collective"]["database"],
            "collective_authentication": team_data["collective"]["authentication"],
            "collective_crudOperations": team_data["collective"]["crudOperations"],
            "collective_requiredFeatures": team_data["collective"]["requiredFeatures"],
            "collective_bonusFeatures": team_data["collective"]["bonusFeatures"],
            "collective_documentation": team_data["collective"]["documentation"],
            "collective_teamCollaboration": team_data["collective"]["teamCollaboration"],
            "collective_deployment": team_data["collective"]["deployment"],
            "collective_totalScore": team_data["collective"]["totalScore"],
            "finalScore": team_data["finalScore"]
        }
        
        # Ajouter les données individuelles pour chaque membre
        for member_name, member_data in team_data["individual"].items():
            # S'assurer que member_name est bien une chaîne de caractères
            member_name_str = str(member_name)
            member_safe_name = member_name_str.replace(" ", "_").replace(".", "").replace(",", "")
            
            try:
                row[f"individual_{member_safe_name}_webProgramming"] = member_data["webProgramming"]
                row[f"individual_{member_safe_name}_algorithmic"] = member_data["algorithmic"]
                row[f"individual_{member_safe_name}_totalScore"] = member_data["totalScore"]
            except KeyError:
                # Si certaines clés sont manquantes, utiliser des valeurs par défaut
                if "webProgramming" not in member_data:
                    row[f"individual_{member_safe_name}_webProgramming"] = 0.0
                if "algorithmic" not in member_data:
                    row[f"individual_{member_safe_name}_algorithmic"] = 0.0
                if "totalScore" not in member_data:
                    row[f"individual_{member_safe_name}_totalScore"] = 0.0
        
        data.append(row)
    
    return pd.DataFrame(data)

# Fonction pour sauvegarder les évaluations dans un CSV
def save_evaluations_to_csv(evaluations, filename="hackathon_evaluations.csv"):
    df = evaluations_to_dataframe(evaluations)
    df.to_csv(filename, index=False)
    
    # Créer également une sauvegarde avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"hackathon_evaluations_{timestamp}.csv"
    # df.to_csv(backup_filename, index=False)
    
    return filename, backup_filename

# Fonction pour reconstruire la structure des évaluations à partir du DataFrame
def dataframe_to_evaluations(df):
    evaluations = {}
    
    for _, row in df.iterrows():
        team_name = row["team_name"]
        
        # Initialiser la structure pour cette équipe
        evaluations[team_name] = {
            "collective": {
                "uiDesign": float(row["collective_uiDesign"]),
                "apiImplementation": float(row["collective_apiImplementation"]),
                "database": float(row["collective_database"]),
                "authentication": float(row["collective_authentication"]),
                "crudOperations": float(row["collective_crudOperations"]),
                "requiredFeatures": float(row["collective_requiredFeatures"]),
                "bonusFeatures": float(row["collective_bonusFeatures"]),
                "documentation": float(row["collective_documentation"]),
                "teamCollaboration": float(row["collective_teamCollaboration"]),
                "deployment": float(row["collective_deployment"]),
                "totalScore": float(row["collective_totalScore"])
            },
            "individual": {},
            "finalScore": float(row["finalScore"])
        }
        
        # Extraire les données individuelles
        individual_columns = [col for col in row.index if col.startswith("individual_")]
        
        # Grouper par membre
        member_prefixes = set()
        for col in individual_columns:
            parts = col.split('_')
            if len(parts) >= 3:
                # Prendre tout sauf "individual" et le critère (dernier élément)
                member_prefix = '_'.join(parts[1:-1])
                member_prefixes.add(member_prefix)
        
        # Traiter chaque membre séparément
        for member_prefix in member_prefixes:
            # Convertir le préfixe en nom en remplaçant les underscores par des espaces
            member_name = member_prefix.replace('_', ' ')
            
            # Créer un dictionnaire pour ce membre
            member_data = {}
            
            # Remplir les données pour ce membre
            for criterion in ['webProgramming', 'algorithmic', 'totalScore']:
                col_name = f'individual_{member_prefix}_{criterion}'
                if col_name in row:
                    try:
                        member_data[criterion] = float(row[col_name])
                    except (ValueError, TypeError):
                        # En cas d'erreur, utiliser 0
                        member_data[criterion] = 0.0
                else:
                    member_data[criterion] = 0.0
            
            # Ajouter le membre à la structure d'évaluation
            evaluations[team_name]["individual"][member_name] = member_data
    
    return evaluations

# Fonction pour charger les évaluations depuis un CSV
def load_evaluations_from_csv(filename="hackathon_evaluations.csv", silent=False):
    try:
        df = pd.read_csv(filename)
        return dataframe_to_evaluations(df)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        if not silent:
            st.warning(f"Le fichier {filename} n'a pas été trouvé ou est vide.")
        return None

# Fonction pour convertir récursivement toutes les valeurs numériques en flottants et remplacer les NaN par 0
def convert_values_to_float(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (int, float)):
                # Convertir en float et remplacer NaN par 0
                data[key] = 0.0 if pd.isna(float(value)) else float(value)
            elif isinstance(value, dict):
                convert_values_to_float(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, (int, float)):
                        # Convertir en float et remplacer NaN par 0
                        value[i] = 0.0 if pd.isna(float(item)) else float(item)
                    elif isinstance(item, (dict, list)):
                        convert_values_to_float(item)
    return data

# Fonction pour charger les données CSV
@st.cache_data
def load_data():
    try:
        # Chargement depuis le dossier de l'application si disponible
        file_path = "data.csv"
        df = pd.read_csv(file_path)
        return df
    except:
        # Si le fichier n'est pas trouvé, utiliser un exemple minimal pour le test
        st.warning("Fichier CSV non trouvé. Utilisation de données d'exemple.")
        # Création de données d'exemple minimales
        data = {
            "timestamp": ["16/04/2025 13:09:46", "16/04/2025 14:30:21", "16/04/2025 15:45:33"],
            "team_name": ["TEK", "CodeMasters", "DevWarriors"],
            "team_description": [
                "L'informatique au service du développement", 
                "Programmation et innovation", 
                "Développement d'applications mobiles"
            ],
            "leader_name": ["DJOMO DE DJOMO Karlyn", "MBARGA Jean", "FOUDA Marie"],
            "leader_email": ["dedjomokarlyn@gmail.com", "mbarga.jean@gmail.com", "marie.fouda@gmail.com"],
            "leader_github": ["https://github.com/DeDjomo", "https://github.com/MbargaJ", "https://github.com/FoudaM"],
            "member1_name": ["MBIAKE Emmanuella Rose", "KAMGA Pierre", "ESSOMBA Paul"],
            "member1_email": ["emmanuellambiake127@gmail.com", "pierre.kamga@gmail.com", "paul.essomba@gmail.com"],
            "member1_github": ["https://github.com/EmmanuellaM", "https://github.com/PierreK", "https://github.com/PaulE"],
            "member2_name": ["DJUSSE TAMENO Christian Tresor", "NANA Claire", "BELINGA Serge"],
            "member2_email": ["christiandjusse@gmail.com", "claire.nana@gmail.com", "serge.belinga@gmail.com"],
            "member2_github": ["https://github.com/Djusse", "https://github.com/ClaireN", "https://github.com/SergeB"]
        }
        return pd.DataFrame(data)

# Chargement des données
data = load_data()

# Transformation des données en format plus facile à utiliser
def transform_data(df):
    teams = []
    for i, row in df.iterrows():
        # Assurer que le nom de l'équipe est valide et unique
        team_name = row.get("team_name", "")
        if pd.isna(team_name) or team_name == "":
            team_name = f"Équipe_{i}"  # Utiliser un index si le nom est manquant
            
        team = {
            "timestamp": row.get("timestamp", ""),
            "teamName": team_name,
            "teamDescription": row.get("team_description", ""),
            "leader": {
                "name": row.get("leader_name", ""),
                "email": row.get("leader_email", ""),
                "phone": row.get("leader_phone", ""),
                "cycle": row.get("leader_cycle", ""),
                "level": row.get("leader_level", ""),
                "department": row.get("leader_department", ""),
                "github": row.get("leader_github", ""),
                "frontendSkill": row.get("leader_frontend", ""),
                "backendSkill": row.get("leader_backend", ""),
                "databaseSkill": row.get("leader_database", ""),
                "devopsSkill": row.get("leader_devops", ""),
                "languages": row.get("leader_languages", "")
            },
            "member1": {
                "name": row.get("member1_name", ""),
                "phone": row.get("member1_phone", ""),
                "cycle": row.get("member1_cycle", ""),
                "level": row.get("member1_level", ""),
                "department": row.get("member1_department", ""),
                "email": row.get("member1_email", ""),
                "github": row.get("member1_github", ""),
                "experience": row.get("member1_experience", ""),
                "frontendSkill": row.get("member1_frontend", ""),
                "backendSkill": row.get("member1_backend", ""),
                "databaseSkill": row.get("member1_database", ""),
                "languages": row.get("member1_languages", "")
            },
            "member2": {
                "name": row.get("member2_name", ""),
                "phone": row.get("member2_phone", ""),
                "cycle": row.get("member2_cycle", ""),
                "level": row.get("member2_level", ""),
                "department": row.get("member2_department", ""),
                "email": row.get("member2_email", ""),
                "github": row.get("member2_github", ""),
                "experience": row.get("member2_experience", ""),
                "frontendSkill": row.get("member2_frontend", ""),
                "backendSkill": row.get("member2_backend", ""),
                "databaseSkill": row.get("member2_database", ""),
                "languages": row.get("member2_languages", "")
            },
            "projects": row.get("team_projects", ""),
            "previousHackathons": row.get("previous_hackathons", ""),
            "howHeard": row.get("how_heard", ""),
            "specialNeeds": row.get("special_needs", "")
        }
        teams.append(team)
    return teams

teams_data = transform_data(data)

# Ajout d'un bouton de rechargement dans la barre latérale
if st.sidebar.button("🔄 Recharger les données sauvegardées"):
    loaded_evaluations = load_evaluations_from_csv(silent=False)
    if loaded_evaluations:
        st.session_state.evaluations = loaded_evaluations
        st.success("Évaluations rechargées avec succès!")
        st.rerun()
    else:
        st.error("Aucune sauvegarde trouvée à charger.")

# Initialisation de l'état des évaluations si c'est la première visite
if 'evaluations' not in st.session_state:
    # Essayer d'abord de charger depuis le CSV
    loaded_evaluations = load_evaluations_from_csv(silent=True)
    
    if loaded_evaluations:
        evaluations = loaded_evaluations
        st.sidebar.success("✅ Évaluations chargées depuis la sauvegarde")
    else:
        # Si pas de CSV, initialiser avec des valeurs par défaut
        evaluations = {}
        for team in teams_data:
            # Assurer que les noms des membres sont valides et présents
            leader_name = team["leader"]["name"] if team["leader"]["name"] else "Chef d'équipe"
            member1_name = team["member1"]["name"] if team["member1"]["name"] else "Membre 1"
            member2_name = team["member2"]["name"] if team["member2"]["name"] else "Membre 2"
            
            evaluations[team["teamName"]] = {
                "collective": {
                    "uiDesign": 0.0,
                    "apiImplementation": 0.0,
                    "database": 0.0,
                    "authentication": 0.0,
                    "crudOperations": 0.0,
                    "requiredFeatures": 0.0,
                    "bonusFeatures": 0.0,
                    "documentation": 0.0,
                    "teamCollaboration": 0.0,
                    "deployment": 0.0,
                    "totalScore": 0.0
                },
                "individual": {
                    leader_name: {
                        "webProgramming": 0.0,
                        "algorithmic": 0.0,
                        "totalScore": 0.0
                    },
                    member1_name: {
                        "webProgramming": 0.0,
                        "algorithmic": 0.0,
                        "totalScore": 0.0
                    },
                    member2_name: {
                        "webProgramming": 0.0,
                        "algorithmic": 0.0,
                        "totalScore": 0.0
                    }
                },
                "finalScore": 0.0
            }
    st.session_state.evaluations = evaluations
else:
    evaluations = st.session_state.evaluations

# Convertir toutes les valeurs numériques en flottants pour éviter les erreurs de type
evaluations = convert_values_to_float(evaluations)

# Fonction pour calculer les scores finaux
def calculate_final_score(evaluations, team_name):
    team_eval = evaluations[team_name]
    
    # Calculer le score collectif (moyenne des critères)
    collective_values = [float(value) for key, value in team_eval["collective"].items() if key != "totalScore"]
    if len(collective_values) > 0:
        team_eval["collective"]["totalScore"] = round(sum(collective_values) / len(collective_values), 2)
    else:
        team_eval["collective"]["totalScore"] = 0.0
    
    # Calculer les scores individuels
    for member, scores in team_eval["individual"].items():
        individual_values = [float(value) for key, value in scores.items() if key != "totalScore"]
        if len(individual_values) > 0:
            scores["totalScore"] = round(sum(individual_values) / len(individual_values), 2)
        else:
            scores["totalScore"] = 0.0
    
    # Calculer le score final de l'équipe selon la formule:
    # Note équipe = (Note sur l'exercice collectif / 2) + (Somme des notes individuelles / 3) / 2
    collective_score = float(team_eval["collective"]["totalScore"])
    individual_scores = [float(member_scores["totalScore"]) for member_scores in team_eval["individual"].values()]
    
    # Vérifier si la liste des scores individuels n'est pas vide
    if individual_scores:
        individual_avg = sum(individual_scores) / len(individual_scores)
    else:
        individual_avg = 0.0
    
    # Calculer le score final
    team_eval["finalScore"] = round((collective_score / 2) + (individual_avg / 2), 2)
    
    # Vérifier si le score final est NaN et le remplacer par 0
    if pd.isna(team_eval["finalScore"]):
        team_eval["finalScore"] = 0.0
    
    return team_eval

# Interface utilisateur avec onglets
tab1, tab2 = st.tabs(["Évaluation des équipes", "Classement général"])

with tab1:
    # Barre de recherche
    search_term = st.text_input("🔍 Rechercher une équipe ou un membre", "")
    
    # Filtrer les équipes en fonction du terme de recherche
    filtered_teams = teams_data
    if search_term:
        filtered_teams = [
            team for team in teams_data if 
            search_term.lower() in team["teamName"].lower() or
            search_term.lower() in team["leader"]["name"].lower() or
            search_term.lower() in team["member1"]["name"].lower() or
            search_term.lower() in team["member2"]["name"].lower()
        ]
    
    if not filtered_teams:
        st.warning("Aucune équipe ne correspond à votre recherche.")
    else:
        # Afficher les équipes sous forme de grille
        col1, col2 = st.columns(2)
        
        for i, team in enumerate(filtered_teams):
            # Alterner entre les colonnes
            col = col1 if i % 2 == 0 else col2
            
            with col:
                # Card-like container with shadow
                final_score = calculate_final_score(evaluations, team['teamName'])['finalScore']
                # Vérifier et remplacer NaN par 0
                if pd.isna(final_score):
                    final_score = 0.0
                st.markdown(f"<div style='border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'><h3>{team['teamName']} - {final_score}/20</h3>", unsafe_allow_html=True)
                
                st.markdown(f"**Description:** {team['teamDescription']}")
                
                # Informations sur l'équipe
                st.markdown("<div class='subtitle'>Membres de l'équipe</div>", unsafe_allow_html=True)
                st.markdown(f"**Chef d'équipe:** {team['leader']['name']} ({team['leader']['email']})")
                st.markdown(f"**GitHub:** [{team['leader']['github']}]({team['leader']['github']})")
                st.markdown(f"**Membre 1:** {team['member1']['name']} ({team['member1']['email']})")
                st.markdown(f"**GitHub:** [{team['member1']['github']}]({team['member1']['github']})")
                st.markdown(f"**Membre 2:** {team['member2']['name']} ({team['member2']['email']})")
                st.markdown(f"**GitHub:** [{team['member2']['github']}]({team['member2']['github']})")
                
                # Évaluation collective
                st.markdown("<div class='subtitle'>Évaluation Collective (Todo App)</div>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    # Générer des clés uniques pour les widgets
                    ui_key = f"ui_{team['teamName']}_{i}"  # Ajouter l'indice i pour garantir l'unicité
                    evaluations[team["teamName"]]["collective"]["uiDesign"] = st.number_input(
                        "Interface utilisateur (UI)",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["uiDesign"]),
                        key=ui_key
                    )
                    
                    api_key = f"api_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["apiImplementation"] = st.number_input(
                        "API RESTful",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["apiImplementation"]),
                        key=api_key
                    )
                    
                    db_key = f"db_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["database"] = st.number_input(
                        "Base de données",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["database"]),
                        key=db_key
                    )
                    
                    auth_key = f"auth_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["authentication"] = st.number_input(
                        "Authentification",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["authentication"]),
                        key=auth_key
                    )
                    
                    crud_key = f"crud_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["crudOperations"] = st.number_input(
                        "Opérations CRUD",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["crudOperations"]),
                        key=crud_key
                    )
                
                with col_b:
                    req_key = f"req_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["requiredFeatures"] = st.number_input(
                        "Fonctionnalités requises",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["requiredFeatures"]),
                        key=req_key
                    )
                    
                    bonus_key = f"bonus_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["bonusFeatures"] = st.number_input(
                        "Fonctionnalités bonus",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["bonusFeatures"]),
                        key=bonus_key
                    )
                    
                    doc_key = f"doc_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["documentation"] = st.number_input(
                        "Documentation",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["documentation"]),
                        key=doc_key
                    )
                    
                    collab_key = f"collab_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["teamCollaboration"] = st.number_input(
                        "Collaboration d'équipe",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["teamCollaboration"]),
                        key=collab_key
                    )
                    
                    deploy_key = f"deploy_{team['teamName']}_{i}"
                    evaluations[team["teamName"]]["collective"]["deployment"] = st.number_input(
                        "Déploiement",
                        min_value=0.0, max_value=20.0, step=1.0,
                        value=float(evaluations[team["teamName"]]["collective"]["deployment"]),
                        key=deploy_key
                    )
                
                # Mettre à jour le score collectif
                evaluate = calculate_final_score(evaluations, team["teamName"])
                collective_score = evaluate['collective']['totalScore']
                if pd.isna(collective_score):
                    collective_score = 0.0
                    
                st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #2A3942; padding: 10px; border-radius: 5px; margin-top: 10px;'><span style='font-weight: bold;'>Score collectif:</span><span class='score-badge'>{collective_score}/20</span></div>", unsafe_allow_html=True)
                
                # Évaluation individuelle
                st.markdown("<div class='subtitle'>Évaluation Individuelle</div>", unsafe_allow_html=True)
                
                # Chef d'équipe - affichage sans expander
                leader_name = team["leader"]["name"] if team["leader"]["name"] else "Chef d'équipe"
                st.markdown(f"<div style='background-color: #2A3942; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>{leader_name} (Chef d'équipe)</strong></div>", unsafe_allow_html=True)
                
                # Vérifier si la clé existe dans les évaluations
                if leader_name not in evaluations[team["teamName"]]["individual"]:
                    evaluations[team["teamName"]]["individual"][leader_name] = {
                        "webProgramming": 0.0,
                        "algorithmic": 0.0,
                        "totalScore": 0.0
                    }
                
                web_leader_key = f"web_{team['teamName']}_{leader_name}_{i}"
                evaluations[team["teamName"]]["individual"][leader_name]["webProgramming"] = st.number_input(
                    "Exercice de programmation web (PDF)",
                    min_value=0.0, max_value=20.0, step=1.0,
                    value=float(evaluations[team["teamName"]]["individual"][leader_name]["webProgramming"]),
                    key=web_leader_key
                )
                
                algo_leader_key = f"algo_{team['teamName']}_{leader_name}_{i}"
                evaluations[team["teamName"]]["individual"][leader_name]["algorithmic"] = st.number_input(
                    "Exercice d'algorithmique (Kattis)",
                    min_value=0.0, max_value=20.0, step=1.0,
                    value=float(evaluations[team["teamName"]]["individual"][leader_name]["algorithmic"]),
                    key=algo_leader_key
                )
                
                # Calculer le score individuel
                calculate_final_score(evaluations, team["teamName"])
                leader_score = evaluations[team['teamName']]['individual'][leader_name]['totalScore']
                if pd.isna(leader_score):
                    leader_score = 0.0
                st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #2A3942; padding: 10px; border-radius: 5px; margin-top: 10px; margin-bottom: 15px;'><span style='font-weight: bold;'>Score individuel:</span><span class='score-badge' style='background-color: #2A3942;'>{leader_score}/20</span></div>", unsafe_allow_html=True)
                
                # Membre 1 - affichage sans expander
                member1_name = team["member1"]["name"] if team["member1"]["name"] else "Membre 1"
                st.markdown(f"<div style='background-color: #2A3942; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>{member1_name}</strong></div>", unsafe_allow_html=True)
                
                # Vérifier si la clé existe dans les évaluations
                if member1_name not in evaluations[team["teamName"]]["individual"]:
                    evaluations[team["teamName"]]["individual"][member1_name] = {
                        "webProgramming": 0.0,
                        "algorithmic": 0.0,
                        "totalScore": 0.0
                    }
                
                web_member1_key = f"web_{team['teamName']}_{member1_name}_{i}"
                evaluations[team["teamName"]]["individual"][member1_name]["webProgramming"] = st.number_input(
                    "Exercice de programmation web (PDF)",
                    min_value=0.0, max_value=20.0, step=1.0,
                    value=float(evaluations[team["teamName"]]["individual"][member1_name]["webProgramming"]),
                    key=web_member1_key
                )
                
                algo_member1_key = f"algo_{team['teamName']}_{member1_name}_{i}"
                evaluations[team["teamName"]]["individual"][member1_name]["algorithmic"] = st.number_input(
                    "Exercice d'algorithmique (Kattis)",
                    min_value=0.0, max_value=20.0, step=1.0,
                    value=float(evaluations[team["teamName"]]["individual"][member1_name]["algorithmic"]),
                    key=algo_member1_key
                )
                
                # Calculer le score individuel
                calculate_final_score(evaluations, team["teamName"])
                member1_score = evaluations[team['teamName']]['individual'][member1_name]['totalScore']
                if pd.isna(member1_score):
                    member1_score = 0.0
                st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #2A3942; padding: 10px; border-radius: 5px; margin-top: 10px; margin-bottom: 15px;'><span style='font-weight: bold;'>Score individuel:</span><span class='score-badge' style='background-color: #2A3942;'>{member1_score}/20</span></div>", unsafe_allow_html=True)
                
                # Membre 2 - affichage sans expander
                member2_name = team["member2"]["name"] if team["member2"]["name"] else "Membre 2"
                st.markdown(f"<div style='background-color: #2A3933; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>{member2_name}</strong></div>", unsafe_allow_html=True)
                
                # Vérifier si la clé existe dans les évaluations
                if member2_name not in evaluations[team["teamName"]]["individual"]:
                    evaluations[team["teamName"]]["individual"][member2_name] = {
                        "webProgramming": 0.0,
                        "algorithmic": 0.0,
                        "totalScore": 0.0
                    }
                
                web_member2_key = f"web_{team['teamName']}_{member2_name}_{i}"
                evaluations[team["teamName"]]["individual"][member2_name]["webProgramming"] = st.number_input(
                    "Exercice de programmation web (PDF)",
                    min_value=0.0, max_value=20.0, step=1.0,
                    value=float(evaluations[team["teamName"]]["individual"][member2_name]["webProgramming"]),
                    key=web_member2_key
                )
                
                algo_member2_key = f"algo_{team['teamName']}_{member2_name}_{i}"
                evaluations[team["teamName"]]["individual"][member2_name]["algorithmic"] = st.number_input(
                    "Exercice d'algorithmique (Kattis)",
                    min_value=0.0, max_value=20.0, step=1.0,
                    value=float(evaluations[team["teamName"]]["individual"][member2_name]["algorithmic"]),
                    key=algo_member2_key
                )
                
                # Calculer le score individuel
                calculate_final_score(evaluations, team["teamName"])
                st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #2A3942; padding: 10px; border-radius: 5px; margin-top: 10px;'><span style='font-weight: bold;'>Score individuel:</span><span class='score-badge' style='background-color: #2A3942;'>{evaluations[team['teamName']]['individual'][member2_name]['totalScore']}/20</span></div>", unsafe_allow_html=True)
                
                # Score final de l'équipe
                st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #2A3654; padding: 15px; border-radius: 5px; margin-top: 20px;'><span style='font-weight: bold; font-size: 1.1rem;'>Score Final:</span><span class='score-badge' style='background-color: #28a745; font-size: 1.1rem;'>{evaluations[team['teamName']]['finalScore']}/20</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    # Créer un classement basé sur les scores finaux
    ranking_data = []
    for team in teams_data:
        team_name = team["teamName"]
        collective_score = evaluations[team_name]["collective"]["totalScore"]
        
        # S'assurer que les noms sont cohérents
        leader_name = team["leader"]["name"] if team["leader"]["name"] else "Chef d'équipe"
        member1_name = team["member1"]["name"] if team["member1"]["name"] else "Membre 1"
        member2_name = team["member2"]["name"] if team["member2"]["name"] else "Membre 2"
        
        # Vérifier si les clés existent
        if leader_name not in evaluations[team_name]["individual"]:
            evaluations[team_name]["individual"][leader_name] = {"totalScore": 0.0}
        if member1_name not in evaluations[team_name]["individual"]:
            evaluations[team_name]["individual"][member1_name] = {"totalScore": 0.0}
        if member2_name not in evaluations[team_name]["individual"]:
            evaluations[team_name]["individual"][member2_name] = {"totalScore": 0.0}
            
        # Calculer la moyenne des scores individuels
        individual_scores = [
            float(evaluations[team_name]["individual"][leader_name]["totalScore"]),
            float(evaluations[team_name]["individual"][member1_name]["totalScore"]),
            float(evaluations[team_name]["individual"][member2_name]["totalScore"])
        ]
        individual_avg = sum(individual_scores) / len(individual_scores)
        
        ranking_data.append({
            "Équipe": team_name,
            "Score Collectif": collective_score,
            "Score Individuel Moyen": individual_avg,
            "Score Final": evaluations[team_name]["finalScore"],
            "Détail Individuel": {
                leader_name: evaluations[team_name]["individual"][leader_name]["totalScore"],
                member1_name: evaluations[team_name]["individual"][member1_name]["totalScore"],
                member2_name: evaluations[team_name]["individual"][member2_name]["totalScore"]
            }
        })
    
    # Trier par score final décroissant
    ranking_data = sorted(ranking_data, key=lambda x: x["Score Final"], reverse=True)
    
    # Créer un DataFrame pour l'affichage
    ranking_df = pd.DataFrame([
        {
            "Rang": i+1,
            "Équipe": team["Équipe"],
            "Score Collectif": team["Score Collectif"],
            "Score Individuel Moyen": team["Score Individuel Moyen"],
            "Score Final": team["Score Final"]
        }
        for i, team in enumerate(ranking_data)
    ])
    
    # Afficher le tableau de classement
    st.markdown("<div class='subtitle'>Classement des équipes</div>", unsafe_allow_html=True)
    
    # Appliquer un style conditionnel pour mettre en évidence les 10 meilleures équipes
    def highlight_top_teams(val):
        color = 'rgba(40, 167, 69, 0.2)' if val <= 10 else ''
        return f'background-color: {color}'
    
    st.dataframe(
        ranking_df.style.applymap(highlight_top_teams, subset=['Rang']).format({
            "Score Collectif": "{:.2f}",
            "Score Individuel Moyen": "{:.2f}",
            "Score Final": "{:.2f}"
        }),
        use_container_width=True,
        height=400
    )
    
    # Visualisation graphique des scores
    st.markdown("<div class='subtitle'>Visualisation des scores</div>", unsafe_allow_html=True)
    
    col_viz1, col_viz2 = st.columns(2)
    
    with col_viz1:
        # Graphique des scores finaux par équipe
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Limiter aux 15 premières équipes pour la lisibilité
        plot_data = ranking_df.head(15).copy()
        bars = ax.barh(plot_data["Équipe"], plot_data["Score Final"], color='forestgreen')
        
        # Ajouter les valeurs sur les barres
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{width:.2f}', ha='left', va='center')
        
        ax.set_xlabel('Score Final (/20)')
        ax.set_title('Top 15 des équipes par score final')
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        st.pyplot(fig)
    
    with col_viz2:
        # Graphique comparatif des scores collectifs vs individuels
        fig, ax = plt.subplots(figsize=(10, 8))
        
        plot_data = ranking_df.head(15).copy()
        x = np.arange(len(plot_data["Équipe"]))
        width = 0.35
        
        bar1 = ax.bar(x - width/2, plot_data["Score Collectif"], width, label='Score Collectif', color='royalblue')
        bar2 = ax.bar(x + width/2, plot_data["Score Individuel Moyen"], width, label='Score Individuel Moyen', color='darkorange')
        
        ax.set_xticks(x)
        ax.set_xticklabels(plot_data["Équipe"], rotation=45, ha='right')
        ax.legend()
        ax.set_ylabel('Score (/20)')
        ax.set_title('Comparaison des scores collectifs et individuels')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        st.pyplot(fig)
    
    # Export des données
    st.markdown("<div class='subtitle'>Exporter les données</div>", unsafe_allow_html=True)
    
    # Fonction pour créer un fichier CSV téléchargeable
    def get_csv_download_link(df):
        csv = df.to_csv(index=False)
        b64 = BytesIO()
        df.to_csv(b64, index=False)
        b64.seek(0)
        return b64.getvalue()
    
    # Création d'un dataframe détaillé contenant les scores individuels
    detailed_data = []
    for i, team in enumerate(ranking_data):
        # Créer une liste des noms et scores pour rester robuste face aux changements
        individual_names = list(team['Détail Individuel'].keys())
        individual_values = list(team['Détail Individuel'].values())
        
        # Utiliser une approche sécurisée pour accéder aux données
        member0_name = individual_names[0] if len(individual_names) > 0 else "Membre"
        member0_score = individual_values[0] if len(individual_values) > 0 else 0
        
        member1_name = individual_names[1] if len(individual_names) > 1 else "Membre"
        member1_score = individual_values[1] if len(individual_values) > 1 else 0
        
        member2_name = individual_names[2] if len(individual_names) > 2 else "Membre"
        member2_score = individual_values[2] if len(individual_values) > 2 else 0
        
        row_data = {
            "Rang": i+1,
            "Équipe": team["Équipe"],
            "Score Collectif": team["Score Collectif"],
            f"{member0_name} (Score)": member0_score,
            f"{member1_name} (Score)": member1_score,
            f"{member2_name} (Score)": member2_score,
            "Score Individuel Moyen": team["Score Individuel Moyen"],
            "Score Final": team["Score Final"]
        }
        detailed_data.append(row_data)
    
    detailed_df = pd.DataFrame(detailed_data)
    export_data = get_csv_download_link(detailed_df)
    st.download_button(
        label="Télécharger le classement complet (CSV)",
        data=export_data,
        file_name="classement_hackathon.csv",
        mime="text/csv"
    )

    # Gestion des évaluations (Sauvegarde/Chargement)
    st.markdown("<div class='subtitle'>Gestion des données d'évaluation</div>", unsafe_allow_html=True)

    save_col1, save_col2 = st.columns(2)

    with save_col1:
        if st.button("💾 Sauvegarder toutes les évaluations", key="save_button"):
            try:
                filename, backup_filename = save_evaluations_to_csv(st.session_state.evaluations)
                st.success(f"Évaluations sauvegardées dans {filename} et {backup_filename} !")
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde: {e}")

    with save_col2:
        if st.button("📂 Charger les évaluations sauvegardées", key="load_button"):
            try:
                # Ne pas utiliser silent ici car l'utilisateur a explicitement demandé le chargement
                loaded_evaluations = load_evaluations_from_csv(silent=False)
                if loaded_evaluations:
                    st.session_state.evaluations = loaded_evaluations
                    st.success("Évaluations chargées avec succès !")
                    st.rerun()  # Recharger la page pour mettre à jour les widgets
            except Exception as e:
                st.error(f"Erreur lors du chargement: {e}")

    st.info("Les évaluations sont sauvegardées dans un fichier CSV qui peut être ouvert avec Excel ou tout autre tableur. Une copie de sauvegarde datée est également créée à chaque sauvegarde.")

    # Messages d'information
    st.info("Les 10 équipes avec le meilleur score final seront qualifiées pour le hackathon HACKVERSE 2025.")
    
    # Explication de la formule de calcul
    with st.expander("Comment le score final est-il calculé ?"):
        st.markdown("""
        La note finale de l'équipe est calculée selon la formule suivante :
        
        ```
        Note équipe = (Note sur l'exercice collectif / 2) + (Somme des notes individuelles / 3) / 2
        ```
        
        **Exemple de calcul :**
        - Note sur l'exercice collectif : 16/20
        - Notes individuelles : 14/20, 18/20, 16/20
        
        ```
        Note équipe = 16/2 + (14+18+16)/3/2 = 8 + 48/3/2 = 8 + 16/2 = 8 + 8 = 16/20
        ```
        """)

# Sauvegarder les évaluations dans la session
st.session_state.evaluations = evaluations