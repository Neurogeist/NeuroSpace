// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ChatPayment {
    event PaymentReceived(address indexed sender, uint256 amount, string sessionId);
    
    uint256 public constant PRICE_PER_MESSAGE = 0.0001 ether;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function payForMessage(string memory sessionId) external payable {
        require(msg.value == PRICE_PER_MESSAGE, "Incorrect payment amount");
        emit PaymentReceived(msg.sender, msg.value, sessionId);
    }
    
    function withdraw() external {
        require(msg.sender == owner, "Only owner can withdraw");
        payable(owner).transfer(address(this).balance);
    }
} 