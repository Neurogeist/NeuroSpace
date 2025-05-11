// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract NeuroCoin is ERC20Capped, Ownable {
    constructor() 
        ERC20("NeuroCoin", "NSPACE") 
        ERC20Capped(100_000_000 * 10 ** 18)  // max supply = 100 million NSPACE
    {
        // Mint initial supply to deployer (for example, 10M NSPACE)
        _mint(msg.sender, 10_000_000 * 10 ** 18);
    }

    /**
     * @notice Mint NeuroCoin to a specific address. Can only be called by owner.
     * @param to Address to receive minted tokens
     * @param amount Amount to mint (in wei)
     */
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount); // Enforces cap via ERC20Capped
    }
}