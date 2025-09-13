// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleTest
 * @dev Contrat de test simple pour vérifier la configuration Brownie
 */
contract SimpleTest {
    
    uint256 public counter;
    address public owner;
    
    event CounterIncremented(uint256 newValue);
    
    constructor() {
        owner = msg.sender;
        counter = 0;
    }
    
    function increment() external {
        counter += 1;
        emit CounterIncremented(counter);
    }
    
    function getCounter() external view returns (uint256) {
        return counter;
    }
    
    function getOwner() external view returns (address) {
        return owner;
    }
}