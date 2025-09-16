#!/usr/bin/env python3
"""
Script de déploiement pour MaterialsRegistrySimple
scripts/deploy_simple_registry.py
"""

from brownie import MaterialsRegistrySimple, accounts, network
import time

def deploy_simple_registry():
    """Déploie la version simplifiée du registry"""
    
    print("🚀 DÉPLOIEMENT MATERIALSREGISTRY SIMPLE")
    print("="*50)
    
    # Vérifications de base
    print(f"📡 Réseau: {network.show_active()}")
    print(f"👥 Comptes: {len(accounts)}")
    
    if len(accounts) == 0:
        print("❌ Aucun compte disponible")
        return None
    
    deployer = accounts[0]
    print(f"👤 Déployeur: {deployer.address}")
    print(f"💰 Balance: {deployer.balance() / 1e18:.4f} ETH")
    
    try:
        print(f"\n🚀 Déploiement en cours...")
        
        # Déploiement
        contract = MaterialsRegistrySimple.deploy({'from': deployer})
        
        print(f"✅ Contrat déployé!")
        print(f"📍 Adresse: {contract.address}")
        print(f"⛽ Gas utilisé: {contract.tx.gas_used:,}")
        
        # Tests basiques
        print(f"\n🔍 Tests:")
        print(f"   Owner: {contract.owner()}")
        print(f"   Objets: {contract.nombreObjets()}")
        print(f"   Maquettes: {contract.nombreMaquettes()}")
        
        # Test de dépôt d'une maquette
        print(f"\n🧪 Test maquette:")
        tx = contract.deposerMaquette(
            "Maquette Test R9",
            123456789012,
            "Test Architecte", 
            "QmTestCID123",
            {'from': deployer}
        )
        print(f"   ✅ Maquette déposée - TX: {tx.txid}")
        print(f"   📊 Maquettes: {contract.nombreMaquettes()}")
        
        # Test de dépôt d'un objet
        print(f"\n🧪 Test objet:")
        tx = contract.deposerObjet(
            "Poutre Test",
            1234567891234567,
            123456789012,
            "acier",
            "QmObjetCID456",
            "QmMetaCID789",
            {'from': deployer}
        )
        print(f"   ✅ Objet déposé - TX: {tx.txid}")
        print(f"   📊 Objets: {contract.nombreObjets()}")
        
        # Test de recherche
        print(f"\n🔍 Test recherche:")
        objets_acier = contract.rechercherParMateriau("acier")
        print(f"   🔍 Objets acier: {len(objets_acier)}")
        
        print(f"\n🎉 DÉPLOIEMENT ET TESTS RÉUSSIS!")
        print(f"🔗 Contrat prêt pour intégration R9")
        
        return contract
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Fonction principale"""
    return deploy_simple_registry()

if __name__ == "__main__":
    main()