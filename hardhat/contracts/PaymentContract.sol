// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract ChatPayment is ReentrancyGuard, Pausable {
    event PaymentReceived(address indexed sender, uint256 amount, string sessionId);
    event PriceUpdated(uint256 oldPrice, uint256 newPrice);
    event Withdrawn(address indexed recipient, uint256 amount);

    address public owner;
    uint256 public pricePerMessage = 0.00001 ether;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /// @notice Pay to submit a message
    function payForMessage(string memory sessionId)
        external
        payable
        whenNotPaused
        nonReentrant
    {
        require(msg.value == pricePerMessage, "Incorrect payment amount");
        require(bytes(sessionId).length > 0, "Session ID required");

        emit PaymentReceived(msg.sender, msg.value, sessionId);
    }

    /// @notice Withdraw accumulated ETH to owner
    function withdraw() external onlyOwner nonReentrant {
        uint256 amount = address(this).balance;
        require(amount > 0, "No balance to withdraw");
        payable(owner).transfer(amount);
        emit Withdrawn(owner, amount);
    }

    /// @notice Update the price per message
    function setPrice(uint256 newPrice) external onlyOwner {
        require(newPrice > 0, "Price must be positive");
        uint256 oldPrice = pricePerMessage;
        pricePerMessage = newPrice;
        emit PriceUpdated(oldPrice, newPrice);
    }

    /// @notice Pause the contract (disables payForMessage)
    function pause() external onlyOwner {
        _pause(); // Emits Paused event
    }

    /// @notice Unpause the contract
    function unpause() external onlyOwner {
        _unpause(); // Emits Unpaused event
    }

    /// @notice Prevent accidental ETH sends
    receive() external payable {
        revert("Use payForMessage");
    }

    fallback() external payable {
        revert("Invalid function call");
    }
}
