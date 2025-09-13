#!/usr/bin/env python3
"""
Test Ganache corrigé pour les nouvelles versions de Web3.py
scripts/test_ganache_fixed.py
"""

from brownie import network, accounts, web3, config
from web3 import Web3

def test_ganache_complet():
    """Test complet de Ganache avec syntaxe corrigée"""
    print("🚀 TEST GANACHE R9 - VERSION CORRIGÉE")
    print("="*50)
    
    try:
        # 1. Test de configuration
        print("📋 CONFIGURATION:")
        print(f"   Réseau actif: {network.show_active()}")
        print(f"   URL: {config['networks']['development']['host']}")
        print(f"   Chain ID configuré: {config['networks']['development']['chainid']}")
        
        # 2. Test de connexion
        print(f"\n🔗 CONNEXION:")
        if web3.isConnected():
            print("   ✅ Web3 connecté")
            print(f"   Chain ID réel: {web3.eth.chain_id}")
            print(f"   Dernier bloc: {web3.eth.block_number}")
        else:
            print("   ❌ Web3 non connecté")
            return False
        
        # 3. Test des comptes - SYNTAXE CORRIGÉE
        print(f"\n👥 COMPTES:")
        print(f"   Comptes disponibles: {len(accounts)}")
        
        if len(accounts) > 0:
            for i in range(min(3, len(accounts))):  # Affiche les 3 premiers
                account = accounts[i]
                
                # Méthode 1: Brownie native (plus simple)
                balance_eth_simple = account.balance() / 1e18
                
                # Méthode 2: Web3.py (plus précise)
                balance_wei = account.balance()
                balance_eth_precise = Web3.fromWei(balance_wei, 'ether')
                
                print(f"   🔑 Compte {i}:")
                print(f"      Adresse: {account.address}")
                print(f"      Balance: {balance_eth_simple:.4f} ETH")
                print(f"      Clé privée: {account.private_key[:10]}...")
        
        # 4. Test de transaction simple
        print(f"\n🧪 TEST TRANSACTION:")
        if len(accounts) >= 2:
            sender = accounts[0]
            receiver = accounts[1]
            
            # Balance avant
            balance_avant = sender.balance() / 1e18
            print(f"   Balance avant: {balance_avant:.4f} ETH")
            
            # Transaction de test (0.1 ETH)
            montant_wei = Web3.toWei(0.1, 'ether')
            tx = sender.transfer(receiver, montant_wei)
            
            print(f"   📤 Transaction:")
            print(f"      Hash: {tx.txid}")
            print(f"      Gas utilisé: {tx.gas_used:,}")
            
            # Balance après
            balance_apres = sender.balance() / 1e18
            print(f"   Balance après: {balance_apres:.4f} ETH")
            
            # Vérification
            difference = balance_avant - balance_apres
            if 0.099 < difference < 0.101:  # ~0.1 ETH + gas
                print("   ✅ Transaction réussie!")
            else:
                print(f"   ⚠️ Différence inattendue: {difference:.4f} ETH")
        
        print(f"\n🎉 GANACHE OPÉRATIONNEL POUR R9!")
        print("✅ Prêt pour le déploiement de smart contracts")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def info_ganache_rapide():
    """Informations rapides sur Ganache"""
    try:
        print("📊 INFO GANACHE")
        print("-" * 25)
        print(f"Réseau: {network.show_active()}")
        print(f"Connecté: {'✅' if web3.isConnected() else '❌'}")
        print(f"Comptes: {len(accounts)}")
        
        if len(accounts) > 0:
            balance_eth = accounts[0].balance() / 1e18
            print(f"Balance compte 0: {balance_eth:.2f} ETH")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    test_ganache_complet()

if __name__ == "__main__":
    main()