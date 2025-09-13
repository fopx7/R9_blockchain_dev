#!/usr/bin/env python3
"""
Script de déploiement du contrat MaterialsRegistry pour le projet R9
scripts/deploy_materials_registry.py
"""

from brownie import MaterialsRegistry, accounts, network, config
from web3 import Web3
import time

def deploy_materials_registry():
    """Déploie le contrat MaterialsRegistry sur Ganache"""
    
    print("🚀 DÉPLOIEMENT MATERIALSREGISTRY R9")
    print("="*50)
    
    # Vérification du réseau
    if network.show_active() not in ['development', 'ganache-local']:
        print(f"⚠️ Réseau actuel: {network.show_active()}")
        print("💡 Recommandé: development ou ganache-local")
        return None
    
    # Sélection du compte déployeur
    deployer = accounts[0]
    print(f"👤 Compte déployeur: {deployer.address}")
    print(f"💰 Balance: {deployer.balance() / 1e18:.4f} ETH")
    
    try:
        print("\n📋 Compilation du contrat...")
        
        # Déploiement
        print("🚀 Déploiement en cours...")
        start_time = time.time()
        
        contract = MaterialsRegistry.deploy(
            {'from': deployer, 'gas_price': Web3.toWei(20, 'gwei')}
        )
        
        deploy_time = time.time() - start_time
        
        print(f"✅ Contrat déployé avec succès!")
        print(f"📍 Adresse: {contract.address}")
        print(f"⏱️  Temps de déploiement: {deploy_time:.2f}s")
        print(f"⛽ Gas utilisé: {contract.tx.gas_used:,}")
        print(f"💸 Coût: {Web3.fromWei(contract.tx.gas_used * contract.tx.gas_price, 'ether'):.6f} ETH")
        
        # Vérification du déploiement
        print(f"\n🔍 Vérification:")
        print(f"   Nombre d'objets: {contract.nombreObjets()}")
        print(f"   Nombre de maquettes: {contract.nombreMaquettes()}")
        print(f"   Admin: {contract.hasRole(contract.DEFAULT_ADMIN_ROLE(), deployer.address)}")
        
        # Configuration des rôles pour les tests
        print(f"\n⚙️ Configuration des rôles de test...")
        
        # Ajout d'autres comptes pour tester les différents rôles
        if len(accounts) >= 5:
            roles_config = [
                (contract.DEPOSEUR_ROLE(), accounts[1], "DEPOSEUR"),
                (contract.COLLECTEUR_ROLE(), accounts[2], "COLLECTEUR"), 
                (contract.VERIFICATEUR_ROLE(), accounts[3], "VERIFICATEUR"),
                (contract.MODIFICATEUR_ROLE(), accounts[4], "MODIFICATEUR")
            ]
            
            for role, account, nom in roles_config:
                tx = contract.attribuerRole(role, account.address, {'from': deployer})
                print(f"   ✅ {nom}: {account.address}")
        
        print(f"\n🎉 DÉPLOIEMENT TERMINÉ!")
        print(f"🔗 Contrat prêt pour l'intégration avec l'extracteur IFC")
        
        return contract
        
    except Exception as e:
        print(f"❌ Erreur lors du déploiement: {e}")
        return None

def test_contract_basic(contract):
    """Test basique du contrat déployé"""
    
    print("\n🧪 TESTS BASIQUES")
    print("="*30)
    
    try:
        deployer = accounts[0]
        
        # Test 1: Vérification des rôles
        print("1️⃣ Test des rôles:")
        has_admin = contract.hasRole(contract.DEFAULT_ADMIN_ROLE(), deployer.address)
        has_deposeur = contract.hasRole(contract.DEPOSEUR_ROLE(), deployer.address)
        print(f"   Admin: {'✅' if has_admin else '❌'}")
        print(f"   Déposeur: {'✅' if has_deposeur else '❌'}")
        
        # Test 2: Test d'un dépôt de maquette
        print("\n2️⃣ Test dépôt maquette:")
        tx = contract.deposerMaquette(
            "Maquette Test",           # nom_maquette
            123456789012,              # id_maquette (12 chiffres)
            "Architecte Test",         # nom_architecte
            "48.8566, 2.3522",        # coordonnees_geographiques
            "Test",                    # programme
            int(time.time()),          # date_livraison
            "QmTestMaquetteIFC123",    # cid_maquette_ifc
            "QmTestMaquetteJSON456",   # cid_maquette_json
            {'from': deployer}
        )
        
        print(f"   ✅ Maquette déposée - TX: {tx.txid}")
        print(f"   📊 Nombre de maquettes: {contract.nombreMaquettes()}")
        
        # Test 3: Test d'un dépôt d'objet
        print("\n3️⃣ Test dépôt objet:")
        tx = contract.deposerObjet(
            "Poutre IPE Test",         # nom
            1234567891234567,          # id (16 chiffres)
            123456789012,              # id_maquette
            5000,                      # longueur_mm
            "S355",                    # caracteristique_materiau
            "acier",                   # materiau
            0,                         # statut_usage (NEUF)
            int(time.time()) - 86400,  # date_fabrication (hier)
            int(time.time()),          # date_mise_en_service (aujourd'hui)
            0,                         # date_reemploi (non applicable)
            25000,                     # empreinte_carbone (grammes CO2)
            "QmTestObjetIFC789",       # cid_ipfs
            "QmTestObjetJSON012",      # cid_metadonnees
            {'from': deployer}
        )
        
        print(f"   ✅ Objet déposé - TX: {tx.txid}")
        print(f"   📊 Nombre d'objets: {contract.nombreObjets()}")
        
        # Test 4: Test de recherche
        print("\n4️⃣ Test recherche:")
        objets_acier = contract.rechercherParMateriau("acier", {'from': deployer})
        print(f"   🔍 Objets en acier trouvés: {len(objets_acier)}")
        
        print(f"\n✅ TOUS LES TESTS RÉUSSIS!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans les tests: {e}")
        return False

def main():
    """Fonction principale"""
    
    # Déploiement
    contract = deploy_materials_registry()
    
    if contract:
        # Tests basiques
        test_contract_basic(contract)
        
        # Sauvegarde de l'adresse pour l'intégration
        print(f"\n📝 INFORMATIONS POUR L'INTÉGRATION:")
        print(f"   Adresse du contrat: {contract.address}")
        print(f"   Réseau: {network.show_active()}")
        print(f"   Prêt pour l'extracteur IFC!")
        
        return contract
    else:
        print("❌ Déploiement échoué")
        return None

if __name__ == "__main__":
    main()