// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Materials_Registry_2.0
 * @dev Smart Contract pour l'enregistrement des matériaux BIM 
 * @author Leopold Malkit Singh 
 * 
 * Architecture hybride blockchain + IPFS selon l'Approche 1:
 * - Blockchain: Métadonnées essentielles + références IPFS + traçabilité
 * - IPFS: Données complètes JSON + fichiers IFC + index décentralisé
 */

contract MaterialsRegistryR9 {
    
    // ===============================
    // STRUCTURES DE DONNÉES
    // ===============================
    
    struct Material {
        bool exists;                    // Existence du matériau
        string name;                    // Nom du matériau
        string materialType;            // Type de matériau (acier, bois, etc.)
        string status;                  // Statut (neuf, en usage, réemployé)
        uint256 length_mm;              // Longueur en millimètres
        uint256 carbonFootprint_cg;     // Empreinte carbone en centigrammes
        string ipfsHashJson;            // Hash IPFS des métadonnées JSON
        string ipfsHashIfc;             // Hash IPFS du fichier IFC
        bytes32 integrityHash;          // Hash SHA-256 d'intégrité des données
        address depositor;              // Adresse du déposeur
        uint256 timestamp;              // Timestamp d'enregistrement
        uint256 accessCount;            // Nombre d'accès au matériau
    }
    
    struct GlobalIndex {
        string ipfsHash;                // Hash IPFS de l'index global
        uint256 materialCount;          // Nombre total de matériaux
        uint256 lastUpdated;            // Timestamp dernière mise à jour
    }
    
    struct AccessLog {
        string materialId;              // ID du matériau accédé
        address accessor;               // Adresse de l'accesseur
        string accessType;              // Type d'accès (COLLECT, MODIFY, VIEW)
        uint256 timestamp;              // Timestamp de l'accès
    }
    
    // ===============================
    // VARIABLES D'ÉTAT
    // ===============================
    
    mapping(string => Material) public materials;
    mapping(address => bool) public authorizedActors;
    mapping(address => string) public actorRoles; // DEPOSITOR, COLLECTOR, VERIFIER, etc.
    
    string[] public materialIds;
    GlobalIndex public currentIndex;
    AccessLog[] public accessHistory;
    
    address public owner;
    uint256 public totalMaterials;
    bool public paused;
    
    // ===============================
    // ÉVÉNEMENTS
    // ===============================
    
    event MaterialRegistered(
        string indexed materialId,
        string name,
        string materialType,
        address indexed depositor,
        string ipfsHashJson
    );
    
    event MaterialAccessed(
        string indexed materialId,
        address indexed accessor,
        string accessType,
        uint256 timestamp
    );
    
    event GlobalIndexUpdated(
        string indexed ipfsHash,
        uint256 materialCount,
        uint256 timestamp
    );
    
    event ActorAuthorized(
        address indexed actor,
        string role,
        uint256 timestamp
    );
    
    event MaterialStatusUpdated(
        string indexed materialId,
        string newStatus,
        address indexed updater
    );
    
    // ===============================
    // MODIFICATEURS
    // ===============================
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Seul le propriétaire peut effectuer cette action");
        _;
    }
    
    modifier onlyAuthorized() {
        require(authorizedActors[msg.sender], "Acteur non autorisé");
        _;
    }
    
    modifier notPaused() {
        require(!paused, "Contrat en pause");
        _;
    }
    
    modifier materialExists(string memory _materialId) {
        require(materials[_materialId].exists, "Matériau inexistant");
        _;
    }
    
    // ===============================
    // CONSTRUCTEUR
    // ===============================
    
    constructor() {
        owner = msg.sender;
        authorizedActors[msg.sender] = true;
        actorRoles[msg.sender] = "OWNER";
        paused = false;
        totalMaterials = 0;
        
        emit ActorAuthorized(msg.sender, "OWNER", block.timestamp);
    }
    
    // ===============================
    // FONCTIONS DE GESTION DES ACTEURS
    // ===============================
    
    function authorizeActor(address _actor, string memory _role) 
        public 
        onlyOwner 
    {
        authorizedActors[_actor] = true;
        actorRoles[_actor] = _role;
        
        emit ActorAuthorized(_actor, _role, block.timestamp);
    }
    
    function revokeActor(address _actor) 
        public 
        onlyOwner 
    {
        authorizedActors[_actor] = false;
        delete actorRoles[_actor];
    }
    
    function getActorRole(address _actor) 
        public 
        view 
        returns (string memory) 
    {
        return actorRoles[_actor];
    }
    
    // ===============================
    // FONCTIONS D'ENREGISTREMENT
    // ===============================
    
    function registerMaterial(
        string memory _materialId,
        string memory _name,
        string memory _materialType,
        string memory _status,
        uint256 _length_mm,
        uint256 _carbonFootprint_cg,
        string memory _ipfsHashJson,
        string memory _ipfsHashIfc,
        bytes32 _integrityHash
    ) 
        public 
        onlyAuthorized 
        notPaused 
    {
        require(!materials[_materialId].exists, "Matériau déjà enregistré");
        require(bytes(_materialId).length > 0, "ID matériau requis");
        require(bytes(_name).length > 0, "Nom matériau requis");
        require(bytes(_ipfsHashJson).length > 0, "Hash IPFS JSON requis");
        
        materials[_materialId] = Material({
            exists: true,
            name: _name,
            materialType: _materialType,
            status: _status,
            length_mm: _length_mm,
            carbonFootprint_cg: _carbonFootprint_cg,
            ipfsHashJson: _ipfsHashJson,
            ipfsHashIfc: _ipfsHashIfc,
            integrityHash: _integrityHash,
            depositor: msg.sender,
            timestamp: block.timestamp,
            accessCount: 0
        });
        
        materialIds.push(_materialId);
        totalMaterials++;
        
        emit MaterialRegistered(
            _materialId,
            _name,
            _materialType,
            msg.sender,
            _ipfsHashJson
        );
    }
    
    function updateMaterialStatus(
        string memory _materialId, 
        string memory _newStatus
    ) 
        public 
        onlyAuthorized 
        materialExists(_materialId) 
    {
        materials[_materialId].status = _newStatus;
        
        emit MaterialStatusUpdated(_materialId, _newStatus, msg.sender);
    }
    
    function updateMaterialIPFS(
        string memory _materialId,
        string memory _newIpfsHashJson,
        bytes32 _newIntegrityHash
    ) 
        public 
        onlyAuthorized 
        materialExists(_materialId) 
    {
        materials[_materialId].ipfsHashJson = _newIpfsHashJson;
        materials[_materialId].integrityHash = _newIntegrityHash;
    }
    
    // ===============================
    // FONCTIONS DE CONSULTATION
    // ===============================
    
    function getMaterial(string memory _materialId) 
        public 
        view 
        returns (
            bool exists,
            string memory name,
            string memory materialType,
            string memory status,
            uint256 length_mm,
            uint256 carbonFootprint_cg,
            string memory ipfsHashJson,
            string memory ipfsHashIfc,
            bytes32 integrityHash,
            address depositor,
            uint256 timestamp,
            uint256 accessCount
        ) 
    {
        Material memory material = materials[_materialId];
        return (
            material.exists,
            material.name,
            material.materialType,
            material.status,
            material.length_mm,
            material.carbonFootprint_cg,
            material.ipfsHashJson,
            material.ipfsHashIfc,
            material.integrityHash,
            material.depositor,
            material.timestamp,
            material.accessCount
        );
    }
    
    function getMaterialsByType(string memory _materialType) 
        public 
        view 
        returns (string[] memory) 
    {
        string[] memory results = new string[](totalMaterials);
        uint256 count = 0;
        
        for (uint256 i = 0; i < materialIds.length; i++) {
            string memory id = materialIds[i];
            if (keccak256(bytes(materials[id].materialType)) == keccak256(bytes(_materialType))) {
                results[count] = id;
                count++;
            }
        }
        
        // Redimensionner le tableau aux résultats trouvés
        string[] memory finalResults = new string[](count);
        for (uint256 i = 0; i < count; i++) {
            finalResults[i] = results[i];
        }
        
        return finalResults;
    }
    
    function getMaterialsByStatus(string memory _status) 
        public 
        view 
        returns (string[] memory) 
    {
        string[] memory results = new string[](totalMaterials);
        uint256 count = 0;
        
        for (uint256 i = 0; i < materialIds.length; i++) {
            string memory id = materialIds[i];
            if (keccak256(bytes(materials[id].status)) == keccak256(bytes(_status))) {
                results[count] = id;
                count++;
            }
        }
        
        string[] memory finalResults = new string[](count);
        for (uint256 i = 0; i < count; i++) {
            finalResults[i] = results[i];
        }
        
        return finalResults;
    }
    
    // ===============================
    // FONCTIONS DE TRAÇABILITÉ
    // ===============================
    
    function recordAccess(
        string memory _materialId,
        string memory _accessType
    ) 
        public 
        onlyAuthorized 
        materialExists(_materialId) 
    {
        materials[_materialId].accessCount++;
        
        accessHistory.push(AccessLog({
            materialId: _materialId,
            accessor: msg.sender,
            accessType: _accessType,
            timestamp: block.timestamp
        }));
        
        emit MaterialAccessed(_materialId, msg.sender, _accessType, block.timestamp);
    }
    
    function getMaterialAccessHistory(string memory _materialId) 
        public 
        view 
        returns (
            address[] memory accessors,
            string[] memory accessTypes,
            uint256[] memory timestamps
        ) 
    {
        uint256 count = 0;
        
        // Compter les accès pour ce matériau
        for (uint256 i = 0; i < accessHistory.length; i++) {
            if (keccak256(bytes(accessHistory[i].materialId)) == keccak256(bytes(_materialId))) {
                count++;
            }
        }
        
        // Créer les tableaux de retour
        address[] memory resultAccessors = new address[](count);
        string[] memory resultTypes = new string[](count);
        uint256[] memory resultTimestamps = new uint256[](count);
        
        uint256 index = 0;
        for (uint256 i = 0; i < accessHistory.length; i++) {
            if (keccak256(bytes(accessHistory[i].materialId)) == keccak256(bytes(_materialId))) {
                resultAccessors[index] = accessHistory[i].accessor;
                resultTypes[index] = accessHistory[i].accessType;
                resultTimestamps[index] = accessHistory[i].timestamp;
                index++;
            }
        }
        
        return (resultAccessors, resultTypes, resultTimestamps);
    }
    
    // ===============================
    // GESTION INDEX GLOBAL
    // ===============================
    
    function updateGlobalIndex(
        string memory _ipfsHash,
        uint256 _materialCount
    ) 
        public 
        onlyAuthorized 
    {
        currentIndex = GlobalIndex({
            ipfsHash: _ipfsHash,
            materialCount: _materialCount,
            lastUpdated: block.timestamp
        });
        
        emit GlobalIndexUpdated(_ipfsHash, _materialCount, block.timestamp);
    }
    
    function getCurrentIndex() 
        public 
        view 
        returns (
            string memory ipfsHash,
            uint256 materialCount,
            uint256 lastUpdated
        ) 
    {
        return (
            currentIndex.ipfsHash,
            currentIndex.materialCount,
            currentIndex.lastUpdated
        );
    }
    
    // ===============================
    // FONCTIONS UTILITAIRES
    // ===============================
    
    function getTotalMaterials() public view returns (uint256) {
        return totalMaterials;
    }
    
    function getAllMaterialIds() public view returns (string[] memory) {
        return materialIds;
    }
    
    function getMaterialIdsPaginated(uint256 _offset, uint256 _limit) 
        public 
        view 
        returns (string[] memory) 
    {
        require(_offset < materialIds.length, "Offset trop élevé");
        
        uint256 end = _offset + _limit;
        if (end > materialIds.length) {
            end = materialIds.length;
        }
        
        string[] memory result = new string[](end - _offset);
        for (uint256 i = _offset; i < end; i++) {
            result[i - _offset] = materialIds[i];
        }
        
        return result;
    }
    
    // ===============================
    // FONCTIONS D'ADMINISTRATION
    // ===============================
    
    function pause() public onlyOwner {
        paused = true;
    }
    
    function unpause() public onlyOwner {
        paused = false;
    }
    
    function isPaused() public view returns (bool) {
        return paused;
    }
    
    // ===============================
    // FONCTIONS D'URGENCE
    // ===============================
    
    function emergencyWithdraw() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
    
    function updateOwner(address _newOwner) public onlyOwner {
        require(_newOwner != address(0), "Nouvelle adresse invalide");
        owner = _newOwner;
        authorizedActors[_newOwner] = true;
        actorRoles[_newOwner] = "OWNER";
    }
}