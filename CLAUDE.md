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
├── contracts/          # Solidity smart contracts (currently empty)
├── scripts/            # Deployment and interaction scripts (currently empty)
├── tests/             # Test files (currently empty)
├── interfaces/        # Contract interfaces
├── build/             # Compiled contracts and deployments
├── data/              # Project data files
│   ├── ifc-files/     # IFC (Industry Foundation Classes) files
│   └── processed/     # Processed data
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

### Network Configuration
- **development**: Local Ganache on http://127.0.0.1:7545
- **ganache-local**: Local Ganache on http://127.0.0.1:8545

## Environment Variables

The `.env` file should contain:
- `PINATA_API_KEY` and `PINATA_SECRET_KEY` for IPFS storage
- `WEB3_INFURA_PROJECT_ID` for Ethereum network access
- `PRIVATE_KEY` for contract deployment (test networks only)

## Architecture Notes

This project appears to be focused on materials tracking with blockchain integration, possibly involving IFC files for construction/engineering data. The `data/` directory structure suggests processing of IFC files, which are commonly used in Building Information Modeling (BIM).

The project is currently in early setup phase with empty contract, script, and test directories but proper Brownie framework configuration in place.