// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract NeuroTokenPayment is Ownable {
    event PaymentReceived(address indexed sender, uint256 amount, string sessionId);
    event PriceUpdated(uint256 oldPrice, uint256 newPrice);

    IERC20 public neuroCoin;
    uint256 public pricePerMessage;
    address public feeReceiver;

    constructor(address _neuroCoin, address _feeReceiver) Ownable(msg.sender) {
        neuroCoin = IERC20(_neuroCoin);
        feeReceiver = _feeReceiver;
        pricePerMessage = 1 * 10**18; // Default to 1 NSPACE
    }

    function payForMessage(string memory sessionId) external {
        bool success = neuroCoin.transferFrom(msg.sender, feeReceiver, pricePerMessage);
        require(success, "Token transfer failed");
        emit PaymentReceived(msg.sender, pricePerMessage, sessionId);
    }

    function setFeeReceiver(address newReceiver) external onlyOwner {
        require(newReceiver != address(0), "Receiver cannot be zero address");
        feeReceiver = newReceiver;
    }

    function setPrice(uint256 newPrice) external onlyOwner {
        require(newPrice > 0, "Price must be positive");
        uint256 oldPrice = pricePerMessage;
        pricePerMessage = newPrice;
        emit PriceUpdated(oldPrice, newPrice);
    }
}
