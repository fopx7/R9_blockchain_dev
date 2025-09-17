#!/usr/bin/env python3
"""
PINATA_UPLOADER_2.0.py
======================
Script d'upload automatique vers Pinata IPFS pour projet R9
Upload des fichiers IFC et JSON extraits par IFC_extractor v5.2
Génération du mapping CID pour smart contracts
Leopold MALKIT SINGH - Version 2.0
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import time
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PinataUploaderR9:
    """Gestionnaire d'upload spécialisé pour les données R9 extraites"""
    
    def __init__(self):
        # Chargement des variables d'environnement
        load_dotenv()
        
        self.api_key = os.getenv('PINATA_API_KEY')
        self.secret_key = os.getenv('PINATA_SECRET_KEY')
        
        # URLs de l'API Pinata
        self.base_url = "https://api.pinata.cloud"
        self.pin_file_url = f"{self.base_url}/pinning/pinFileToIPFS"
        self.pin_json_url = f"{self.base_url}/pinning/pinJSONToIPFS"
        self.test_url = f"{self.base_url}/data/testAuthentication"
        
        # Headers d'authentification
        self.headers = {
            'pinata_api_key': self.api_key,
            'pinata_secret_api_key': self.secret_key
        }
        
        # Structure des dossiers R9
        self.data_dir = Path('data/processed')
        self.objets_ifc_dir = self.data_dir / 'objets_ifc'
        self.objets_json_dir = self.data_dir / 'objets_json'
        self.maquettes_dir = self.data_dir / 'maquettes'
        
        # Fichier de mapping CID
        self.mapping_file = Path('data/cid_mapping_r9.json')
        
        # Statistiques
        self.stats = {
            'objets_json_uploaded': 0,
            'objets_ifc_uploaded': 0,
            'maquettes_uploaded': 0,
            'erreurs': [],
            'temps_total': 0,
            'cout_total_bytes': 0
        }
        
        # Validation des clés
        self._valider_configuration()
    
    def _valider_configuration(self):
        """Valide la configuration des clés Pinata"""
        if not self.api_key or self.api_key == "your_pinata_api_key_here":
            raise ValueError("❌ PINATA_API_KEY non configurée dans le fichier .env")
        
        if not self.secret_key or self.secret_key == "your_pinata_secret_key_here":
            raise ValueError("❌ PINATA_SECRET_KEY non configurée dans le fichier .env")
        
        logger.info("✅ Clés Pinata chargées depuis .env")
    
    def tester_connexion(self) -> bool:
        """Teste la connexion à l'API Pinata"""
        try:
            logger.info("🔍 Test de la connexion Pinata...")
            
            response = requests.get(self.test_url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Connexion Pinata réussie! Message: {result.get('message', 'OK')}")
                return True
            else:
                logger.error(f"❌ Échec connexion Pinata. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de connexion: {e}")
            return False
    
    def upload_fichier_ifc(self, chemin_fichier: Path, metadata: Dict) -> Optional[str]:
        """Upload un fichier IFC vers IPFS"""
        try:
            if not chemin_fichier.exists():
                logger.error(f"❌ Fichier IFC non trouvé: {chemin_fichier}")
                return None
            
            logger.info(f"📤 Upload IFC: {chemin_fichier.name}")
            
            with open(chemin_fichier, 'rb') as fichier:
                files = {
                    'file': (chemin_fichier.name, fichier, 'application/octet-stream')
                }
                
                pinata_metadata = {
                    'name': chemin_fichier.name,
                    'keyvalues': {
                        'projet': 'R9_blockchain_bim',
                        'type': 'fichier_ifc',
                        'objet_id': metadata.get('objet_id', 'unknown'),
                        'materiau': metadata.get('materiau', 'unknown'),
                        'timestamp': str(int(time.time()))
                    }
                }
                
                data = {
                    'pinataMetadata': json.dumps(pinata_metadata),
                    'pinataOptions': json.dumps({'cidVersion': 1})
                }
                
                response = requests.post(
                    self.pin_file_url,
                    files=files,
                    data=data,
                    headers=self.headers,
                    timeout=120
                )
            
            if response.status_code == 200:
                result = response.json()
                cid = result['IpfsHash']
                taille = result['PinSize']
                
                logger.info(f"✅ IFC uploadé - CID: {cid[:20]}... ({taille} bytes)")
                self.stats['objets_ifc_uploaded'] += 1
                self.stats['cout_total_bytes'] += taille
                return cid
            else:
                logger.error(f"❌ Échec upload IFC: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur upload IFC: {e}")
            return None
    
    def upload_json_metadata(self, data_json: Dict, nom_fichier: str, metadata: Dict) -> Optional[str]:
        """Upload des métadonnées JSON vers IPFS"""
        try:
            logger.info(f"📤 Upload JSON: {nom_fichier}")
            
            pinata_metadata = {
                'name': nom_fichier,
                'keyvalues': {
                    'projet': 'R9_blockchain_bim',
                    'type': metadata.get('type', 'metadata_objet'),
                    'objet_id': metadata.get('objet_id', 'unknown'),
                    'materiau': metadata.get('materiau', 'unknown'),
                    'hash_json': data_json.get('hash_json', 'unknown'),
                    'hash_ifc': data_json.get('hash_ifc', 'unknown'),
                    'timestamp': str(int(time.time()))
                }
            }
            
            payload = {
                'pinataContent': data_json,
                'pinataMetadata': pinata_metadata,
                'pinataOptions': {'cidVersion': 1}
            }
            
            response = requests.post(
                self.pin_json_url,
                json=payload,
                headers={**self.headers, 'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result['IpfsHash']
                taille = result['PinSize']
                
                logger.info(f"✅ JSON uploadé - CID: {cid[:20]}... ({taille} bytes)")
                self.stats['objets_json_uploaded'] += 1
                self.stats['cout_total_bytes'] += taille
                return cid
            else:
                logger.error(f"❌ Échec upload JSON: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur upload JSON: {e}")
            return None
    
    def upload_objets_r9(self) -> Dict:
        """Upload tous les objets R9 (IFC + JSON) vers IPFS"""
        logger.info("🚀 UPLOAD DES OBJETS R9 VERS IPFS")
        logger.info("="*50)
        
        mapping_objets = {}
        
        # Vérifier la présence des dossiers
        if not self.objets_json_dir.exists():
            logger.error(f"❌ Dossier objets_json non trouvé: {self.objets_json_dir}")
            return {}
        
        # Lister tous les fichiers JSON
        fichiers_json = list(self.objets_json_dir.glob("*.json"))
        
        if not fichiers_json:
            logger.warning("⚠️ Aucun fichier JSON trouvé")
            return {}
        
        logger.info(f"📊 {len(fichiers_json)} objets R9 à uploader")
        
        for idx, fichier_json in enumerate(fichiers_json, 1):
            try:
                logger.info(f"\n📦 Objet {idx}/{len(fichiers_json)}: {fichier_json.stem}")
                
                # 1. Charger les métadonnées JSON
                with open(fichier_json, 'r', encoding='utf-8') as f:
                    metadata_objet = json.load(f)
                
                objet_id = metadata_objet.get('ID', 'unknown')
                materiau = metadata_objet.get('Materiau', 'unknown')
                nom_objet = metadata_objet.get('NOM', 'unknown')
                
                # 2. Upload du JSON metadata
                metadata_upload = {
                    'type': 'metadata_objet',
                    'objet_id': objet_id,
                    'materiau': materiau
                }
                
                cid_json = self.upload_json_metadata(
                    metadata_objet, 
                    fichier_json.name, 
                    metadata_upload
                )
                
                if not cid_json:
                    self.stats['erreurs'].append(f"Échec upload JSON: {fichier_json.name}")
                    continue
                
                # 3. Upload du fichier IFC correspondant
                fichier_ifc = self.objets_ifc_dir / f"{fichier_json.stem}.ifc"
                cid_ifc = None
                
                if fichier_ifc.exists():
                    cid_ifc = self.upload_fichier_ifc(fichier_ifc, metadata_upload)
                    if not cid_ifc:
                        self.stats['erreurs'].append(f"Échec upload IFC: {fichier_ifc.name}")
                else:
                    logger.warning(f"⚠️ Fichier IFC non trouvé: {fichier_ifc.name}")
                
                # 4. Enregistrer le mapping
                mapping_objets[objet_id] = {
                    'nom': nom_objet,
                    'materiau': materiau,
                    'id_maquette': metadata_objet.get('ID_maquette', 'unknown'),
                    'cid_json': cid_json,
                    'cid_ifc': cid_ifc,
                    'hash_json': metadata_objet.get('hash_json', ''),
                    'hash_ifc': metadata_objet.get('hash_ifc', ''),
                    'timestamp_upload': int(time.time()),
                    'urls': {
                        'json': f"https://gateway.pinata.cloud/ipfs/{cid_json}",
                        'ifc': f"https://gateway.pinata.cloud/ipfs/{cid_ifc}" if cid_ifc else None
                    }
                }
                
                logger.info(f"✅ Objet {objet_id} uploadé avec succès")
                
                # Pause pour éviter les limites de taux
                time.sleep(1)
                
            except Exception as e:
                erreur = f"Erreur objet {fichier_json.name}: {e}"
                logger.error(f"❌ {erreur}")
                self.stats['erreurs'].append(erreur)
                continue
        
        return mapping_objets
    
    def upload_maquettes_r9(self) -> Dict:
        """Upload les maquettes complètes vers IPFS"""
        logger.info("\n🏗️ UPLOAD DES MAQUETTES R9")
        logger.info("="*40)
        
        mapping_maquettes = {}
        
        if not self.maquettes_dir.exists():
            logger.warning("⚠️ Dossier maquettes non trouvé")
            return {}
        
        # Lister les dossiers de maquettes
        dossiers_maquettes = [d for d in self.maquettes_dir.iterdir() if d.is_dir()]
        
        if not dossiers_maquettes:
            logger.warning("⚠️ Aucune maquette trouvée")
            return {}
        
        logger.info(f"📊 {len(dossiers_maquettes)} maquettes à uploader")
        
        for idx, dossier_maquette in enumerate(dossiers_maquettes, 1):
            try:
                logger.info(f"\n🏗️ Maquette {idx}/{len(dossiers_maquettes)}: {dossier_maquette.name}")
                
                # Chercher les fichiers JSON et IFC de la maquette
                fichiers_json = list(dossier_maquette.glob("*.json"))
                fichiers_ifc = list(dossier_maquette.glob("*.ifc"))
                
                if not fichiers_json or not fichiers_ifc:
                    logger.warning("⚠️ Fichiers maquette manquants")
                    continue
                
                fichier_json = fichiers_json[0]
                fichier_ifc = fichiers_ifc[0]
                
                # 1. Charger les métadonnées de la maquette
                with open(fichier_json, 'r', encoding='utf-8') as f:
                    metadata_maquette = json.load(f)
                
                id_maquette = metadata_maquette.get('ID_maquette', 'unknown')
                nom_maquette = metadata_maquette.get('nom_maquette', 'unknown')
                
                # 2. Upload du JSON maquette
                metadata_upload = {
                    'type': 'metadata_maquette',
                    'objet_id': id_maquette,
                    'materiau': 'maquette_complete'
                }
                
                cid_json = self.upload_json_metadata(
                    metadata_maquette,
                    fichier_json.name,
                    metadata_upload
                )
                
                if not cid_json:
                    self.stats['erreurs'].append(f"Échec upload maquette JSON: {fichier_json.name}")
                    continue
                
                # 3. Upload du fichier IFC maquette
                cid_ifc = self.upload_fichier_ifc(fichier_ifc, metadata_upload)
                
                if not cid_ifc:
                    self.stats['erreurs'].append(f"Échec upload maquette IFC: {fichier_ifc.name}")
                    continue
                
                # 4. Enregistrer le mapping
                mapping_maquettes[id_maquette] = {
                    'nom_maquette': nom_maquette,
                    'nom_architecte': metadata_maquette.get('nom_architecte', 'unknown'),
                    'programme': metadata_maquette.get('programme', 'unknown'),
                    'cid_json': cid_json,
                    'cid_ifc': cid_ifc,
                    'hash_maquette_json': metadata_maquette.get('hash_maquette_json', ''),
                    'hash_maquette_ifc': metadata_maquette.get('hash_maquette_ifc', ''),
                    'timestamp_upload': int(time.time()),
                    'urls': {
                        'json': f"https://gateway.pinata.cloud/ipfs/{cid_json}",
                        'ifc': f"https://gateway.pinata.cloud/ipfs/{cid_ifc}"
                    }
                }
                
                self.stats['maquettes_uploaded'] += 1
                logger.info(f"✅ Maquette {id_maquette} uploadée avec succès")
                
                time.sleep(2)  # Pause plus longue pour les maquettes
                
            except Exception as e:
                erreur = f"Erreur maquette {dossier_maquette.name}: {e}"
                logger.error(f"❌ {erreur}")
                self.stats['erreurs'].append(erreur)
                continue
        
        return mapping_maquettes
    
    def sauvegarder_mapping_complet(self, mapping_objets: Dict, mapping_maquettes: Dict):
        """Sauvegarde le mapping complet des CID pour les smart contracts"""
        try:
            mapping_complet = {
                'metadata': {
                    'projet': 'R9_blockchain_bim',
                    'version': '2.0',
                    'timestamp_creation': int(time.time()),
                    'date_creation': datetime.now().isoformat(),
                    'extracteur_version': '5.2',
                    'statistiques': self.stats
                },
                'objets': mapping_objets,
                'maquettes': mapping_maquettes,
                'smart_contract_data': {
                    'total_objets': len(mapping_objets),
                    'total_maquettes': len(mapping_maquettes),
                    'ready_for_deployment': True if mapping_objets else False
                }
            }
            
            # Créer le dossier data si nécessaire
            self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder le fichier de mapping
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping_complet, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Mapping CID sauvegardé: {self.mapping_file}")
            logger.info(f"📄 Fichier de mapping prêt pour les smart contracts")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde mapping: {e}")
    
    def upload_complet_r9(self) -> bool:
        """Upload complet de tous les éléments R9 vers IPFS"""
        debut = time.time()
        
        print("╔" + "="*58 + "╗")
        print("║" + " PINATA UPLOADER R9 v2.0 ".center(58) + "║")
        print("║" + " Upload automatique vers IPFS ".center(58) + "║")
        print("╚" + "="*58 + "╝")
        
        try:
            # 1. Test de connexion
            if not self.tester_connexion():
                logger.error("❌ Impossible de se connecter à Pinata")
                return False
            
            # 2. Upload des objets R9
            mapping_objets = self.upload_objets_r9()
            
            # 3. Upload des maquettes R9
            mapping_maquettes = self.upload_maquettes_r9()
            
            # 4. Sauvegarde du mapping
            self.sauvegarder_mapping_complet(mapping_objets, mapping_maquettes)
            
            # 5. Statistiques finales
            fin = time.time()
            self.stats['temps_total'] = fin - debut
            
            self._afficher_statistiques_finales()
            
            return len(mapping_objets) > 0 or len(mapping_maquettes) > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'upload complet: {e}")
            return False
    
    def _afficher_statistiques_finales(self):
        """Affiche les statistiques finales d'upload"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ UPLOAD PINATA R9")
        print("="*60)
        print(f"✅ Objets JSON uploadés: {self.stats['objets_json_uploaded']}")
        print(f"✅ Objets IFC uploadés: {self.stats['objets_ifc_uploaded']}")
        print(f"✅ Maquettes uploadées: {self.stats['maquettes_uploaded']}")
        print(f"⏱️ Temps total: {self.stats['temps_total']:.2f} secondes")
        print(f"💾 Volume total: {self.stats['cout_total_bytes']:,} bytes")
        
        if self.stats['erreurs']:
            print(f"\n⚠️ Erreurs ({len(self.stats['erreurs'])}):")
            for erreur in self.stats['erreurs'][:5]:  # Afficher max 5 erreurs
                print(f"  - {erreur}")
            if len(self.stats['erreurs']) > 5:
                print(f"  ... et {len(self.stats['erreurs']) - 5} autres erreurs")
        
        total_uploads = (self.stats['objets_json_uploaded'] + 
                        self.stats['objets_ifc_uploaded'] + 
                        self.stats['maquettes_uploaded'])
        
        if total_uploads > 0:
            print(f"\n🚀 UPLOAD RÉUSSI!")
            print(f"📄 Mapping CID sauvegardé: {self.mapping_file}")
            print(f"⛓️ PRÊT POUR SMART CONTRACTS ETHEREUM")
        else:
            print(f"\n❌ AUCUN FICHIER UPLOADÉ")
            print(f"🔧 Vérifiez que l'extracteur IFC a été exécuté")


def main():
    """Fonction principale"""
    try:
        uploader = PinataUploaderR9()
        success = uploader.upload_complet_r9()
        
        if success:
            print("\n🎉 Upload Pinata terminé avec succès!")
            print("🔗 Prochaine étape: Déploiement smart contract")
        else:
            print("\n❌ Échec de l'upload Pinata")
            print("🔧 Vérifiez la configuration et les fichiers source")
            
    except KeyboardInterrupt:
        print("\n⛔ Upload interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()