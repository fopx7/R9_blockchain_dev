// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title MaterialsRegistry
 * @dev Smart contract pour l'enregistrement des matériaux BIM dans le projet R9
 * Gère les 5 types d'acteurs : déposeurs, collecteurs, vérificateurs, modificateurs, stockeurs
 */
contract MaterialsRegistry is AccessControl, ReentrancyGuard {
    using Counters for Counters.Counter;

    // ====================
    // ROLES ET PERMISSIONS
    // ====================
    
    bytes32 public constant DEPOSEUR_ROLE = keccak256("DEPOSEUR_ROLE");
    bytes32 public constant COLLECTEUR_ROLE = keccak256("COLLECTEUR_ROLE");
    bytes32 public constant VERIFICATEUR_ROLE = keccak256("VERIFICATEUR_ROLE");
    bytes32 public constant MODIFICATEUR_ROLE = keccak256("MODIFICATEUR_ROLE");
    bytes32 public constant STOCKEUR_ROLE = keccak256("STOCKEUR_ROLE");

    // ====================
    // STRUCTURES DE DONNÉES
    // ====================

    /**
     * @dev Structure pour les métadonnées d'un objet BIM selon spécifications R9
     */
    struct ObjetBIM {
        // Paramètres obligatoires R9
        string nom;                          // NOM
        uint256 id;                         // ID (16 chiffres)
        uint256 idMaquette;                 // ID_maquette (12 chiffres)
        uint256 longueurMm;                 // Longueur en millimètres
        string caracteristiqueMateriau;     // Caracteristique_Materiau (ex: S355)
        string materiau;                    // Materiau (ex: acier)
        StatutUsage statutUsage;            // Statut_usage
        uint256 dateFabrication;            // Date_fabrication (timestamp)
        uint256 dateMiseEnService;          // Date_mise_en_service (timestamp)
        uint256 dateReemploi;               // Date_reemploi (timestamp, 0 si non applicable)
        uint256 empreinteCarbone;           // Empreinte_Carbone (grammes CO2)
        
        // Métadonnées techniques
        string cidIPFS;                     // CID IPFS du fichier IFC
        string cidMetadonnees;              // CID IPFS des métadonnées JSON
        address deposeur;                   // Adresse du déposeur
        uint256 timestampDepot;             // Timestamp du dépôt
        bool estActif;                      // Objet actif ou supprimé
        uint256 nombreModifications;        // Compteur de modifications
    }

    /**
     * @dev Structure pour les métadonnées d'une maquette BIM
     */
    struct MaquetteBIM {
        string nomMaquette;                 // nom_maquette
        uint256 idMaquette;                 // ID_maquette (12 chiffres)
        string nomArchitecte;               // nom_architecte
        string coordonneesGeographiques;    // coordonnees_geographiques
        string programme;                   // programme
        uint256 dateLivraison;              // date_livraison (timestamp)
        uint256 dateDepot;                  // date_depot (timestamp)
        string cidMaquetteIFC;              // CID IPFS de la maquette complète
        string cidMaquetteJSON;             // CID IPFS des métadonnées maquette
        address deposeur;                   // Adresse du déposeur
        uint256[] objetsIds;                // Liste des IDs des objets de cette maquette
        bool estActive;                     // Maquette active
    }

    /**
     * @dev Énumération pour le statut d'usage
     */
    enum StatutUsage {
        NEUF,           // 0 - neuf
        EN_USAGE,       // 1 - en usage
        REEMPLOYE       // 2 - réemployé
    }

    // ====================
    // VARIABLES D'ÉTAT
    // ====================

    Counters.Counter private _compteurObjets;
    Counters.Counter private _compteurMaquettes;

    // Mapping ID objet => ObjetBIM
    mapping(uint256 => ObjetBIM) public objets;
    
    // Mapping ID maquette => MaquetteBIM
    mapping(uint256 => MaquetteBIM) public maquettes;
    
    // Mapping pour vérifier l'existence des IDs
    mapping(uint256 => bool) public objetExiste;
    mapping(uint256 => bool) public maquetteExiste;
    
    // Mapping déposeur => liste des objets déposés
    mapping(address => uint256[]) public objetsParDeposeur;
    
    // Mapping pour les recherches par matériau
    mapping(string => uint256[]) public objetsParMateriau;
    
    // Mapping pour les recherches par maquette
    mapping(uint256 => uint256[]) public objetsParMaquette;

    // ====================
    // ÉVÉNEMENTS
    // ====================

    event ObjetDepose(
        uint256 indexed id,
        uint256 indexed idMaquette,
        address indexed deposeur,
        string nom,
        string materiau,
        string cidIPFS
    );

    event MaquetteDeposee(
        uint256 indexed idMaquette,
        address indexed deposeur,
        string nomMaquette,
        string nomArchitecte,
        string cidMaquetteIFC
    );

    event ObjetModifie(
        uint256 indexed id,
        address indexed modificateur,
        string nouveauCidIPFS,
        uint256 timestamp
    );

    event ObjetCollecte(
        uint256 indexed id,
        address indexed collecteur,
        uint256 timestamp
    );

    event RoleAttribue(
        bytes32 indexed role,
        address indexed compte,
        address indexed admin
    );

    // ====================
    // MODIFIERS
    // ====================

    modifier objetValide(uint256 _id) {
        require(objetExiste[_id], "Objet inexistant");
        require(objets[_id].estActif, "Objet inactif");
        _;
    }

    modifier maquetteValide(uint256 _idMaquette) {
        require(maquetteExiste[_idMaquette], "Maquette inexistante");
        require(maquettes[_idMaquette].estActive, "Maquette inactive");
        _;
    }

    // ====================
    // CONSTRUCTEUR
    // ====================

    constructor() {
        // Attribution du rôle admin au déployeur
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        
        // Attribution de tous les rôles au déployeur pour l'initialisation
        _grantRole(DEPOSEUR_ROLE, msg.sender);
        _grantRole(COLLECTEUR_ROLE, msg.sender);
        _grantRole(VERIFICATEUR_ROLE, msg.sender);
        _grantRole(MODIFICATEUR_ROLE, msg.sender);
        _grantRole(STOCKEUR_ROLE, msg.sender);
    }

    // ====================
    // FONCTIONS DE DÉPÔT
    // ====================

    /**
     * @dev Dépose une nouvelle maquette BIM
     */
    function deposerMaquette(
        string memory _nomMaquette,
        uint256 _idMaquette,
        string memory _nomArchitecte,
        string memory _coordonneesGeographiques,
        string memory _programme,
        uint256 _dateLivraison,
        string memory _cidMaquetteIFC,
        string memory _cidMaquetteJSON
    ) external onlyRole(DEPOSEUR_ROLE) nonReentrant {
        require(!maquetteExiste[_idMaquette], "ID maquette deja utilise");
        require(bytes(_nomMaquette).length > 0, "Nom maquette requis");
        require(bytes(_cidMaquetteIFC).length > 0, "CID maquette IFC requis");

        MaquetteBIM storage nouvelleMaquette = maquettes[_idMaquette];
        nouvelleMaquette.nomMaquette = _nomMaquette;
        nouvelleMaquette.idMaquette = _idMaquette;
        nouvelleMaquette.nomArchitecte = _nomArchitecte;
        nouvelleMaquette.coordonneesGeographiques = _coordonneesGeographiques;
        nouvelleMaquette.programme = _programme;
        nouvelleMaquette.dateLivraison = _dateLivraison;
        nouvelleMaquette.dateDepot = block.timestamp;
        nouvelleMaquette.cidMaquetteIFC = _cidMaquetteIFC;
        nouvelleMaquette.cidMaquetteJSON = _cidMaquetteJSON;
        nouvelleMaquette.deposeur = msg.sender;
        nouvelleMaquette.estActive = true;

        maquetteExiste[_idMaquette] = true;
        _compteurMaquettes.increment();

        emit MaquetteDeposee(
            _idMaquette,
            msg.sender,
            _nomMaquette,
            _nomArchitecte,
            _cidMaquetteIFC
        );
    }

    /**
     * @dev Dépose un nouvel objet BIM
     */
    function deposerObjet(
        string memory _nom,
        uint256 _id,
        uint256 _idMaquette,
        uint256 _longueurMm,
        string memory _caracteristiqueMateriau,
        string memory _materiau,
        StatutUsage _statutUsage,
        uint256 _dateFabrication,
        uint256 _dateMiseEnService,
        uint256 _dateReemploi,
        uint256 _empreinteCarbone,
        string memory _cidIPFS,
        string memory _cidMetadonnees
    ) external onlyRole(DEPOSEUR_ROLE) nonReentrant {
        require(!objetExiste[_id], "ID objet deja utilise");
        require(maquetteExiste[_idMaquette], "Maquette inexistante");
        require(bytes(_nom).length > 0, "Nom objet requis");
        require(bytes(_cidIPFS).length > 0, "CID IPFS requis");

        ObjetBIM storage nouvelObjet = objets[_id];
        nouvelObjet.nom = _nom;
        nouvelObjet.id = _id;
        nouvelObjet.idMaquette = _idMaquette;
        nouvelObjet.longueurMm = _longueurMm;
        nouvelObjet.caracteristiqueMateriau = _caracteristiqueMateriau;
        nouvelObjet.materiau = _materiau;
        nouvelObjet.statutUsage = _statutUsage;
        nouvelObjet.dateFabrication = _dateFabrication;
        nouvelObjet.dateMiseEnService = _dateMiseEnService;
        nouvelObjet.dateReemploi = _dateReemploi;
        nouvelObjet.empreinteCarbone = _empreinteCarbone;
        nouvelObjet.cidIPFS = _cidIPFS;
        nouvelObjet.cidMetadonnees = _cidMetadonnees;
        nouvelObjet.deposeur = msg.sender;
        nouvelObjet.timestampDepot = block.timestamp;
        nouvelObjet.estActif = true;
        nouvelObjet.nombreModifications = 0;

        // Mise à jour des mappings
        objetExiste[_id] = true;
        objetsParDeposeur[msg.sender].push(_id);
        objetsParMateriau[_materiau].push(_id);
        objetsParMaquette[_idMaquette].push(_id);
        maquettes[_idMaquette].objetsIds.push(_id);

        _compteurObjets.increment();

        emit ObjetDepose(_id, _idMaquette, msg.sender, _nom, _materiau, _cidIPFS);
    }

    // ====================
    // FONCTIONS DE RECHERCHE
    // ====================

    /**
     * @dev Recherche des objets par matériau
     */
    function rechercherParMateriau(string memory _materiau) 
        external 
        view 
        onlyRole(COLLECTEUR_ROLE) 
        returns (uint256[] memory) 
    {
        return objetsParMateriau[_materiau];
    }

    /**
     * @dev Recherche des objets d'une maquette
     */
    function rechercherParMaquette(uint256 _idMaquette) 
        external 
        view 
        onlyRole(COLLECTEUR_ROLE)
        returns (uint256[] memory) 
    {
        return objetsParMaquette[_idMaquette];
    }

    /**
     * @dev Collecte les informations d'un objet (avec événement de traçabilité)
     */
    function collecterObjet(uint256 _id) 
        external 
        onlyRole(COLLECTEUR_ROLE) 
        objetValide(_id) 
        returns (ObjetBIM memory) 
    {
        emit ObjetCollecte(_id, msg.sender, block.timestamp);
        return objets[_id];
    }

    // ====================
    // FONCTIONS DE MODIFICATION
    // ====================

    /**
     * @dev Modifie le CID IPFS d'un objet (pour mise à jour)
     */
    function modifierObjetCID(uint256 _id, string memory _nouveauCidIPFS) 
        external 
        onlyRole(MODIFICATEUR_ROLE) 
        objetValide(_id) 
    {
        require(bytes(_nouveauCidIPFS).length > 0, "CID requis");
        
        objets[_id].cidIPFS = _nouveauCidIPFS;
        objets[_id].nombreModifications++;

        emit ObjetModifie(_id, msg.sender, _nouveauCidIPFS, block.timestamp);
    }

    // ====================
    // FONCTIONS D'ADMINISTRATION
    // ====================

    /**
     * @dev Attribution des rôles par l'admin
     */
    function attribuerRole(bytes32 _role, address _compte) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        _grantRole(_role, _compte);
        emit RoleAttribue(_role, _compte, msg.sender);
    }

    /**
     * @dev Désactive un objet (au lieu de le supprimer)
     */
    function desactiverObjet(uint256 _id) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
        objetValide(_id) 
    {
        objets[_id].estActif = false;
    }

    // ====================
    // FONCTIONS DE CONSULTATION
    // ====================

    /**
     * @dev Retourne le nombre total d'objets
     */
    function nombreObjets() external view returns (uint256) {
        return _compteurObjets.current();
    }

    /**
     * @dev Retourne le nombre total de maquettes
     */
    function nombreMaquettes() external view returns (uint256) {
        return _compteurMaquettes.current();
    }

    /**
     * @dev Vérifie si un objet existe
     */
    function objetExistePublic(uint256 _id) external view returns (bool) {
        return objetExiste[_id];
    }

    /**
     * @dev Vérifie si une maquette existe
     */
    function maquetteExistePublic(uint256 _idMaquette) external view returns (bool) {
        return maquetteExiste[_idMaquette];
    }

    /**
     * @dev Retourne les objets déposés par un utilisateur
     */
    function mesObjets() external view returns (uint256[] memory) {
        return objetsParDeposeur[msg.sender];
    }
}