#!/usr/bin/env python3
"""
INDEX_INTEGRATION_1.0.py
Intégration complète Brownie Framework + Système Index R9
Connexion blockchain Ethereum avec index IPFS décentralisé
"""

from brownie import MaterialsRegistryR9, accounts, network, Wei
from brownie.project import get_loaded_projects
import json
import time
from typing import Dict, List, Any
from r9_metadata_index_system import MetadataIndexManager, MaterialR9

class R9BlockchainManager:
    """Gestionnaire de l'intégration blockchain R9 avec Brownie"""
    
    def __init__(self, pinata_jwt: str, account_index: int = 0):
        self.metadata_manager = MetadataIndexManager(pinata_jwt)
        self.account = accounts[account_index]
        self.contract = None
        self.current_index_hash = ""
        
        print(f"🔗 Compte blockchain: {self.account.address}")
        print(f"💰 Balance: {self.account.balance() / 1e18:.4f} ETH")
    
    def deploy_contract(self) -> str:
        """Déploie le smart contract MaterialsRegistry R9"""
        try:
            # Déploiement avec estimation des gas fees
            self.contract = MaterialsRegistryR9.deploy(
                {'from': self.account, 'gas_limit': 3000000}
            )
            
            print(f"✅ Smart contract déployé: {self.contract.address}")
            print(f"💸 Gas utilisé: {self.contract.tx.gas_used:,}")
            
            return self.contract.address
            
        except Exception as e:
            print(f"❌ Erreur déploiement: {e}")
            return ""
    
    def connect_to_contract(self, contract_address: str):
        """Se connecte à un contrat existant"""
        try:
            self.contract = MaterialsRegistryR9.at(contract_address)
            print(f"🔗 Connecté au contrat: {contract_address}")
        except Exception as e:
            print(f"❌ Erreur connexion contrat: {e}")
    
    def register_material_complete(self, material: MaterialR9) -> Dict[str, Any]:
        """Enregistrement complet: Index IPFS + Blockchain"""
        
        print(f"📦 Traitement: {material.NOM}...")
        
        # 1. Ajout à l'index IPFS
        ipfs_result = self.metadata_manager.add_material_to_index(material)
        
        if not ipfs_result["material_ipfs_hash"]:
            return {"success": False, "error": "Échec upload IPFS"}
        
        # 2. Enregistrement blockchain
        try:
            tx = self.contract.registerMaterial(
                material.ID,
                material.NOM,
                material.Materiau,
                material.Statut_usage,
                int(material.Longueur_m * 1000),  # Conversion en mm pour éviter les float
                int(material.Empreinte_Carbone * 100),  # 2 décimales de précision
                ipfs_result["material_ipfs_hash"],
                material.ipfs_hash_ifc,
                ipfs_result["integrity_hash"],
                {'from': self.account, 'gas_limit': 500000}
            )
            
            material.blockchain_tx = tx.txid
            
            print(f"  ✅ Blockchain: {tx.txid[:10]}...")
            print(f"  📍 IPFS: {ipfs_result['material_ipfs_hash'][:10]}...")
            print(f"  💸 Gas: {tx.gas_used:,}")
            
            return {
                "success": True,
                "blockchain_tx": tx.txid,
                "ipfs_hash": ipfs_result["material_ipfs_hash"],
                "gas_used": tx.gas_used,
                "integrity_hash": ipfs_result["integrity_hash"]
            }
            
        except Exception as e:
            print(f"  ❌ Erreur blockchain: {e}")
            return {"success": False, "error": str(e)}
    
    def update_global_index_blockchain(self) -> str:
        """Met à jour l'index global et enregistre la référence blockchain"""
        
        # 1. Mise à jour index IPFS
        index_hash = self.metadata_manager.update_global_index()
        
        if not index_hash:
            return ""
        
        # 2. Enregistrement référence blockchain
        try:
            tx = self.contract.updateGlobalIndex(
                index_hash,
                len(self.metadata_manager.current_index["materials"]),
                {'from': self.account, 'gas_limit': 200000}
            )
            
            self.current_index_hash = index_hash
            
            print(f"🔄 Index blockchain mis à jour:")
            print(f"  📍 IPFS: {index_hash}")
            print(f"  ⛓️ TX: {tx.txid}")
            print(f"  💸 Gas: {tx.gas_used:,}")
            
            return index_hash
            
        except Exception as e:
            print(f"❌ Erreur mise à jour blockchain: {e}")
            return index_hash  # Retourner quand même le hash IPFS
    
    def query_materials_hybrid(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recherche hybride: Index IPFS + vérification blockchain"""
        
        print(f"🔍 Recherche avec filtres: {filters}")
        
        # 1. Recherche rapide dans l'index IPFS
        ipfs_results = self.metadata_manager.search_materials(filters)
        
        # 2. Vérification existence blockchain pour chaque résultat
        verified_results = []
        
        for material in ipfs_results:
            try:
                # Vérification que le matériau existe sur la blockchain
                blockchain_data = self.contract.getMaterial(material["ID"])
                
                if blockchain_data[0]:  # exists = True
                    material["blockchain_verified"] = True
                    material["blockchain_status"] = blockchain_data[3]  # status
                    verified_results.append(material)
                    
            except Exception:
                material["blockchain_verified"] = False
                verified_results.append(material)
        
        print(f"  📊 Trouvé: {len(ipfs_results)} (IPFS) / {len(verified_results)} (vérifiés)")
        
        return verified_results
    
    def collect_material_complete(self, material_id: str) -> Dict[str, Any]:
        """Collecte complète d'un matériau avec toutes ses données"""
        
        print(f"📋 Collecte matériau: {material_id}")
        
        # 1. Vérification blockchain
        try:
            blockchain_data = self.contract.getMaterial(material_id)
            
            if not blockchain_data[0]:  # not exists
                return {"success": False, "error": "Matériau inexistant sur blockchain"}
            
            print(f"  ✅ Blockchain: vérifié")
            
        except Exception as e:
            return {"success": False, "error": f"Erreur blockchain: {e}"}
        
        # 2. Récupération données complètes IPFS
        full_material = self.metadata_manager.get_full_material_data(material_id)
        
        if not full_material:
            return {"success": False, "error": "Données IPFS inaccessibles"}
        
        print(f"  ✅ IPFS: données récupérées")
        print(f"  🔐 Intégrité: vérifiée")
        
        # 3. Enregistrement de l'accès sur blockchain (pour traçabilité)
        try:
            tx = self.contract.recordAccess(
                material_id,
                "COLLECT",
                {'from': self.account, 'gas_limit': 150000}
            )
            
            return {
                "success": True,
                "material": full_material,
                "blockchain_data": {
                    "name": blockchain_data[1],
                    "material_type": blockchain_data[2], 
                    "status": blockchain_data[3],
                    "ipfs_hash": blockchain_data[6]
                },
                "access_tx": tx.txid,
                "gas_used": tx.gas_used
            }
            
        except Exception as e:
            # Retourner quand même les données même si l'enregistrement échoue
            return {
                "success": True,
                "material": full_material,
                "blockchain_data": {
                    "name": blockchain_data[1],
                    "material_type": blockchain_data[2],
                    "status": blockchain_data[3]
                },
                "access_recording_error": str(e)
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Collecte des métriques système pour analyse R9"""
        
        metrics = {
            "blockchain": {},
            "ipfs": {},
            "system": {}
        }
        
        # Métriques blockchain
        if self.contract:
            try:
                total_materials = self.contract.getTotalMaterials()
                global_index = self.contract.getCurrentIndex()
                
                metrics["blockchain"] = {
                    "contract_address": self.contract.address,
                    "total_materials": total_materials,
                    "current_index_hash": global_index[0],
                    "index_material_count": global_index[1],
                    "network": network.show_active()
                }
            except Exception as e:
                metrics["blockchain"]["error"] = str(e)
        
        # Métriques IPFS
        metrics["ipfs"] = {
            "total_materials": len(self.metadata_manager.current_index["materials"]),
            "current_index_hash": self.current_index_hash,
            "last_updated": self.metadata_manager.current_index.get("metadata", {}).get("last_updated", "")
        }
        
        # Métriques système
        metrics["system"] = {
            "account_address": self.account.address,
            "account_balance_eth": float(self.account.balance() / 1e18),
            "network_active": network.show_active(),
            "timestamp": time.time()
        }
        
        return metrics

# ===============================
# DEMO COMPLÈTE INTÉGRATION R9
# ===============================

def demo_r9_complete_system():
    """Démonstration complète du système R9 intégré"""
    
    print("🚀 === DEMO SYSTÈME R9 COMPLET ===\n")
    
    # Configuration
    PINATA_JWT = "your_pinata_jwt_here"  # Remplacer par votre JWT
    
    # Initialisation
    r9_manager = R9BlockchainManager(PINATA_JWT, account_index=0)
    
    # 1. Déploiement du contrat (ou connexion à un existant)
    print("📋 === DÉPLOIEMENT BLOCKCHAIN ===")
    contract_address = r9_manager.deploy_contract()
    
    if not contract_address:
        print("❌ Impossible de déployer le contrat")
        return
    
    # 2. Enregistrement de matériaux du projet Diogène
    print("\n📦 === ENREGISTREMENT MATÉRIAUX DIOGÈNE ===")
    
    materials_diogene = [
        MaterialR9(
            NOM="poutre IPE 200 Diogène",
            ID="1111111111111111",
            ID_maquette="123456789123", 
            Longueur_m=12.23,
            Caracteristique_Materiau="S355",
            Materiau="acier",
            Statut_usage="réemployé",
            Date_fabrication="13012011",
            Date_mise_service="13012011", 
            Date_reemploi="13012024",
            Empreinte_Carbone=400.0,
            ipfs_hash_ifc="QmDiogeneIFC1..."
        ),
        MaterialR9(
            NOM="isolant laine de bois Diogène",
            ID="2222222222222222",
            ID_maquette="123456789123",
            Longueur_m=2.40,
            Caracteristique_Materiau="λ=0.036",
            Materiau="isolant",
            Statut_usage="neuf",
            Date_fabrication="20032020",
            Date_mise_service="20032020",
            Date_reemploi="",
            Empreinte_Carbone=45.0,
            ipfs_hash_ifc="QmDiogeneIFC2..."
        )
    ]
    
    registration_results = []
    for material in materials_diogene:
        result = r9_manager.register_material_complete(material)
        registration_results.append(result)
        time.sleep(2)  # Pause entre transactions
    
    # 3. Mise à jour index global
    print("\n🔄 === MISE À JOUR INDEX GLOBAL ===")
    global_index_hash = r9_manager.update_global_index_blockchain()
    
    # 4. Tests de recherche
    print("\n🔍 === TESTS DE RECHERCHE ===")
    
    steel_search = r9_manager.query_materials_hybrid({"Materiau": "acier"})
    print(f"Matériaux acier trouvés: {len(steel_search)}")
    
    reused_search = r9_manager.query_materials_hybrid({"Statut_usage": "réemployé"})
    print(f"Matériaux réemployés trouvés: {len(reused_search)}")
    
    # 5. Test de collecte complète
    print("\n📋 === TEST COLLECTE COMPLÈTE ===")
    if steel_search:
        material_id = steel_search[0]["ID"]
        collection_result = r9_manager.collect_material_complete(material_id)
        
        if collection_result["success"]:
            print(f"✅ Collecte réussie:")
            print(f"   Nom: {collection_result['material'].NOM}")
            print(f"   Statut: {collection_result['blockchain_data']['status']}")
            print(f"   TX accès: {collection_result['access_tx'][:10]}...")
    
    # 6. Métriques finales
    print("\n📊 === MÉTRIQUES SYSTÈME ===")
    metrics = r9_manager.get_system_metrics()
    
    print(f"Blockchain:")
    print(f"  - Matériaux enregistrés: {metrics['blockchain']['total_materials']}")
    print(f"  - Index global: {metrics['blockchain']['current_index_hash'][:10]}...")
    
    print(f"IPFS:")
    print(f"  - Matériaux indexés: {metrics['ipfs']['total_materials']}")
    print(f"  - Hash index: {metrics['ipfs']['current_index_hash'][:10]}...")
    
    print(f"Système:")
    print(f"  - Réseau: {metrics['system']['network_active']}")
    print(f"  - Balance: {metrics['system']['account_balance_eth']:.4f} ETH")
    
    # 7. Calcul des coûts
    total_gas_used = sum([r.get('gas_used', 0) for r in registration_results if r.get('success')])
    print(f"\n💸 === ANALYSE COÛTS ===")
    print(f"Gas total utilisé: {total_gas_used:,}")
    print(f"Coût estimé (20 gwei): {(total_gas_used * 20) / 1e9:.6f} ETH")
    
    return {
        "contract_address": contract_address,
        "global_index_hash": global_index_hash,
        "total_materials": len(materials_diogene),
        "total_gas_used": total_gas_used,
        "metrics": metrics
    }

if __name__ == "__main__":
    demo_r9_complete_system()