#!/usr/bin/env python3
"""
Script de test simple pour vérifier que Brownie fonctionne
scripts/deploy_simple_test.py
"""

from brownie import SimpleTest, accounts, network

def deploy_simple_test():
    """Déploie un contrat de test simple"""
    
    print("🧪 TEST DE DÉPLOIEMENT SIMPLE")
    print("="*40)
    
    # Vérification du réseau
    print(f"📡 Réseau: {network.show_active()}")
    print(f"👥 Comptes: {len(accounts)}")
    
    if len(accounts) == 0:
        print("❌ Aucun compte disponible")
        return None
    
    # Compte déployeur
    deployer = accounts[0]
    print(f"👤 Déployeur: {deployer.address}")
    print(f"💰 Balance: {deployer.balance() / 1e18:.4f} ETH")
    
    try:
        print("\n🚀 Déploiement...")
        
        # Déploiement du contrat simple
        contract = SimpleTest.deploy({'from': deployer})
        
        print(f"✅ Contrat déployé!")
        print(f"📍 Adresse: {contract.address}")
        print(f"⛽ Gas: {contract.tx.gas_used:,}")
        
        # Test du contrat
        print(f"\n🔍 Test du contrat:")
        print(f"   Counter initial: {contract.getCounter()}")
        print(f"   Owner: {contract.getOwner()}")
        
        # Test d'une transaction
        tx = contract.increment({'from': deployer})
        print(f"   ✅ Increment TX: {tx.txid}")
        print(f"   Counter après: {contract.getCounter()}")
        
        print(f"\n🎉 TEST RÉUSSI!")
        return contract
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Fonction principale"""
    contract = deploy_simple_test()
    return contract

if __name__ == "__main__":
    main()