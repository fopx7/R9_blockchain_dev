// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title MaterialsRegistrySimple
 * @dev Version simplifiée du registry pour éviter "Stack too deep"
 * Fonctionnalités essentielles pour le projet R9
 */
contract MaterialsRegistrySimple {

    // ====================
    // STRUCTURES SIMPLIFIÉES
    // ====================

    struct ObjetBIM {
        string nom;
        uint256 id;
        uint256 idMaquette;
        string materiau;
        string cidIPFS;
        string cidMetadonnees;
        address deposeur;
        uint256 timestampDepot;
        bool estActif;
    }

    struct MaquetteBIM {
        string nomMaquette;
        uint256 idMaquette;
        string nomArchitecte;
        string cidMaquetteIFC;
        address deposeur;
        bool estActive;
    }

    // ====================
    // VARIABLES D'ÉTAT
    // ====================

    address public owner;
    uint256 public nombreObjetsTotal;
    uint256 public nombreMaquettesTotal;

    // Mappings principaux
    mapping(uint256 => ObjetBIM) public objets;
    mapping(uint256 => MaquetteBIM) public maquettes;
    mapping(uint256 => bool) public objetExiste;
    mapping(uint256 => bool) public maquetteExiste;
    
    // Mappings pour recherches
    mapping(string => uint256[]) public objetsParMateriau;
    mapping(address => uint256[]) public objetsParDeposeur;

    // ====================
    // ÉVÉNEMENTS
    // ====================

    event ObjetDepose(
        uint256 indexed id,
        string nom,
        string materiau,
        address deposeur
    );

    event MaquetteDeposee(
        uint256 indexed idMaquette,
        string nomMaquette,
        address deposeur
    );

    event ObjetCollecte(
        uint256 indexed id,
        address collecteur
    );

    // ====================
    // MODIFIERS
    // ====================

    modifier onlyOwner() {
        require(msg.sender == owner, "Seul le proprietaire");
        _;
    }

    modifier objetValide(uint256 _id) {
        require(objetExiste[_id], "Objet inexistant");
        require(objets[_id].estActif, "Objet inactif");
        _;
    }

    // ====================
    // CONSTRUCTEUR
    // ====================

    constructor() {
        owner = msg.sender;
        nombreObjetsTotal = 0;
        nombreMaquettesTotal = 0;
    }

    // ====================
    // FONCTIONS DE DÉPÔT
    // ====================

    function deposerMaquette(
        string memory _nomMaquette,
        uint256 _idMaquette,
        string memory _nomArchitecte,
        string memory _cidMaquetteIFC
    ) external {
        require(!maquetteExiste[_idMaquette], "ID maquette existe");
        require(bytes(_nomMaquette).length > 0, "Nom requis");

        maquettes[_idMaquette] = MaquetteBIM({
            nomMaquette: _nomMaquette,
            idMaquette: _idMaquette,
            nomArchitecte: _nomArchitecte,
            cidMaquetteIFC: _cidMaquetteIFC,
            deposeur: msg.sender,
            estActive: true
        });

        maquetteExiste[_idMaquette] = true;
        nombreMaquettesTotal++;

        emit MaquetteDeposee(_idMaquette, _nomMaquette, msg.sender);
    }

    function deposerObjet(
        string memory _nom,
        uint256 _id,
        uint256 _idMaquette,
        string memory _materiau,
        string memory _cidIPFS,
        string memory _cidMetadonnees
    ) external {
        require(!objetExiste[_id], "ID objet existe");
        require(maquetteExiste[_idMaquette], "Maquette inexistante");
        require(bytes(_nom).length > 0, "Nom requis");

        objets[_id] = ObjetBIM({
            nom: _nom,
            id: _id,
            idMaquette: _idMaquette,
            materiau: _materiau,
            cidIPFS: _cidIPFS,
            cidMetadonnees: _cidMetadonnees,
            deposeur: msg.sender,
            timestampDepot: block.timestamp,
            estActif: true
        });

        objetExiste[_id] = true;
        objetsParMateriau[_materiau].push(_id);
        objetsParDeposeur[msg.sender].push(_id);
        nombreObjetsTotal++;

        emit ObjetDepose(_id, _nom, _materiau, msg.sender);
    }

    // ====================
    // FONCTIONS DE RECHERCHE
    // ====================

    function rechercherParMateriau(string memory _materiau) 
        external 
        view 
        returns (uint256[] memory) 
    {
        return objetsParMateriau[_materiau];
    }

    function collecterObjet(uint256 _id) 
        external 
        objetValide(_id) 
        returns (ObjetBIM memory) 
    {
        emit ObjetCollecte(_id, msg.sender);
        return objets[_id];
    }

    function mesObjets() external view returns (uint256[] memory) {
        return objetsParDeposeur[msg.sender];
    }

    // ====================
    // FONCTIONS D'ADMINISTRATION
    // ====================

    function desactiverObjet(uint256 _id) external onlyOwner objetValide(_id) {
        objets[_id].estActif = false;
    }

    function nombreObjets() external view returns (uint256) {
        return nombreObjetsTotal;
    }

    function nombreMaquettes() external view returns (uint256) {
        return nombreMaquettesTotal;
    }
}