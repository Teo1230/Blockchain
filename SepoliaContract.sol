// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SepoliaContract {
    address public owner;
    mapping(string => address) public fileOwners;
    event FileUploaded(address indexed uploader, string filename);
    event EthTransferred(address indexed from, address indexed to, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function uploadFile(string memory filename) public payable {
        require(msg.value > 0, "Value must be greater than 0");
        fileOwners[filename] = msg.sender;
        emit FileUploaded(msg.sender, filename);
    }

    function getFileOwner(string memory filename) public view returns (address) {
        return fileOwners[filename];
    }

    function transferEth(address payable recipient, uint256 amount) public onlyOwner {
        require(address(this).balance >= amount, "Insufficient balance");
        recipient.transfer(amount);
        emit EthTransferred(address(this), recipient, amount);
    }

    function examplePureFunction(uint256 a, uint256 b) public pure returns (uint256) {
        return a + b;
    }

    function exampleViewFunction() public view returns (uint256) {
        return address(this).balance;
    }

    function withdraw() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
}
