#!/usr/bin/env python3
"""
Script de déploiement R9 - Compatible Brownie
Placez ce fichier dans: scripts/deploy_r9_system.py
"""

from brownie import MaterialsRegistryR9, accounts, network, Wei
import json
import os
from datetime import datetime

def main():
    """Fonction principale requise par Brownie"""
    print("🚀 === DÉPLOIEMENT SYSTÈME R9 ===\n")
    
    # Configuration du compte
    deployer = accounts[0]
    print(f"👤 Déployeur: {deployer.address}")
    print(f"💰 Balance: {deployer.balance() / 1e18:.4f} ETH")
    print(f"🌐 Réseau: {network.show_active()}\n")
    
    # Vérification solde minimum
    if deployer.balance() < Wei("0.01 ether"):
        print("❌ Solde insuffisant pour le déploiement")
        return None
    
    # Déploiement du smart contract
    print("📋 Déploiement MaterialsRegistryR9...")
    
    try:
        contract = MaterialsRegistryR9.deploy(
            {'from': deployer, 'gas_limit': 3000000},
            publish_source=False
        )
        
        print(f"✅ Contrat déployé: {contract.address}")
        print(f"💸 Gas utilisé: {contract.tx.gas_used:,}")
        print(f"📝 Hash TX: {contract.tx.txid}")
        
    except Exception as e:
        print(f"❌ Erreur déploiement: {e}")
        return None
    
    # Configuration des acteurs de test
    print(f"\n👥 Configuration des acteurs...")
    
    test_actors = [
        {"address": accounts[1].address, "role": "DEPOSITOR"},
        {"address": accounts[2].address, "role": "COLLECTOR"}, 
        {"address": accounts[3].address, "role": "VERIFIER"}
    ]
    
    for actor in test_actors:
        try:
            tx = contract.authorizeActor(
                actor["address"],
                actor["role"],
                {'from': deployer, 'gas_limit': 100000}
            )
            print(f"  ✅ {actor['role']}: {actor['address'][:10]}...")
        except Exception as e:
            print(f"  ❌ Erreur {actor['role']}: {e}")
    
    # Tests de base
    print(f"\n🔧 Tests de fonctionnement...")
    
    try:
        total_materials = contract.getTotalMaterials()
        paused_status = contract.isPaused()
        owner = contract.owner()
        
        print(f"  ✅ Total matériaux: {total_materials}")
        print(f"  ✅ Statut pause: {paused_status}")
        print(f"  ✅ Propriétaire: {owner}")
        
    except Exception as e:
        print(f"  ❌ Erreur tests: {e}")
    
    # Sauvegarde informations
    deployment_info = {
        "contract_address": contract.address,
        "deployment_tx": contract.tx.txid,
        "deployer_address": deployer.address,
        "network": network.show_active(),
        "gas_used": contract.tx.gas_used,
        "deployment_time": datetime.now().isoformat(),
        "authorized_actors": test_actors
    }
    
    # Création du dossier de sauvegarde
    os.makedirs("deployments", exist_ok=True)
    filename = f"deployments/r9_deployment_{network.show_active()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"\n📄 Informations sauvegardées: {filename}")
    
    # Résumé final
    print(f"\n🎯 === RÉSUMÉ DÉPLOIEMENT ===")
    print(f"✅ Contrat: {contract.address}")
    print(f"🌐 Réseau: {network.show_active()}")
    print(f"💸 Coût estimé: {(contract.tx.gas_used * 20) / 1e9:.6f} ETH (20 gwei)")
    print(f"👥 Acteurs autorisés: {len(test_actors)}")
    print(f"📋 Prêt pour tests matériaux Diogène")
    
    # Test d'enregistrement de matériau
    demo_material_registration(contract, deployer)
    
    return contract

    def demo_material_registration(contract, deployer):
        """Démo d'enregistrement d'un matériau du projet Diogène"""
        
        print(f"\n📦 === DEMO MATÉRIAU DIOGÈNE ===")
        
        # Matériau de test du projet Diogène
        material_data = {
            "materialId": "1111111111111111",
            "name": "Poutre IPE 200 Diogène", 
            "materialType": "acier",
            "status": "réemployé",
            "length_mm": 12230,  # 12.23m
            "carbonFootprint_cg": 40000,  # 400kg
            "ipfsHashJson": "QmDiogeneTestJSON...",
            "ipfsHashIfc": "QmDiogeneTestIFC...",
            "integrityHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        }
        
        try:
            print(f"📥 Enregistrement: {material_data['name']}")
            
            tx = contract.registerMaterial(
                material_data["materialId"],
                material_data["name"],
                material_data["materialType"],
                material_data["status"],
                material_data["length_mm"],
                material_data["carbonFootprint_cg"],
                material_data["ipfsHashJson"],
                material_data["ipfsHashIfc"],
                bytes.fromhex(material_data["integrityHash"][2:]),
                {'from': deployer, 'gas_limit': 500000}
            )
            
            print(f"  ✅ Matériau enregistré - TX: {tx.txid[:10]}...")
            print(f"  💸 Gas: {tx.gas_used:,}")
            
            # Vérification
            stored_material = contract.getMaterial(material_data["materialId"])
            print(f"  🔍 Vérification: {stored_material[1]} - {stored_material[2]}")
            
            # Test de recherche
            steel_materials = contract.getMaterialsByType("acier")
            print(f"  🔍 Matériaux acier trouvés: {len(steel_materials)}")
            
            print(f"  ✅ Test matériau Diogène réussi !")
            
        except Exception as e:
            print(f"  ❌ Erreur enregistrement matériau: {e}")

# Point d'entrée pour exécution directe
if __name__ == "__main__":
    main()