# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Brownie-based Ethereum development project focused on blockchain materials tracking. The project uses:
- **Framework**: Brownie v1.21.0 (Python development framework for Ethereum)
- **Solidity**: v0.8.19
- **Dependencies**: OpenZeppelin contracts v4.8.0
- **Networks**: Local development on Ganache (ports 7545/8545)

## Project Structure

```
├── contracts/          # Solidity smart contracts
│   ├── MaterialsRegistry.sol    # Main BIM materials tracking contract
│   └── SimpleTest.sol          # Test contract
├── scripts/            # Deployment and interaction scripts
│   ├── deploy_materials_registry.py  # Deploy MaterialsRegistry contract
│   ├── ifc_r9_extractor.py          # IFC file processing and extraction
│   ├── pinata_uploader.py            # IPFS/Pinata integration
│   └── setup_ganache.py              # Ganache configuration
├── tests/             # Test files (empty - tests defined in deployment script)
├── interfaces/        # Contract interfaces
├── build/             # Compiled contracts and deployments
├── data/              # Project data files
│   ├── ifc-files/     # IFC (Industry Foundation Classes) input files
│   └── processed/     # Processed IFC data for blockchain
├── reports/           # Test coverage and analysis reports
├── brownie-config.yaml # Brownie configuration
└── .env               # Environment variables (Pinata, Infura keys)
```

## Development Commands

### Core Brownie Commands
- `brownie compile` - Compile all contracts in the contracts/ folder
- `brownie test` - Run all tests in the tests/ folder
- `brownie run <script>` - Execute a script from the scripts/ folder
- `brownie console` - Open interactive console with deployed contracts
- `brownie accounts` - Manage local accounts for development
- `brownie networks` - Manage network configurations

### Specific Project Commands
- `brownie run deploy_materials_registry` - Deploy the MaterialsRegistry smart contract with role setup
- `python scripts/ifc_r9_extractor.py` - Extract and validate BIM objects from IFC files
- `python scripts/pinata_uploader.py` - Upload processed files to IPFS via Pinata

### Network Configuration
- **development**: Local Ganache on http://127.0.0.1:7545 (default)
- **ganache-local**: Local Ganache on http://127.0.0.1:8545 
- **development-fork**: Auto-launched Ganache for testing

## Environment Variables

The `.env` file should contain:
- `PINATA_API_KEY` and `PINATA_SECRET_KEY` for IPFS storage
- `WEB3_INFURA_PROJECT_ID` for Ethereum network access
- `PRIVATE_KEY` for contract deployment (test networks only)

## Architecture Overview

This project implements a complete BIM (Building Information Modeling) materials tracking system on the blockchain for the R9 project. Key architectural components:

### Smart Contract Layer (contracts/MaterialsRegistry.sol)
- **Role-based access control** with 5 actor types: déposeurs, collecteurs, vérificateurs, modificateurs, stockeurs
- **Materials Registry** managing BIM objects with 11 mandatory parameters per R9 specifications
- **Maquette tracking** with 7 mandatory metadata fields per architectural model
- **IPFS integration** for storing IFC files and metadata off-chain

### Data Processing Pipeline (scripts/ifc_r9_extractor.py)
- **IFC file parsing** using ifcopenshell library
- **Strict validation** of all 11 R9 parameters: NOM, ID (16 digits), ID_maquette (12 digits), Longueur_m, Caracteristique_Materiau, Materiau, Statut_usage, Date_fabrication, Date_mise_en_service, Date_reemploi, Empreinte_Carbone
- **Individual object extraction** creating separate IFC files for each BIM object
- **JSON metadata generation** for blockchain integration

### Deployment & Testing
- **Role assignment** during deployment to test accounts
- **Built-in testing** within deployment script (scripts/deploy_materials_registry.py)
- **Interactive metadata input** for maquette information during IFC processing

### Dependencies & Requirements
- **ifcopenshell**: For IFC file processing
- **Python 3.8+**: Runtime environment
- **Ganache**: Local blockchain development
- **Pinata**: IPFS storage provider