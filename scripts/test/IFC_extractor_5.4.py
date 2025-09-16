#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R9 IFC EXTRACTOR - VERSION FINALE COMPLÈTE
==========================================
Extracteur IFC pour Brownie/Ethereum avec extraction correcte des métadonnées
Traitement automatique de tous les fichiers dans ifc-files/
Auteur: Leopold Malkit Singh
version 5.4 - 2025-09-16
Corrections: Validation stricte des propriétés et formats + Hash SHA-256
"""

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.attribute
import json
import os
import hashlib
import shutil
import re
import time  # Ajouter avec les autres imports
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

class ExtracteurIFC_R9_Brownie:
    """
    Extracteur IFC Final pour Brownie/Ethereum
    Extraction complète des métadonnées depuis les fichiers IFC
    """
    
    def __init__(self):
        self.model_ifc = None
        self.chemin_fichier = None
        self.objets_extraits = []
        self.metadonnees_maquette = {}
        self.start_time = None
        self.temps_traitement = 0.0
        
        # Structure des dossiers
        self.base_dir = Path('data')
        self.ifc_files_dir = self.base_dir / 'ifc-files'
        self.processed_dir = self.base_dir / 'processed'
        
        # Créer la structure de sortie
        self.create_output_structure()
        
        # Paramètres R9 obligatoires avec leurs types et formats
        self.parametres_obligatoires = {
            "NOM": {"type": str, "format": "lettres", "description": "Nom de l'objet (lettres uniquement)"},
            "ID": {"type": str, "format": "16_chiffres", "description": "ID à 16 chiffres"},
            "ID_maquette": {"type": str, "format": "12_chiffres", "description": "ID maquette à 12 chiffres"},
            "Longueur_m": {"type": float, "format": "nombre", "description": "Longueur en mètres"},
            "Caracteristique_Materiau": {"type": str, "format": "texte", "description": "Caractéristique du matériau"},
            "Materiau": {"type": str, "format": "texte", "description": "Type de matériau"},
            "Statut usage": {"type": str, "format": "texte", "description": "Statut d'usage (neuf/en usage/réemployé)"},
            "Date de fabrication": {"type": str, "format": "date", "description": "Date de fabrication (JJ MM AAAA)"},
            "date mise en service": {"type": str, "format": "date", "description": "date mise en service (JJ MM AAAA)"},
            "Date de réemploye": {"type": str, "format": "date", "description": "Date de réemploi (JJ MM AAAA)"},
            "Empreinte Carbonne": {"type": float, "format": "nombre", "description": "Empreinte carbone"}
        }

    def create_output_structure(self):
        """Crée la structure complète des dossiers de sortie"""
        # Dossiers principaux dans processed/
        self.objets_ifc_dir = self.processed_dir / 'objets_ifc'
        self.objets_json_dir = self.processed_dir / 'objets_json'
        self.maquettes_dir = self.processed_dir / 'maquettes'
        
        # Créer tous les dossiers
        for directory in [self.objets_ifc_dir, self.objets_json_dir, self.maquettes_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def calculer_hash_json(self, proprietes: Dict) -> str:
        """
        Calcule le hash SHA-256 d'un dictionnaire JSON
        """
        json_string = json.dumps(proprietes, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_string.encode('utf-8')).hexdigest()

    def calculer_hash_fichier(self, fichier_path: Path) -> str:
        """
        Calcule le hash SHA-256 d'un fichier
        """
        with open(fichier_path, 'rb') as f:
            contenu = f.read()
        return hashlib.sha256(contenu).hexdigest()

    def valider_format(self, valeur: Any, format_attendu: str, nom_propriete: str) -> Tuple[bool, str]:
        """
        Valide le format d'une valeur selon le format attendu
        Retourne (True, valeur_formatée) si valide, (False, message_erreur) sinon
        """
        if valeur is None:
            return False, f"La propriété '{nom_propriete}' est manquante ou nulle"
        
        valeur_str = str(valeur)
        
        if format_attendu == "16_chiffres":
            if not valeur_str.isdigit():
                return False, f"'{nom_propriete}' doit contenir uniquement des chiffres, reçu: '{valeur_str}'"
            if len(valeur_str) != 16:
                return False, f"'{nom_propriete}' doit contenir exactement 16 chiffres, reçu: {len(valeur_str)} chiffres"
            return True, valeur_str
        
        elif format_attendu == "12_chiffres":
            if not valeur_str.isdigit():
                return False, f"'{nom_propriete}' doit contenir uniquement des chiffres, reçu: '{valeur_str}'"
            if len(valeur_str) != 12:
                return False, f"'{nom_propriete}' doit contenir exactement 12 chiffres, reçu: {len(valeur_str)} chiffres"
            return True, valeur_str
        
        elif format_attendu == "lettres":
            # Garder seulement les lettres et espaces
            nom_clean = re.sub(r'[^a-zA-Z\s]', '', valeur_str)
            if not nom_clean:
                return False, f"'{nom_propriete}' doit contenir des lettres, reçu: '{valeur_str}'"
            return True, nom_clean.strip()
        
        elif format_attendu == "nombre":
            try:
                return True, float(valeur_str)
            except ValueError:
                return False, f"'{nom_propriete}' doit être un nombre, reçu: '{valeur_str}'"
        
        elif format_attendu == "date":
            # Vérifier le format JJ MM AAAA
            date_clean = valeur_str.replace('-', ' ').replace('/', ' ')
            parts = date_clean.split()
            
            if len(parts) != 3:
                return False, f"'{nom_propriete}' doit être au format JJ MM AAAA, reçu: '{valeur_str}'"
            
            try:
                jour, mois, annee = parts
                date_obj = datetime(int(annee), int(mois), int(jour))
                return True, f"{jour} {mois} {annee}"
            except:
                return False, f"'{nom_propriete}' date invalide, reçu: '{valeur_str}'"
        
        elif format_attendu == "texte":
            if not valeur_str or valeur_str.strip() == "":
                return False, f"'{nom_propriete}' ne peut pas être vide"
            return True, valeur_str
        
        return True, valeur_str

    def extraire_propriete_specifique(self, element, nom_propriete: str) -> Optional[Any]:
        """
        Extrait une propriété spécifique d'un élément IFC
        Retourne None si non trouvée
        """
        try:
            # Chercher dans les PropertySets
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_set = definition.RelatingPropertyDefinition
                    
                    if property_set.is_a('IfcPropertySet'):
                        for prop in property_set.HasProperties:
                            if prop.is_a('IfcPropertySingleValue'):
                                # Vérifier le nom exact (sans accent pour Date réemploye)
                                if prop.Name == nom_propriete and prop.NominalValue:
                                    return prop.NominalValue.wrappedValue
            return None
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction de '{nom_propriete}': {e}")
            return None

    def extraire_toutes_proprietes_element(self, element) -> Tuple[Dict[str, Any], List[str]]:
        """
        Extrait TOUTES les propriétés d'un élément IFC selon le format R9
        Retourne (proprietes_dict, liste_erreurs)
        """
        proprietes = {}
        erreurs = []
        
        try:
            # Parcourir chaque propriété obligatoire
            for nom_prop, config in self.parametres_obligatoires.items():
                
                # Nom de la propriété dans le fichier IFC (sans underscore pour les dates)
                nom_ifc = nom_prop
                if nom_prop == "Date de fabrication":
                    nom_ifc = "Date de fabrication"
                elif nom_prop == "date mise en service":
                    nom_ifc = "date mise en service"
                elif nom_prop == "Date de réemploye":
                    nom_ifc = "Date de réemploye"  # Sans accent !
                elif nom_prop == "ID_maquette":
                    nom_ifc = "ID_maquette"
                elif nom_prop == "Longueur_m":
                    nom_ifc = "Longueur_m"
                elif nom_prop == "Caracteristique_Materiau":
                    nom_ifc = "Caracteristique_Materiau"
                elif nom_prop == "Statut usage":
                    nom_ifc = "Statut usage"
                elif nom_prop == "Empreinte Carbonne":
                    nom_ifc = "Empreinte Carbonne"
                
                # Extraire la valeur
                valeur = self.extraire_propriete_specifique(element, nom_ifc)
                
                # Si pas trouvé, chercher aussi avec des variantes
                if valeur is None and "Date" in nom_prop:
                    # Essayer différentes variantes pour les dates
                    variantes = [
                        nom_ifc,
                        nom_ifc.replace(" ", "_"),
                        nom_ifc.replace("_", " "),
                        "Date de réemploye" if "réemploye" in nom_ifc else nom_ifc,
                        "Date de réemploye" if "réemploye" in nom_ifc else nom_ifc
                    ]
                    for variante in variantes:
                        valeur = self.extraire_propriete_specifique(element, variante)
                        if valeur is not None:
                            break
                
                # Vérifier si la propriété est présente
                if valeur is None:
                    erreur = f"❌ PROPRIÉTÉ MANQUANTE: '{nom_ifc}' ({config['description']})"
                    erreurs.append(erreur)
                    print(erreur)
                    continue
                
                # Valider le format
                valide, resultat = self.valider_format(valeur, config['format'], nom_prop)
                
                if not valide:
                    erreur = f"❌ FORMAT INVALIDE: {resultat}"
                    erreurs.append(erreur)
                    print(erreur)
                else:
                    # Stocker la valeur validée
                    # Pour Date reemploye, on stocke avec underscore dans le JSON
                    if nom_prop == "Date de réemploye":
                        proprietes["Date de réemploye"] = resultat
                    else:
                        proprietes[nom_prop] = resultat
                    print(f"  ✓ {nom_prop}: {resultat}")
            
            # Si des erreurs, arrêter le processus
            if erreurs:
                print("\n❌ EXTRACTION ÉCHOUÉE - Propriétés manquantes ou invalides:")
                for err in erreurs:
                    print(f"  {err}")
                raise ValueError(f"Extraction échouée: {len(erreurs)} erreur(s)")
            
            return proprietes, []
            
        except Exception as e:
            print(f"❌ Erreur extraction propriétés: {e}")
            raise

    def demander_type_traitement(self) -> str:
        """
        Demande si on traite des maquettes à découper ou des objets unitaires
        """
        print("\n" + "="*60)
        print("🔧 TYPE DE TRAITEMENT")
        print("="*60)
        print("\n1. MAQUETTES IFC à découper en objets")
        print("2. OBJETS UNITAIRES IFC (juste séparer JSON)")
        
        while True:
            choix = input("\nVotre choix (1 ou 2): ").strip()
            if choix == '1':
                return 'maquette'
            elif choix == '2':
                return 'objets'
            else:
                print("❌ Choix invalide. Entrez 1 ou 2.")

    def collecter_metadonnees_maquette(self) -> Dict:
        """
        Collecte les métadonnées de la maquette via input utilisateur
        L'ID_maquette est extrait automatiquement depuis le fichier IFC
        """
        print("\n" + "="*60)
        print("📋 MÉTADONNÉES DE LA MAQUETTE")
        print("="*60)
        
        # Chercher l'ID_maquette dans le fichier
        id_maquette = None
        
        # Chercher dans tous les PropertySets
        for pset in self.model_ifc.by_type('IfcPropertySet'):
            for prop in pset.HasProperties:
                if prop.is_a('IfcPropertySingleValue'):
                    if prop.Name == "ID_maquette" and prop.NominalValue:
                        value = str(prop.NominalValue.wrappedValue)
                        if value.isdigit() and len(value) == 12:
                            id_maquette = value
                            break
        
        if not id_maquette:
            print("❌ ERREUR: ID_maquette non trouvé dans le fichier IFC!")
            print("   La propriété 'ID_maquette' (12 chiffres) doit être définie")
            raise ValueError("ID_maquette manquant dans le fichier IFC")
        
        print(f"✅ ID_maquette trouvé: {id_maquette}")
        
        metadonnees = {
            'ID_maquette': id_maquette,
            'nom_maquette': input("Nom de la maquette: ").strip() or "Diogène",
            'nom_architecte': input("Nom de l'architecte: ").strip() or "Renzo Piano",
            'coordonnees_geographiques': input("Coordonnées (lat/long): ").strip() or "46.5197/6.6323",
            'programme': input("Programme: ").strip() or "Logement",
            'date livraison': input("Date de livraison (JJ MM AAAA): ").strip() or datetime.now().strftime("%d %m %Y"),
            'date depot': datetime.now().strftime("%d %m %Y")
        }
        
        return metadonnees

    def traiter_fichier_maquette(self, fichier_path: Path) -> Dict:
        """
        Traite un fichier IFC comme maquette (découpage en objets)
        """
        print(f"\n📁 Traitement MAQUETTE: {fichier_path.name}")
        debut_traitement = time.time()
        
        try:
            # Charger le fichier
            self.model_ifc = ifcopenshell.open(str(fichier_path))
            self.chemin_fichier = fichier_path
            
            # Collecter les métadonnées
            metadonnees_maquette = self.collecter_metadonnees_maquette()
            
            # Récupérer l'ID_maquette
            id_maquette = metadonnees_maquette['ID_maquette']
            
            # Créer le dossier spécifique pour cette maquette
            nom_maquette_clean = re.sub(r'[^\w\-]', '', metadonnees_maquette['nom_maquette'])
            dossier_maquette = self.maquettes_dir / f"maquette_{nom_maquette_clean}_{id_maquette}"
            dossier_maquette.mkdir(exist_ok=True)
            
            # Extraire tous les éléments IFC
            elements = []
            
            # Types d'éléments à extraire
            types_elements = [
                'IfcProxy', 'IfcWall', 'IfcSlab', 'IfcBeam', 'IfcColumn',
                'IfcDoor', 'IfcWindow', 'IfcRoof', 'IfcStair', 'IfcRailing',
                'IfcBuildingElementProxy', 'IfcFurnishingElement'
            ]
            
            for type_element in types_elements:
                elements.extend(self.model_ifc.by_type(type_element))
            
            print(f"  Éléments trouvés: {len(elements)}")
            
            objets_crees = 0
            erreurs_totales = 0
            
            for idx, element in enumerate(elements, 1):
                try:
                    print(f"\n  📦 Objet {idx}/{len(elements)}:")
                    
                    # Extraire les propriétés avec validation stricte
                    proprietes, erreurs = self.extraire_toutes_proprietes_element(element)
                    
                    if erreurs:
                        erreurs_totales += 1
                        print(f"  ❌ Objet {idx} ignoré - propriétés manquantes/invalides")
                        continue

                    # === AJOUT HASH SHA-256 ===
                    # 1. Calculer le hash du fichier IFC
                    hash_ifc = self.calculer_hash_fichier(fichier_path)
                    proprietes['hash_ifc'] = hash_ifc
                    
                    # 2. Calculer le hash du JSON (après ajout du hash IFC)
                    hash_json = self.calculer_hash_json(proprietes)
                    proprietes['hash_json'] = hash_json
                    
                    print(f"  🔒 Hash JSON: {hash_json[:16]}...")
                    print(f"  🔒 Hash IFC: {hash_ifc[:16]}...")
                    # === FIN HASH SHA-256 ===
                    
                    # Nom de fichier unique
                    nom_fichier = f"{proprietes['ID']}_{proprietes['NOM'].replace(' ', '_')}"
                    nom_fichier = re.sub(r'[^\w\-]', '', nom_fichier)
                    
                    # 1. Créer le fichier JSON de l'objet
                    json_path = self.objets_json_dir / f"{nom_fichier}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(proprietes, f, indent=2, ensure_ascii=False)
                    
                    # 2. Créer le fichier IFC individuel
                    ifc_path = self.objets_ifc_dir / f"{nom_fichier}.ifc"
                    shutil.copy2(fichier_path, ifc_path)
                    
                    objets_crees += 1
                    
                except ValueError as e:
                    print(f"  ⚠️ Objet {idx} ignoré: {e}")
                    erreurs_totales += 1
                except Exception as e:
                    print(f"  ⚠️ Erreur objet {idx}: {e}")
                    erreurs_totales += 1
            
            if objets_crees == 0:
                raise ValueError(f"Aucun objet valide créé! {erreurs_totales} erreurs rencontrées")
            
            # Copier la maquette complète
            maquette_ifc_path = dossier_maquette / f"{nom_maquette_clean}.ifc"
            shutil.copy2(fichier_path, maquette_ifc_path)
            
            # === AJOUT HASH SHA-256 POUR LA MAQUETTE ===
            # 1. Calculer le hash du fichier IFC maquette
            hash_maquette_ifc = self.calculer_hash_fichier(fichier_path)
            metadonnees_maquette['hash_maquette_ifc'] = hash_maquette_ifc
            
            # 2. Calculer le hash du JSON maquette (après ajout du hash IFC)
            hash_maquette_json = self.calculer_hash_json(metadonnees_maquette)
            metadonnees_maquette['hash_maquette_json'] = hash_maquette_json
            
            print(f"  🔒 Hash JSON Maquette: {hash_maquette_json[:16]}...")
            print(f"  🔒 Hash IFC Maquette: {hash_maquette_ifc[:16]}...")
            # === FIN HASH SHA-256 MAQUETTE ===
            
            # Créer le JSON de la maquette
            maquette_json_path = dossier_maquette / f"{nom_maquette_clean}.json"
            with open(maquette_json_path, 'w', encoding='utf-8') as f:
                json.dump(metadonnees_maquette, f, indent=2, ensure_ascii=False)
            
            fin_traitement = time.time()
            self.temps_traitement = fin_traitement - debut_traitement
            print(f"⏱️ Temps d'extraction: {self.temps_traitement:.2f} secondes")
            
            print(f"\n  ✅ {objets_crees} objets valides créés")
            if erreurs_totales > 0:
                print(f"  ⚠️ {erreurs_totales} objets ignorés (propriétés manquantes/invalides)")
            
            return {
                'status': 'success',
                'objets_crees': objets_crees,
                'erreurs': erreurs_totales,
                'maquette_path': str(dossier_maquette)
            }
            
        except Exception as e:
            print(f"  ❌ Erreur fatale: {e}")
            fin_traitement = time.time()
            self.temps_traitement = fin_traitement - debut_traitement
            print(f"⏱️ Temps d'extraction: {self.temps_traitement:.2f} secondes")
            return {'status': 'error', 'message': str(e)}

    def traiter_objet_unitaire(self, fichier_path: Path) -> Dict:
        """
        Traite un fichier IFC comme objet unitaire (juste séparer JSON)
        """
        print(f"\n📁 Traitement OBJET UNITAIRE: {fichier_path.name}")
        debut_traitement = time.time()
        
        try:
            # Charger le fichier
            self.model_ifc = ifcopenshell.open(str(fichier_path))
            self.chemin_fichier = fichier_path
            
            # Trouver le premier élément principal
            element = None
            for type_element in ['IfcProxy', 'IfcBuildingElementProxy', 'IfcBeam', 'IfcColumn']:
                elements = self.model_ifc.by_type(type_element)
                if elements:
                    element = elements[0]
                    break
            
            if not element:
                # Prendre n'importe quel élément
                all_elements = self.model_ifc.by_type('IfcElement')
                if all_elements:
                    element = all_elements[0]
            
            if element:
                # Extraire les propriétés avec validation stricte
                proprietes, erreurs = self.extraire_toutes_proprietes_element(element)
                
                if erreurs:
                    print(f"  ❌ Objet invalide - propriétés manquantes/invalides")
                    return {'status': 'error', 'message': 'Propriétés manquantes ou invalides'}

                # === AJOUT HASH SHA-256 ===
                # 1. Calculer le hash du fichier IFC
                hash_ifc = self.calculer_hash_fichier(fichier_path)
                proprietes['hash_ifc'] = hash_ifc
                
                # 2. Calculer le hash du JSON (après ajout du hash IFC)
                hash_json = self.calculer_hash_json(proprietes)
                proprietes['hash_json'] = hash_json
                
                print(f"  🔒 Hash JSON: {hash_json[:16]}...")
                print(f"  🔒 Hash IFC: {hash_ifc[:16]}...")
                # === FIN HASH SHA-256 ===
                
                # Nom de fichier
                nom_fichier = f"{proprietes['ID']}_{proprietes['NOM'].replace(' ', '_')}"
                nom_fichier = re.sub(r'[^\w\-]', '', nom_fichier)
                
                # Créer le JSON
                json_path = self.objets_json_dir / f"{nom_fichier}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(proprietes, f, indent=2, ensure_ascii=False)
                
                # Copier l'IFC
                ifc_path = self.objets_ifc_dir / f"{nom_fichier}.ifc"
                shutil.copy2(fichier_path, ifc_path)
                
                fin_traitement = time.time()  
                self.temps_traitement = fin_traitement - debut_traitement
                print(f"⏱️ Temps d'extraction: {self.temps_traitement:.2f} secondes")
                
                print(f"  ✅ Objet traité avec succès")
                return {'status': 'success'}
            else:
                print(f"  ❌ Aucun élément trouvé dans le fichier")
                return {'status': 'error', 'message': 'Aucun élément IFC valide'}
                
        except ValueError as e:
            print(f"  ❌ Erreur de validation: {e}")
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            fin_traitement = time.time()  
            self.temps_traitement = fin_traitement - debut_traitement
            print(f"⏱️ Temps d'extraction: {self.temps_traitement:.2f} secondes")
            return {'status': 'error', 'message': str(e)}

    def traiter_tous_fichiers(self):
        """
        Traite automatiquement tous les fichiers dans ifc-files/
        """
        print("\n" + "="*60)
        print("🚀 TRAITEMENT AUTOMATIQUE DE TOUS LES FICHIERS")
        print("="*60)
        
        # Lister tous les fichiers IFC
        fichiers_ifc = list(self.ifc_files_dir.glob('*.ifc'))
        
        if not fichiers_ifc:
            print("❌ Aucun fichier IFC trouvé dans data/ifc-files/")
            return
        
        print(f"📊 {len(fichiers_ifc)} fichiers IFC trouvés")
        
        # Demander le type de traitement
        type_traitement = self.demander_type_traitement()
        
        stats = {
            'total': len(fichiers_ifc),
            'success': 0,
            'errors': 0,
            'objets_crees': 0,
            'objets_ignores': 0
        }
        
        # Traiter chaque fichier
        for fichier in fichiers_ifc:
            if type_traitement == 'maquette':
                result = self.traiter_fichier_maquette(fichier)
                if result['status'] == 'success':
                    stats['success'] += 1
                    stats['objets_crees'] += result.get('objets_crees', 0)
                    stats['objets_ignores'] += result.get('erreurs', 0)
                else:
                    stats['errors'] += 1
            else:
                result = self.traiter_objet_unitaire(fichier)
                if result['status'] == 'success':
                    stats['success'] += 1
                    stats['objets_crees'] += 1
                else:
                    stats['errors'] += 1
                    stats['objets_ignores'] += 1
        
        # Résumé final
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DU TRAITEMENT")
        print("="*60)
        print(f"Total fichiers: {stats['total']}")
        print(f"✅ Fichiers traités avec succès: {stats['success']}")
        print(f"❌ Fichiers en erreur: {stats['errors']}")
        print(f"🔧 Objets valides créés: {stats['objets_crees']}")
        print(f"⚠️ Objets ignorés (invalides): {stats['objets_ignores']}")
        
        print("\n📁 FICHIERS CRÉÉS DANS:")
        print(f"  - Objets IFC: {self.objets_ifc_dir}")
        print(f"  - Objets JSON: {self.objets_json_dir}")
        print(f"  - Maquettes: {self.maquettes_dir}")
        
        print("\n🔒 HASHS GÉNÉRÉS:")
        print("  → Hash JSON: Intégrité des métadonnées")  
        print("  → Hash IFC: Intégrité des fichiers 3D")
        print("  → Prêt pour smart contracts Ethereum")
        
        if stats['objets_crees'] > 0:
            print("\n✅ PRÊT POUR BROWNIE/ETHEREUM!")
            print("  → Upload vers Pinata IPFS")
            print("  → Déploiement smart contracts")
            print("  → Tests sur Ganache")
        else:
            print("\n❌ AUCUN OBJET VALIDE CRÉÉ")
            print("  Vérifiez que vos fichiers IFC contiennent toutes les propriétés requises:")
            for nom, config in self.parametres_obligatoires.items():
                print(f"    - {nom}: {config['description']}")

def main():
    """Fonction principale"""
    print("╔" + "="*58 + "╗")
    print("║" + " R9 IFC EXTRACTOR - BROWNIE/ETHEREUM ".center(58) + "║")
    print("║" + " Version 5.2 - Hash SHA-256 ".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    extracteur = ExtracteurIFC_R9_Brownie()
    
    try:
        extracteur.traiter_tous_fichiers()
    except KeyboardInterrupt:
        print("\n\n⛔ Processus interrompu par l'utilisateur.")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()