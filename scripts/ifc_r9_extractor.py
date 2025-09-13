#!/usr/bin/env python3
"""
Système d'extraction IFC pour le projet R9 - Blockchain BIM
Extraction des objets IFC avec validation complète des 11 paramètres obligatoires
Compatible avec Brownie Framework + Ganache + Pinata + IFCOpenShell
Auteur: Leopold Malkit Singh
"""

import ifcopenshell
import ifcopenshell.util.element
import json
import hashlib
import os
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
import random
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Exception personnalisée pour les erreurs de validation"""
    pass

class ExtracteurIFC_R9:
    """
    Extracteur IFC spécialement conçu pour le projet R9
    Validation stricte des 11 paramètres obligatoires + paramètres maquette
    """
    
    def __init__(self):
        self.model_ifc = None
        self.chemin_fichier = None
        self.objets_extraits = []
        self.metadonnees_maquette = {}
        self.start_time = None
        self.existing_ids = set()  # Pour vérifier les doublons
        
        # Liste exacte des 11 paramètres obligatoires
        self.parametres_obligatoires = [
            "NOM",
            "ID", 
            "ID_maquette",
            "Longueur_m",
            "Caracteristique_Materiau",
            "Materiau",
            "Statut_usage",
            "Date_fabrication",
            "Date_mise_en_service", 
            "Date_reemploi",
            "Empreinte_Carbone"
        ]
        
        # Paramètres maquette obligatoires
        self.parametres_maquette_obligatoires = [
            "nom_maquette",
            "ID_maquette", 
            "nom_architecte",
            "coordonnees_geographiques",
            "programme",
            "date_livraison",
            "date_depot"
        ]

    def charger_fichier_ifc(self, chemin_fichier: str) -> bool:
        """Charge le fichier IFC et initialise le timer"""
        try:
            self.start_time = time.time()
            self.chemin_fichier = Path(chemin_fichier)
            
            if not self.chemin_fichier.exists():
                raise FileNotFoundError(f"Fichier IFC non trouvé: {chemin_fichier}")
            
            logger.info(f"Chargement du fichier IFC: {chemin_fichier}")
            self.model_ifc = ifcopenshell.open(str(chemin_fichier))
            logger.info(f"Fichier IFC chargé avec succès. Version: {self.model_ifc.schema}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier IFC: {e}")
            return False

    def simuler_verification_ids_reseau(self, ids_a_verifier: List[str]) -> List[str]:
        """
        Simule la vérification des IDs déjà présents sur le réseau blockchain
        Dans la vraie implémentation, cela interrogerait le smart contract
        """
        # Simulation: on génère quelques IDs "existants" pour tester
        ids_existants_simules = [
            "1234567891234567",  # ID déjà présent
            "9876543210987654",  # Autre ID existant
        ]
        
        doublons_detectes = []
        for id_obj in ids_a_verifier:
            if id_obj in ids_existants_simules:
                doublons_detectes.append(id_obj)
        
        return doublons_detectes

    def valider_format_date(self, date_str: str) -> bool:
        """Valide le format de date DD-MM-YYYY"""
        if not date_str or date_str in ["Non trouvé", "Non spécifié", ""]:
            return False
        
        pattern = r'^\d{2}-\d{2}-\d{4}$'
        if not re.match(pattern, date_str):
            return False
        
        try:
            datetime.strptime(date_str, '%d-%m-%Y')
            return True
        except ValueError:
            return False

    def valider_format_parametre(self, nom_param: str, valeur: Any) -> Tuple[bool, str]:
        """
        Valide le format de chaque paramètre selon les spécifications R9
        
        Returns:
            Tuple[bool, str]: (est_valide, message_erreur)
        """
        if valeur is None or valeur == "" or valeur == "Non trouvé":
            return False, f"Paramètre {nom_param} est vide ou non trouvé"
        
        valeur_str = str(valeur).strip()
        
        if nom_param == "NOM":
            if not isinstance(valeur_str, str) or len(valeur_str) < 1:
                return False, "NOM doit être une chaîne de caractères non vide"
                
        elif nom_param == "ID":
            if not valeur_str.isdigit() or len(valeur_str) != 16:
                return False, "ID doit être un entier de 16 chiffres exactement"
                
        elif nom_param == "ID_maquette":
            if not valeur_str.isdigit() or len(valeur_str) != 12:
                return False, "ID_maquette doit être un entier de 12 chiffres exactement"
                
        elif nom_param == "Longueur_m":
            try:
                float(valeur_str)
            except ValueError:
                return False, "Longueur_m doit être un nombre décimal (ex: 12.23)"
                
        elif nom_param == "Statut_usage":
            statuts_valides = ["neuf", "en usage", "réemployé"]
            if valeur_str.lower() not in statuts_valides:
                return False, f"Statut_usage doit être l'un de: {statuts_valides}"
                
        elif nom_param in ["Date_fabrication", "Date_mise_en_service", "Date_reemploi"]:
            if not self.valider_format_date(valeur_str):
                return False, f"{nom_param} doit être au format DD-MM-YYYY (ex: 13-01-2001)"
                
        elif nom_param == "Empreinte_Carbone":
            try:
                float(valeur_str)
            except ValueError:
                return False, "Empreinte_Carbone doit être un nombre (kg CO2 équivalent)"
        
        return True, ""

    def extraire_proprietes_objet(self, element) -> Dict[str, Any]:
        """Extrait les propriétés d'un élément IFC selon les 11 paramètres R9"""
        
        proprietes = {}
        
        # 1. NOM - depuis Name ou type IFC
        proprietes["NOM"] = element.Name if element.Name else f"{element.is_a()}_{element.id()}"
        
        # 2. ID - génération d'un ID 16 chiffres depuis GlobalId
        global_id = element.GlobalId if hasattr(element, 'GlobalId') else str(element.id())
        # Conversion en ID numérique 16 chiffres
        id_hash = hashlib.md5(global_id.encode()).hexdigest()
        proprietes["ID"] = str(int(id_hash[:15], 16))[:16].zfill(16)
        
        # 3. ID_maquette - sera défini lors de la saisie des métadonnées maquette
        proprietes["ID_maquette"] = "000000000000"  # Placeholder
        
        # 4. Longueur_m - recherche dans les propriétés ou calcul approximatif
        longueur = "0.0"
        if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
            for relation in element.IsDefinedBy:
                if relation.is_a('IfcRelDefinesByProperties'):
                    prop_set = relation.RelatingPropertyDefinition
                    if prop_set.is_a('IfcPropertySet'):
                        for prop in prop_set.HasProperties:
                            if prop.is_a('IfcPropertySingleValue') and prop.Name:
                                nom = prop.Name.lower()
                                if any(dim in nom for dim in ['length', 'longueur', 'height', 'hauteur']):
                                    if prop.NominalValue and hasattr(prop.NominalValue, 'wrappedValue'):
                                        longueur = str(float(prop.NominalValue.wrappedValue))
                                        break
        proprietes["Longueur_m"] = longueur
        
        # 5. Caracteristique_Materiau - depuis les propriétés matériau
        caracteristique = "Non spécifié"
        if hasattr(element, 'HasAssociations') and element.HasAssociations:
            for association in element.HasAssociations:
                if association.is_a('IfcRelAssociatesMaterial'):
                    materiau = association.RelatingMaterial
                    if materiau.is_a('IfcMaterial'):
                        # Recherche de propriétés comme Grade, Strength, etc.
                        if hasattr(materiau, 'HasProperties') and materiau.HasProperties:
                            for prop_rel in materiau.HasProperties:
                                if prop_rel.is_a('IfcMaterialProperties'):
                                    for prop in prop_rel.Properties:
                                        if prop.Name in ['Grade', 'Strength', 'Class']:
                                            caracteristique = str(prop.NominalValue.wrappedValue) if prop.NominalValue else "S235"
        proprietes["Caracteristique_Materiau"] = caracteristique
        
        # 6. Materiau - type de matériau principal
        materiau_type = "Non spécifié"
        type_ifc = element.is_a()
        mapping_materiaux = {
            'IfcBeam': 'acier',
            'IfcColumn': 'acier', 
            'IfcSlab': 'béton',
            'IfcWall': 'béton',
            'IfcWindow': 'verre',
            'IfcDoor': 'bois'
        }
        materiau_type = mapping_materiaux.get(type_ifc, 'mixte')
        proprietes["Materiau"] = materiau_type
        
        # 7. Statut_usage - par défaut "neuf" pour nouveaux objets
        proprietes["Statut_usage"] = "neuf"
        
        # 8. Date_fabrication - date par défaut ou depuis propriétés
        proprietes["Date_fabrication"] = "01-01-2020"
        
        # 9. Date_mise_en_service - date par défaut
        proprietes["Date_mise_en_service"] = "01-06-2020"
        
        # 10. Date_reemploi - vide car objet neuf
        proprietes["Date_reemploi"] = "Non spécifié"
        
        # 11. Empreinte_Carbone - calcul approximatif ou valeur par défaut
        empreinte = 100.0  # kg CO2 par défaut
        # TODO: Calcul plus précis basé sur le volume et le matériau
        proprietes["Empreinte_Carbone"] = str(empreinte)
        
        return proprietes

    def demander_metadonnees_maquette(self) -> Dict[str, Any]:
        """Demande à l'utilisateur de saisir les métadonnées de la maquette"""
        
        print("\n" + "="*60)
        print("SAISIE DES MÉTADONNÉES DE LA MAQUETTE")
        print("="*60)
        
        metadonnees = {}
        
        # Génération automatique de l'ID_maquette (12 chiffres)
        id_maquette = str(random.randint(100000000000, 999999999999))
        
        try:
            # Saisie des paramètres requis
            metadonnees["nom_maquette"] = input("Nom de la maquette (ex: Diogène): ").strip()
            metadonnees["ID_maquette"] = id_maquette
            metadonnees["nom_architecte"] = input("Nom de l'architecte (ex: Renzo Piano): ").strip()
            
            # Coordonnées géographiques
            print("\nCoordonnées géographiques:")
            latitude = input("  Latitude (ex: 48.8566): ").strip()
            longitude = input("  Longitude (ex: 2.3522): ").strip()
            metadonnees["coordonnees_geographiques"] = f"{latitude}, {longitude}"
            
            metadonnees["programme"] = input("Programme (ex: logement): ").strip()
            metadonnees["date_livraison"] = input("Date de livraison (DD-MM-YYYY, ex: 13-01-2024): ").strip()
            
            # Date de dépôt automatique
            metadonnees["date_depot"] = datetime.now().strftime("%d-%m-%Y")
            
            print(f"\n✅ ID_maquette généré automatiquement: {id_maquette}")
            print(f"✅ Date de dépôt: {metadonnees['date_depot']}")
            
            return metadonnees
            
        except KeyboardInterrupt:
            print("\n❌ Saisie interrompue par l'utilisateur")
            raise ValidationError("Saisie des métadonnées interrompue")

    def valider_metadonnees_maquette(self, metadonnees: Dict[str, Any]) -> List[str]:
        """Valide les métadonnées de la maquette"""
        erreurs = []
        
        # Vérification que tous les paramètres sont présents
        for param in self.parametres_maquette_obligatoires:
            if param not in metadonnees:
                erreurs.append(f"Paramètre maquette manquant: {param}")
                continue
                
            valeur = metadonnees[param]
            if not valeur or str(valeur).strip() == "":
                erreurs.append(f"Paramètre maquette vide: {param}")
                continue
        
        # Validation des formats spécifiques
        if "date_livraison" in metadonnees:
            if not self.valider_format_date(metadonnees["date_livraison"]):
                erreurs.append("date_livraison doit être au format DD-MM-YYYY")
        
        # Validation coordonnées géographiques
        if "coordonnees_geographiques" in metadonnees:
            coords = metadonnees["coordonnees_geographiques"]
            if "," not in coords:
                erreurs.append("coordonnees_geographiques doivent être au format 'latitude, longitude'")
        
        return erreurs

    def extraire_objets_avec_validation(self) -> List[Dict[str, Any]]:
        """Extrait tous les objets IFC avec validation complète"""
        
        if not self.model_ifc:
            raise ValidationError("Fichier IFC non chargé")
        
        # Types d'éléments BIM à extraire
        types_elements = [
            'IfcWall', 'IfcSlab', 'IfcBeam', 'IfcColumn', 'IfcWindow', 
            'IfcDoor', 'IfcRoof', 'IfcStair', 'IfcRailing', 'IfcPlate', 
            'IfcMember', 'IfcBuildingElementProxy'
        ]
        
        objets_valides = []
        erreurs_validation = []
        ids_extraits = []
        
        logger.info("Début de l'extraction et validation des objets BIM...")
        
        for type_element in types_elements:
            elements = self.model_ifc.by_type(type_element)
            
            for element in elements:
                try:
                    # Extraction des propriétés
                    proprietes = self.extraire_proprietes_objet(element)
                    
                    # Mise à jour de l'ID_maquette avec la valeur correcte
                    proprietes["ID_maquette"] = self.metadonnees_maquette["ID_maquette"]
                    
                    # Validation de chaque paramètre
                    erreurs_objet = []
                    for param in self.parametres_obligatoires:
                        if param not in proprietes:
                            erreurs_objet.append(f"Paramètre manquant: {param}")
                            continue
                        
                        valide, message = self.valider_format_parametre(param, proprietes[param])
                        if not valide:
                            erreurs_objet.append(f"Objet {element.id()}: {message}")
                    
                    # Vérification des doublons d'ID
                    id_objet = proprietes["ID"]
                    if id_objet in ids_extraits:
                        erreurs_objet.append(f"ID dupliqué détecté: {id_objet}")
                    
                    ids_extraits.append(id_objet)
                    
                    if erreurs_objet:
                        erreurs_validation.extend(erreurs_objet)
                    else:
                        # Ajout des métadonnées techniques
                        proprietes["_metadata"] = {
                            "global_id": element.GlobalId if hasattr(element, 'GlobalId') else str(element.id()),
                            "ifc_type": element.is_a(),
                            "geometrie_disponible": hasattr(element, 'Representation') and element.Representation is not None
                        }
                        objets_valides.append(proprietes)
                
                except Exception as e:
                    erreurs_validation.append(f"Erreur lors du traitement de l'objet {element.id()}: {e}")
        
        # Vérification des IDs sur le réseau (simulation)
        if ids_extraits:
            doublons_reseau = self.simuler_verification_ids_reseau(ids_extraits)
            if doublons_reseau:
                for id_doublon in doublons_reseau:
                    erreurs_validation.append(f"ID déjà présent sur le réseau: {id_doublon}")
        
        if erreurs_validation:
            logger.error(f"Erreurs de validation détectées: {len(erreurs_validation)}")
            for erreur in erreurs_validation:
                logger.error(f"  - {erreur}")
            raise ValidationError(f"Validation échouée: {len(erreurs_validation)} erreurs détectées")
        
        self.objets_extraits = objets_valides
        logger.info(f"✅ Extraction réussie: {len(objets_valides)} objets validés")
        return objets_valides

    def extraire_objet_ifc_individuel(self, element, dossier_sortie: Path) -> str:
        """Extrait un objet IFC individuel avec sa géométrie dans un fichier séparé"""
        
        try:
            # Création d'un nouveau modèle IFC pour l'objet individuel
            nouveau_modele = ifcopenshell.file(schema=self.model_ifc.schema)
            
            # Copie des entités de base nécessaires
            project = self.model_ifc.by_type('IfcProject')[0]
            nouveau_modele.add(project)
            
            if self.model_ifc.by_type('IfcSite'):
                site = self.model_ifc.by_type('IfcSite')[0]
                nouveau_modele.add(site)
            
            if self.model_ifc.by_type('IfcBuilding'):
                building = self.model_ifc.by_type('IfcBuilding')[0]
                nouveau_modele.add(building)
            
            # Ajout de l'élément et de ses dépendances
            nouveau_modele.add(element)
            
            # Copie de la géométrie et des matériaux
            if hasattr(element, 'Representation') and element.Representation:
                nouveau_modele.add(element.Representation)
            
            if hasattr(element, 'HasAssociations') and element.HasAssociations:
                for association in element.HasAssociations:
                    nouveau_modele.add(association)
            
            # Génération du nom de fichier
            global_id = element.GlobalId if hasattr(element, 'GlobalId') else str(element.id())
            nom_fichier = f"objet_{global_id}.ifc"
            chemin_complet = dossier_sortie / nom_fichier
            
            # Sauvegarde du fichier IFC
            nouveau_modele.write(str(chemin_complet))
            
            return str(chemin_complet)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'objet IFC {element.id()}: {e}")
            raise

    def generer_fichiers_sortie(self, dossier_sortie: str) -> Dict[str, Any]:
        """Génère tous les fichiers de sortie pour IPFS"""
        
        dossier = Path(dossier_sortie)
        dossier.mkdir(parents=True, exist_ok=True)
        
        # Dossiers spécifiques
        dossier_objets_ifc = dossier / "objets_ifc"
        dossier_objets_json = dossier / "objets_json"
        dossier_objets_ifc.mkdir(exist_ok=True)
        dossier_objets_json.mkdir(exist_ok=True)
        
        fichiers_generes = {
            "objets_ifc": [],
            "objets_json": [],
            "maquette_ifc": "",
            "maquette_json": ""
        }
        
        logger.info("Génération des fichiers de sortie...")
        
        # 1. Génération des objets IFC individuels et leurs JSON
        types_elements = [
            'IfcWall', 'IfcSlab', 'IfcBeam', 'IfcColumn', 'IfcWindow', 
            'IfcDoor', 'IfcRoof', 'IfcStair', 'IfcRailing', 'IfcPlate', 
            'IfcMember', 'IfcBuildingElementProxy'
        ]
        
        for type_element in types_elements:
            elements = self.model_ifc.by_type(type_element)
            
            for i, element in enumerate(elements):
                if i < len(self.objets_extraits):
                    try:
                        # Fichier IFC individuel
                        chemin_ifc = self.extraire_objet_ifc_individuel(element, dossier_objets_ifc)
                        fichiers_generes["objets_ifc"].append(chemin_ifc)
                        
                        # Fichier JSON correspondant
                        global_id = element.GlobalId if hasattr(element, 'GlobalId') else str(element.id())
                        nom_json = f"objet_{global_id}.json"
                        chemin_json = dossier_objets_json / nom_json
                        
                        with open(chemin_json, 'w', encoding='utf-8') as f:
                            json.dump(self.objets_extraits[i], f, indent=2, ensure_ascii=False)
                        
                        fichiers_generes["objets_json"].append(str(chemin_json))
                        
                    except Exception as e:
                        logger.error(f"Erreur génération fichier objet {element.id()}: {e}")
        
        # 2. Copie de la maquette IFC complète
        nom_maquette = self.metadonnees_maquette["nom_maquette"].replace(" ", "_")
        chemin_maquette_ifc = dossier / f"maquette_{nom_maquette}.ifc"
        
        import shutil
        shutil.copy2(self.chemin_fichier, chemin_maquette_ifc)
        fichiers_generes["maquette_ifc"] = str(chemin_maquette_ifc)
        
        # 3. JSON de la maquette
        chemin_maquette_json = dossier / f"maquette_{nom_maquette}.json"
        with open(chemin_maquette_json, 'w', encoding='utf-8') as f:
            json.dump(self.metadonnees_maquette, f, indent=2, ensure_ascii=False)
        
        fichiers_generes["maquette_json"] = str(chemin_maquette_json)
        
        return fichiers_generes

    def traitement_complet(self, chemin_fichier_ifc: str, dossier_sortie: str) -> Dict[str, Any]:
        """Lance le traitement complet avec validation stricte"""
        
        try:
            print("\n" + "="*60)
            print("DÉBUT DU TRAITEMENT IFC R9")
            print("="*60)
            
            # 1. Chargement du fichier IFC
            if not self.charger_fichier_ifc(chemin_fichier_ifc):
                raise ValidationError("Impossible de charger le fichier IFC")
            
            # 2. Saisie des métadonnées maquette
            self.metadonnees_maquette = self.demander_metadonnees_maquette()
            
            # 3. Validation des métadonnées maquette
            erreurs_maquette = self.valider_metadonnees_maquette(self.metadonnees_maquette)
            if erreurs_maquette:
                print("\n❌ ERREURS MÉTADONNÉES MAQUETTE:")
                for erreur in erreurs_maquette:
                    print(f"  - {erreur}")
                raise ValidationError("Métadonnées maquette incorrectes")
            
            # 4. Extraction et validation des objets
            objets = self.extraire_objets_avec_validation()
            
            # 5. Génération des fichiers
            fichiers = self.generer_fichiers_sortie(dossier_sortie)
            
            # 6. Calcul du temps de traitement
            temps_total = time.time() - self.start_time
            
            # 7. Résumé de succès
            print("\n" + "="*60)
            print("✅ TRAITEMENT RÉUSSI")
            print("="*60)
            print(f"✅ Temps de traitement total: {temps_total:.2f} secondes")
            print(f"✅ Objets traités: {len(objets)}")
            print(f"✅ Fichiers IFC objets générés: {len(fichiers['objets_ifc'])}")
            print(f"✅ Fichiers JSON objets générés: {len(fichiers['objets_json'])}")
            print(f"✅ Maquette IFC: {fichiers['maquette_ifc']}")
            print(f"✅ Maquette JSON: {fichiers['maquette_json']}")
            print("\n🚀 FICHIERS PRÊTS POUR IPFS/PINATA!")
            
            return {
                'statut': 'succès',
                'temps_traitement_secondes': round(temps_total, 2),
                'nombre_objets': len(objets),
                'fichiers_generes': fichiers,
                'metadonnees_maquette': self.metadonnees_maquette,
                'dossier_sortie': dossier_sortie
            }
            
        except ValidationError as e:
            print(f"\n❌ ERREUR DE VALIDATION: {e}")
            return {'statut': 'erreur', 'message': str(e)}
            
        except Exception as e:
            print(f"\n❌ ERREUR TECHNIQUE: {e}")
            logger.error(f"Erreur lors du traitement: {e}")
            return {'statut': 'erreur', 'message': str(e)}


def main():
    """Fonction principale adaptée au projet Brownie"""
    
    print("="*60)
    print("EXTRACTEUR IFC R9 - BLOCKCHAIN BIM")
    print("="*60)
    
    # Chemin vers le dossier IFC du projet
    chemin_ifc = input("Nom du fichier IFC (dans data/ifc-files/): ").strip()
    
    # Construction du chemin complet
    chemin_complet = f"data/ifc-files/{chemin_ifc}"
    
    if not Path(chemin_complet).exists():
        print(f"❌ Fichier non trouvé: {chemin_complet}")
        return
    
    # Dossier de sortie dans data/processed/
    nom_base = Path(chemin_ifc).stem
    dossier_sortie = f"data/processed/extraction_r9_{nom_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Lancement de l'extraction
    extracteur = ExtracteurIFC_R9()
    resultat = extracteur.traitement_complet(chemin_complet, dossier_sortie)
    
    if resultat['statut'] == 'succès':
        print(f"\n📁 Résultats dans: {dossier_sortie}")
        print("🚀 Fichiers prêts pour intégration Brownie!")
    else:
        print(f"\n❌ Échec: {resultat['message']}")


if __name__ == "__main__":
    main()