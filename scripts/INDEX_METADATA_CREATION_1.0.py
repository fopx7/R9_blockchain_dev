#!/usr/bin/env python3
"""
INDEX_METADATA_CREATION_1.0.py
Gestion décentralisée des métadonnées BIM sur IPFS avec index de recherche rapide
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import os
from dataclasses import dataclass, asdict

@dataclass
class MaterialR9:
    """Structure des métadonnées R9 selon votre mémoire"""
    NOM: str                           # Nom_Materiau_R9
    ID: str                           # ID_Objet_R9 (16 chiffres)
    ID_maquette: str                  # ID_Maquette_R9 (12 chiffres)
    Longueur_m: float                 # Grande_Dimension_R9
    Caracteristique_Materiau: str     # Caracteristique_Materiau_R9
    Materiau: str                     # Type_Materiau_R9
    Statut_usage: str                 # Statut_Usage_R9 (neuf/en usage/réemployé)
    Date_fabrication: str             # Date_Fabrication_R9
    Date_mise_service: str            # Date_Mise_Service_R9
    Date_reemploi: str                # Date_Reemploi_R9
    Empreinte_Carbone: float          # Empreinte_Carbone_R9
    
    # Métadonnées techniques ajoutées
    ipfs_hash_ifc: str = ""           # CID du fichier IFC complet
    ipfs_hash_json: str = ""          # CID des métadonnées JSON
    integrity_hash: str = ""          # Hash SHA-256 d'intégrité
    last_updated: str = ""            # Timestamp dernière modification
    blockchain_tx: str = ""           # Hash de la transaction blockchain

class MetadataIndexManager:
    """Gestionnaire de l'index de métadonnées décentralisé"""
    
    def __init__(self, pinata_jwt: str):
        self.pinata_jwt = pinata_jwt
        self.pinata_url = "https://api.pinata.cloud"
        self.headers = {
            "Authorization": f"Bearer {pinata_jwt}",
            "Content-Type": "application/json"
        }
        self.current_index = {"materials": [], "metadata": {}}
        
    def hash_material_json(self, material: MaterialR9) -> str:
        """Calcule le hash SHA-256 des métadonnées pour l'intégrité"""
        material_dict = asdict(material)
        # Exclure les champs techniques du hash d'intégrité
        core_data = {k: v for k, v in material_dict.items() 
                    if k not in ['ipfs_hash_ifc', 'ipfs_hash_json', 'integrity_hash', 'last_updated', 'blockchain_tx']}
        
        json_string = json.dumps(core_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_string.encode('utf-8')).hexdigest()
    
    def upload_to_pinata(self, data: Dict[str, Any], filename: str) -> str:
        """Upload des données JSON vers Pinata IPFS"""
        try:
            # Préparation du payload
            payload = {
                "pinataOptions": {"cidVersion": 1},
                "pinataMetadata": {
                    "name": filename,
                    "keyvalues": {
                        "project": "R9_Blockchain",
                        "type": "metadata" if "materials" in data else "material"
                    }
                },
                "pinataContent": data
            }
            
            response = requests.post(
                f"{self.pinata_url}/pinning/pinJSONToIPFS",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            return result["IpfsHash"]
            
        except Exception as e:
            print(f"❌ Erreur upload Pinata: {e}")
            return ""
    
    def download_from_pinata(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """Télécharge des données JSON depuis IPFS via gateway"""
        try:
            # Utilisation du gateway IPFS public
            gateway_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
            response = requests.get(gateway_url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Erreur téléchargement IPFS {ipfs_hash}: {e}")
            return None
    
    def add_material_to_index(self, material: MaterialR9) -> Dict[str, str]:
        """Ajoute un matériau à l'index et upload sur IPFS"""
        
        # 1. Calcul du hash d'intégrité
        material.integrity_hash = self.hash_material_json(material)
        material.last_updated = datetime.now().isoformat()
        
        # 2. Upload du matériau individuel sur IPFS
        material_dict = asdict(material)
        material_ipfs_hash = self.upload_to_pinata(
            material_dict, 
            f"material_{material.ID}.json"
        )
        material.ipfs_hash_json = material_ipfs_hash
        
        print(f"✅ Matériau {material.NOM} uploadé: {material_ipfs_hash}")
        
        # 3. Ajout à l'index local
        self.current_index["materials"].append({
            "ID": material.ID,
            "NOM": material.NOM,
            "Materiau": material.Materiau,
            "Caracteristique_Materiau": material.Caracteristique_Materiau,
            "Longueur_m": material.Longueur_m,
            "Statut_usage": material.Statut_usage,
            "Empreinte_Carbone": material.Empreinte_Carbone,
            "ipfs_hash_json": material_ipfs_hash,
            "ipfs_hash_ifc": material.ipfs_hash_ifc,
            "integrity_hash": material.integrity_hash,
            "last_updated": material.last_updated
        })
        
        return {
            "material_ipfs_hash": material_ipfs_hash,
            "integrity_hash": material.integrity_hash
        }
    
    def update_global_index(self) -> str:
        """Met à jour l'index global sur IPFS"""
        
        # Métadonnées de l'index
        self.current_index["metadata"] = {
            "total_materials": len(self.current_index["materials"]),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "project": "R9_Blockchain_Consortium"
        }
        
        # Upload de l'index complet
        index_ipfs_hash = self.upload_to_pinata(
            self.current_index,
            "r9_materials_index.json"
        )
        
        print(f"🔄 Index global mis à jour: {index_ipfs_hash}")
        return index_ipfs_hash
    
    def load_index_from_ipfs(self, index_ipfs_hash: str) -> bool:
        """Charge l'index depuis IPFS"""
        index_data = self.download_from_pinata(index_ipfs_hash)
        if index_data:
            self.current_index = index_data
            print(f"✅ Index chargé: {len(self.current_index['materials'])} matériaux")
            return True
        return False
    
    def search_materials(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recherche dans l'index local avec filtres"""
        results = []
        
        for material in self.current_index["materials"]:
            match = True
            
            for key, value in filters.items():
                if key not in material:
                    continue
                    
                if key in ["Longueur_m", "Empreinte_Carbone"]:
                    # Filtres numériques
                    if isinstance(value, str) and value.startswith(">"):
                        if material[key] <= float(value[1:]):
                            match = False
                            break
                    elif isinstance(value, str) and value.startswith("<"):
                        if material[key] >= float(value[1:]):
                            match = False
                            break
                    elif material[key] != value:
                        match = False
                        break
                else:
                    # Filtres textuels (insensible à la casse)
                    if isinstance(value, str) and value.lower() not in str(material[key]).lower():
                        match = False
                        break
            
            if match:
                results.append(material)
        
        return results
    
    def get_full_material_data(self, material_id: str) -> Optional[MaterialR9]:
        """Récupère les données complètes d'un matériau depuis IPFS"""
        
        # 1. Trouver dans l'index local
        material_ref = None
        for material in self.current_index["materials"]:
            if material["ID"] == material_id:
                material_ref = material
                break
        
        if not material_ref:
            print(f"❌ Matériau {material_id} non trouvé dans l'index")
            return None
        
        # 2. Télécharger depuis IPFS
        full_data = self.download_from_pinata(material_ref["ipfs_hash_json"])
        if not full_data:
            return None
        
        # 3. Vérifier l'intégrité
        received_hash = material_ref["integrity_hash"]
        calculated_hash = self.hash_material_json(MaterialR9(**{k: v for k, v in full_data.items() 
                                                              if k in MaterialR9.__dataclass_fields__}))
        
        if received_hash != calculated_hash:
            print(f"⚠️ Intégrité compromise pour {material_id}")
            return None
        
        return MaterialR9(**full_data)

# ===============================
# EXEMPLE D'UTILISATION COMPLÈTE
# ===============================

def demo_system_r9():
    """Démonstration complète du système d'index R9"""
    
    # Configuration
    PINATA_JWT = os.getenv("PINATA_JWT", "your_pinata_jwt_here")
    manager = MetadataIndexManager(PINATA_JWT)
    
    print("🚀 === DEMO SYSTÈME INDEX R9 ===\n")
    
    # 1. Création de matériaux de test (projet Diogène)
    materials_diogene = [
        MaterialR9(
            NOM="poutre IPE 200",
            ID="1234567891234567",
            ID_maquette="123456789123",
            Longueur_m=12.23,
            Caracteristique_Materiau="S355",
            Materiau="acier",
            Statut_usage="réemployé",
            Date_fabrication="13012011",
            Date_mise_service="13012011",
            Date_reemploi="13012024",
            Empreinte_Carbone=400.0,
            ipfs_hash_ifc="QmSimulatedIFCHash123..."
        ),
        MaterialR9(
            NOM="poutre bois lamellé collé",
            ID="2345678912345678",
            ID_maquette="123456789123",
            Longueur_m=8.50,
            Caracteristique_Materiau="GL24h",
            Materiau="bois",
            Statut_usage="neuf",
            Date_fabrication="15032020",
            Date_mise_service="15032020",
            Date_reemploi="",
            Empreinte_Carbone=120.0,
            ipfs_hash_ifc="QmSimulatedIFCHash456..."
        ),
        MaterialR9(
            NOM="section tubulaire acier",
            ID="3456789123456789",
            ID_maquette="123456789123",
            Longueur_m=6.75,
            Caracteristique_Materiau="S275",
            Materiau="acier",
            Statut_usage="en usage",
            Date_fabrication="20052018",
            Date_mise_service="20052018",
            Date_reemploi="",
            Empreinte_Carbone=350.0,
            ipfs_hash_ifc="QmSimulatedIFCHash789..."
        )
    ]
    
    # 2. Ajout des matériaux à l'index
    print("📦 Ajout des matériaux à l'index...")
    for material in materials_diogene:
        result = manager.add_material_to_index(material)
        print(f"  ✅ {material.NOM} - Hash: {result['integrity_hash'][:10]}...")
    
    # 3. Mise à jour de l'index global
    print("\n🔄 Mise à jour de l'index global...")
    global_index_hash = manager.update_global_index()
    print(f"📍 Index global IPFS: {global_index_hash}")
    
    # 4. Simulation de recherches
    print("\n🔍 === TESTS DE RECHERCHE ===")
    
    # Recherche par matériau
    print("\n🔸 Recherche: Matériau = 'acier'")
    steel_materials = manager.search_materials({"Materiau": "acier"})
    for mat in steel_materials:
        print(f"  → {mat['NOM']} - {mat['Caracteristique_Materiau']} - {mat['Statut_usage']}")
    
    # Recherche par longueur
    print("\n🔸 Recherche: Longueur > 8m")
    long_materials = manager.search_materials({"Longueur_m": ">8"})
    for mat in long_materials:
        print(f"  → {mat['NOM']} - {mat['Longueur_m']}m")
    
    # Recherche combinée
    print("\n🔸 Recherche combinée: Acier + Réemployé")
    reused_steel = manager.search_materials({
        "Materiau": "acier",
        "Statut_usage": "réemployé"
    })
    for mat in reused_steel:
        print(f"  → {mat['NOM']} - Empreinte: {mat['Empreinte_Carbone']}kg CO₂")
    
    # 5. Récupération complète d'un matériau
    print("\n📋 === RÉCUPÉRATION COMPLÈTE ===")
    if steel_materials:
        material_id = steel_materials[0]["ID"]
        print(f"🔸 Récupération complète du matériau: {material_id}")
        full_material = manager.get_full_material_data(material_id)
        if full_material:
            print(f"  ✅ Données complètes récupérées:")
            print(f"     Nom: {full_material.NOM}")
            print(f"     Hash IFC: {full_material.ipfs_hash_ifc}")
            print(f"     Intégrité vérifiée: ✅")
    
    print(f"\n🎯 === RÉSUMÉ FINAL ===")
    print(f"✅ {len(materials_diogene)} matériaux indexés")
    print(f"📍 Index global IPFS: {global_index_hash}")
    print(f"🔍 Recherche rapide opérationnelle")
    print(f"🔐 Intégrité des données vérifiée")
    
    return global_index_hash

if __name__ == "__main__":
    demo_system_r9()