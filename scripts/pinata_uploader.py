#!/usr/bin/env python3
"""
Script d'upload Pinata IPFS pour R9
Upload des fichiers IFC et JSON vers IPFS via l'API Pinata
Compatible avec Brownie Framework
Leopold MALKIT SINGH
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PinataUploader:
    """Gestionnaire d'upload vers IPFS via l'API Pinata"""
    
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
        
        # Validation des clés
        self._valider_configuration()
    
    def _valider_configuration(self):
        """Valide la configuration des clés Pinata"""
        if not self.api_key or self.api_key == "votre_cle_api_pinata":
            raise ValueError("❌ PINATA_API_KEY non configurée dans le fichier .env")
        
        if not self.secret_key or self.secret_key == "votre_cle_secrete_pinata":
            raise ValueError("❌ PINATA_SECRET_KEY non configurée dans le fichier .env")
        
        logger.info("✅ Clés Pinata chargées depuis .env")
    
    def tester_connexion(self) -> bool:
        """Teste la connexion à l'API Pinata"""
        try:
            logger.info("🔍 Test de la connexion Pinata...")
            
            response = requests.get(self.test_url, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Connexion Pinata réussie! Message: {result.get('message', 'OK')}")
                return True
            else:
                logger.error(f"❌ Échec connexion Pinata. Status: {response.status_code}")
                logger.error(f"Réponse: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de connexion: {e}")
            return False
    
    def upload_fichier(self, chemin_fichier: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Upload un fichier vers IPFS via Pinata
        
        Args:
            chemin_fichier: Chemin vers le fichier à uploader
            metadata: Métadonnées optionnelles pour le fichier
            
        Returns:
            CID IPFS du fichier uploadé ou None en cas d'erreur
        """
        try:
            fichier_path = Path(chemin_fichier)
            
            if not fichier_path.exists():
                logger.error(f"❌ Fichier non trouvé: {chemin_fichier}")
                return None
            
            logger.info(f"📤 Upload de {fichier_path.name} vers IPFS...")
            
            # Préparation du fichier
            with open(fichier_path, 'rb') as fichier:
                files = {
                    'file': (fichier_path.name, fichier, 'application/octet-stream')
                }
                
                # Métadonnées Pinata
                pinata_metadata = {
                    'name': fichier_path.name,
                    'keyvalues': metadata or {}
                }
                
                # Options Pinata
                pinata_options = {
                    'cidVersion': 1,
                    'wrapWithDirectory': False
                }
                
                data = {
                    'pinataMetadata': json.dumps(pinata_metadata),
                    'pinataOptions': json.dumps(pinata_options)
                }
                
                # Envoi de la requête
                response = requests.post(
                    self.pin_file_url,
                    files=files,
                    data=data,
                    headers=self.headers
                )
            
            if response.status_code == 200:
                result = response.json()
                cid = result['IpfsHash']
                taille = result['PinSize']
                
                logger.info(f"✅ Upload réussi!")
                logger.info(f"   CID: {cid}")
                logger.info(f"   Taille: {taille} bytes")
                logger.info(f"   URL: https://gateway.pinata.cloud/ipfs/{cid}")
                
                return cid
            else:
                logger.error(f"❌ Échec upload. Status: {response.status_code}")
                logger.error(f"Réponse: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'upload: {e}")
            return None
    
    def upload_json(self, data_json: Dict, nom_fichier: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Upload des données JSON vers IPFS via Pinata
        
        Args:
            data_json: Données JSON à uploader
            nom_fichier: Nom pour identifier le fichier
            metadata: Métadonnées optionnelles
            
        Returns:
            CID IPFS des données JSON ou None en cas d'erreur
        """
        try:
            logger.info(f"📤 Upload JSON '{nom_fichier}' vers IPFS...")
            
            # Préparation des métadonnées
            pinata_metadata = {
                'name': nom_fichier,
                'keyvalues': metadata or {}
            }
            
            # Options Pinata
            pinata_options = {
                'cidVersion': 1
            }
            
            # Données à envoyer
            payload = {
                'pinataContent': data_json,
                'pinataMetadata': pinata_metadata,
                'pinataOptions': pinata_options
            }
            
            # Envoi de la requête
            response = requests.post(
                self.pin_json_url,
                json=payload,
                headers={**self.headers, 'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result['IpfsHash']
                taille = result['PinSize']
                
                logger.info(f"✅ Upload JSON réussi!")
                logger.info(f"   CID: {cid}")
                logger.info(f"   Taille: {taille} bytes")
                logger.info(f"   URL: https://gateway.pinata.cloud/ipfs/{cid}")
                
                return cid
            else:
                logger.error(f"❌ Échec upload JSON. Status: {response.status_code}")
                logger.error(f"Réponse: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'upload JSON: {e}")
            return None
    
    def upload_dossier_r9(self, dossier_extraction: str) -> Dict[str, List[str]]:
        """
        Upload complet d'un dossier d'extraction R9 vers IPFS
        
        Args:
            dossier_extraction: Chemin vers le dossier d'extraction R9
            
        Returns:
            Dictionnaire avec les CID de tous les fichiers uploadés
        """
        dossier = Path(dossier_extraction)
        
        if not dossier.exists():
            logger.error(f"❌ Dossier d'extraction non trouvé: {dossier_extraction}")
            return {}
        
        resultats = {
            'objets_ifc_cids': [],
            'objets_json_cids': [],
            'maquette_ifc_cid': None,
            'maquette_json_cid': None,
            'erreurs': []
        }
        
        logger.info(f"🚀 Upload complet du dossier R9: {dossier.name}")
        
        # 1. Upload des objets IFC individuels
        dossier_objets_ifc = dossier / "objets_ifc"
        if dossier_objets_ifc.exists():
            fichiers_ifc = list(dossier_objets_ifc.glob("*.ifc"))
            logger.info(f"📁 Upload de {len(fichiers_ifc)} objets IFC...")
            
            for fichier_ifc in fichiers_ifc:
                metadata = {
                    'type': 'objet_ifc',
                    'projet': 'R9_blockchain_bim'
                }
                
                cid = self.upload_fichier(str(fichier_ifc), metadata)
                if cid:
                    resultats['objets_ifc_cids'].append({
                        'fichier': fichier_ifc.name,
                        'cid': cid
                    })
                else:
                    resultats['erreurs'].append(f"Échec upload: {fichier_ifc.name}")
                
                # Pause entre uploads pour éviter les limites de taux
                time.sleep(1)
        
        # 2. Upload des JSON d'objets
        dossier_objets_json = dossier / "objets_json"
        if dossier_objets_json.exists():
            fichiers_json = list(dossier_objets_json.glob("*.json"))
            logger.info(f"📁 Upload de {len(fichiers_json)} métadonnées JSON...")
            
            for fichier_json in fichiers_json:
                try:
                    with open(fichier_json, 'r', encoding='utf-8') as f:
                        data_json = json.load(f)
                    
                    metadata = {
                        'type': 'metadata_objet',
                        'projet': 'R9_blockchain_bim'
                    }
                    
                    cid = self.upload_json(data_json, fichier_json.name, metadata)
                    if cid:
                        resultats['objets_json_cids'].append({
                            'fichier': fichier_json.name,
                            'cid': cid
                        })
                    else:
                        resultats['erreurs'].append(f"Échec upload JSON: {fichier_json.name}")
                        
                except Exception as e:
                    resultats['erreurs'].append(f"Erreur lecture {fichier_json.name}: {e}")
                
                time.sleep(0.5)
        
        # 3. Upload de la maquette IFC complète
        fichiers_maquette_ifc = list(dossier.glob("maquette_*.ifc"))
        if fichiers_maquette_ifc:
            maquette_ifc = fichiers_maquette_ifc[0]
            logger.info(f"📁 Upload de la maquette complète: {maquette_ifc.name}")
            
            metadata = {
                'type': 'maquette_complete',
                'projet': 'R9_blockchain_bim'
            }
            
            cid = self.upload_fichier(str(maquette_ifc), metadata)
            if cid:
                resultats['maquette_ifc_cid'] = cid
            else:
                resultats['erreurs'].append(f"Échec upload maquette: {maquette_ifc.name}")
        
        # 4. Upload des métadonnées de maquette
        fichiers_maquette_json = list(dossier.glob("maquette_*.json"))
        if fichiers_maquette_json:
            maquette_json = fichiers_maquette_json[0]
            logger.info(f"📁 Upload métadonnées maquette: {maquette_json.name}")
            
            try:
                with open(maquette_json, 'r', encoding='utf-8') as f:
                    data_maquette = json.load(f)
                
                metadata = {
                    'type': 'metadata_maquette',
                    'projet': 'R9_blockchain_bim'
                }
                
                cid = self.upload_json(data_maquette, maquette_json.name, metadata)
                if cid:
                    resultats['maquette_json_cid'] = cid
                else:
                    resultats['erreurs'].append(f"Échec upload métadonnées maquette")
                    
            except Exception as e:
                resultats['erreurs'].append(f"Erreur lecture métadonnées maquette: {e}")
        
        # Résumé
        logger.info("📊 RÉSUMÉ UPLOAD PINATA:")
        logger.info(f"  ✅ Objets IFC: {len(resultats['objets_ifc_cids'])}")
        logger.info(f"  ✅ Métadonnées JSON: {len(resultats['objets_json_cids'])}")
        logger.info(f"  ✅ Maquette IFC: {'Oui' if resultats['maquette_ifc_cid'] else 'Non'}")
        logger.info(f"  ✅ Maquette JSON: {'Oui' if resultats['maquette_json_cid'] else 'Non'}")
        
        if resultats['erreurs']:
            logger.warning(f"  ⚠️  Erreurs: {len(resultats['erreurs'])}")
            for erreur in resultats['erreurs']:
                logger.warning(f"    - {erreur}")
        
        return resultats


def test_pinata_connection():
    """Test simple de la connexion Pinata"""
    try:
        uploader = PinataUploader()
        return uploader.tester_connexion()
    except Exception as e:
        print(f"❌ Erreur test Pinata: {e}")
        return False


def upload_fichier_simple(chemin_fichier: str) -> Optional[str]:
    """Upload simple d'un fichier vers Pinata"""
    try:
        uploader = PinataUploader()
        return uploader.upload_fichier(chemin_fichier)
    except Exception as e:
        logger.error(f"❌ Erreur upload: {e}")
        return None


def main():
    """Fonction de test et démonstration"""
    print("🔗 TEST DE CONNEXION PINATA POUR R9")
    print("="*50)
    
    # Test de connexion
    if test_pinata_connection():
        print("✅ Pinata configuré correctement!")
        
        # Test d'upload d'un fichier exemple
        fichier_test = input("\nChemin d'un fichier test (optionnel): ").strip()
        if fichier_test and Path(fichier_test).exists():
            cid = upload_fichier_simple(fichier_test)
            if cid:
                print(f"🚀 Fichier uploadé avec succès!")
                print(f"CID: {cid}")
                print(f"URL: https://gateway.pinata.cloud/ipfs/{cid}")
    else:
        print("❌ Problème de configuration Pinata")
        print("\n🔧 Vérifiez vos clés dans le fichier .env:")
        print("   PINATA_API_KEY=votre_vraie_cle")
        print("   PINATA_SECRET_KEY=votre_vraie_cle_secrete")


if __name__ == "__main__":
    main()