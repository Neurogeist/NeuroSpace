// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract LLMVerifier is Ownable, Pausable {
    struct HashInfo {
        address submitter;
        uint256 timestamp;
    }

    mapping(bytes32 => HashInfo) public hashInfo;

    event HashStored(address indexed submitter, bytes32 indexed hash, uint256 timestamp);

    /**
     * @notice Store a hash (verifiable message hash)
     * @param _hash The hash to store
     */
    function storeHash(bytes32 _hash) external whenNotPaused {
        require(hashInfo[_hash].timestamp == 0, "Hash already exists");

        hashInfo[_hash] = HashInfo({
            submitter: msg.sender,
            timestamp: block.timestamp
        });

        emit HashStored(msg.sender, _hash, block.timestamp);
    }

    /**
     * @notice Get full info for a stored hash
     */
    function getHashInfo(bytes32 _hash) external view returns (address submitter, uint256 timestamp) {
        HashInfo memory stored = hashInfo[_hash];
        require(stored.timestamp != 0, "Hash does not exist");
        return (stored.submitter, stored.timestamp);
    }

    /**
     * @notice Check if a hash exists
     */
    function hashExists(bytes32 _hash) external view returns (bool) {
        return hashInfo[_hash].timestamp != 0;
    }

    // Optional control: pause in case of abuse
    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}
