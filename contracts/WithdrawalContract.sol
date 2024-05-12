// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract WithdrawalContract {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    function withdraw(address payable recipient, uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Insufficient balance");
        recipient.transfer(amount);
    }

    receive() external payable {} // Allow contract to receive ether
}
