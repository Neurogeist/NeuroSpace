// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract NeuroTokenPayment is Ownable, ReentrancyGuard, Pausable {
    event PaymentReceived(address indexed sender, uint256 amount, string sessionId);
    event PriceUpdated(uint256 oldPrice, uint256 newPrice);

    IERC20 public neuroCoin;
    uint256 public pricePerMessage;
    address public feeReceiver;

    constructor(address _neuroCoin, address _feeReceiver) {
        require(_neuroCoin != address(0), "Invalid token address");
        require(_feeReceiver != address(0), "Invalid fee receiver");
        neuroCoin = IERC20(_neuroCoin);
        feeReceiver = _feeReceiver;
        pricePerMessage = 1 * 10**18;
    }

    /// @notice Called by users to pay with NeuroCoin for a message
    function payForMessage(string memory sessionId)
        external
        whenNotPaused
        nonReentrant
    {
        require(bytes(sessionId).length > 0, "Session ID required");

        bool success = neuroCoin.transferFrom(msg.sender, feeReceiver, pricePerMessage);
        require(success, "Token transfer failed");

        emit PaymentReceived(msg.sender, pricePerMessage, sessionId);
    }

    /// @notice Update the receiver of token payments
    function setFeeReceiver(address newReceiver) external onlyOwner {
        require(newReceiver != address(0), "Receiver cannot be zero address");
        feeReceiver = newReceiver;
    }

    /// @notice Update the token price per message
    function setPrice(uint256 newPrice) external onlyOwner {
        require(newPrice > 0, "Price must be positive");
        uint256 oldPrice = pricePerMessage;
        pricePerMessage = newPrice;
        emit PriceUpdated(oldPrice, newPrice);
    }

    /// @notice Pause the contract (disables payForMessage)
    function pause() external onlyOwner {
        _pause();
    }

    /// @notice Unpause the contract
    function unpause() external onlyOwner {
        _unpause();
    }
}
