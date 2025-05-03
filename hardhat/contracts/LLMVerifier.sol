// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LLMVerifier {
    // Struct to store hash information
    struct HashInfo {
        address submitter;
        uint256 timestamp;
    }
    
    // Mapping from hash to HashInfo
    mapping(bytes32 => HashInfo) public hashInfo;
    
    // Event emitted when a hash is stored
    event HashStored(
        address indexed submitter,
        bytes32 hash,
        uint256 timestamp
    );
    
    /**
     * @dev Store a hash with submitter and timestamp
     * @param _hash The hash to store
     */
    function storeHash(bytes32 _hash) public {
        require(hashInfo[_hash].timestamp == 0, "Hash already exists");
        
        hashInfo[_hash] = HashInfo({
            submitter: msg.sender,
            timestamp: block.timestamp
        });
        
        emit HashStored(msg.sender, _hash, block.timestamp);
    }
    
    /**
     * @dev Get information about a stored hash
     * @param _hash The hash to look up
     * @return submitter The address that submitted the hash
     * @return timestamp The block timestamp when the hash was submitted
     */
    function getHashInfo(bytes32 _hash) public view returns (address submitter, uint256 timestamp) {
        HashInfo memory info = hashInfo[_hash];
        require(info.timestamp != 0, "Hash does not exist");
        return (info.submitter, info.timestamp);
    }
    
    /**
     * @dev Check if a hash exists
     * @param _hash The hash to check
     * @return exists True if the hash exists
     */
    function hashExists(bytes32 _hash) public view returns (bool exists) {
        return hashInfo[_hash].timestamp != 0;
    }
} 