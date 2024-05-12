// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LibraryContract {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function isOwner(address _sender) public view returns (bool) {
        return owner == _sender;
    }
}
