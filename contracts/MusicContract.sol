// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./LibraryContract.sol";
import "./WithdrawalContract.sol";

contract MusicContract {
    address public owner;
    address public withdrawalContract;
    mapping(string => address) public fileOwners;
    mapping(string => uint256) public fileBalances;
    event FileUploaded(address indexed uploader, string filename, uint256 amount);
    event FileDeleted(address indexed deleter, string filename);
    event VoteCasted(address indexed voter, string filename);
    event EthTransferred(address indexed sender, address indexed recipient, uint256 amount);

     LibraryContract public lib;

    modifier onlyOwner() {
        require(lib.isOwner(msg.sender), "Not the owner");
        _;
    }

    modifier fileExists(string memory filename) {
        require(fileOwners[filename] != address(0), "File not found");
        _;
    }

    modifier validAddress(address _address) {
        require(_address != address(0), "Invalid address");
        _;
    }

    constructor(address _withdrawalContract) {
    owner = msg.sender;
    lib = new LibraryContract();
    withdrawalContract = _withdrawalContract;
    }


    function uploadFile(string memory filename) public payable {
        require(msg.value > 0, "Value must be greater than 0");
        fileOwners[filename] = msg.sender;
        fileBalances[filename] += msg.value;
        emit FileUploaded(msg.sender, filename, msg.value);
    }

    function notifyVoteCasted(string memory filename) external {
        emit VoteCasted(msg.sender, filename);
    }

    function deleteFile(string memory filename) public onlyOwner {
        require(fileOwners[filename] != address(0), "File not found");
        uint256 balance = fileBalances[filename];
        fileBalances[filename] = 0;
        (bool success, ) = withdrawalContract.call{value: balance}(
            abi.encodeWithSignature("withdraw(address,uint256)", owner, balance)
        );
        require(success, "Withdrawal failed");
        emit FileDeleted(msg.sender, filename);
    }
}