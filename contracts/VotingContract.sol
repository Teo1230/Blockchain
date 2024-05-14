// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./MusicContract.sol";

contract VotingContract {
    struct AudioFile {
        address musicContract; // Adresa contractului MusicContract care deține fișierul audio
        uint256 votes;
        bool exists;
    }

    mapping(string => AudioFile) public audioFiles;
    MusicContract public musicContract; // Referință către contractul MusicContract

    constructor(address _musicContractAddress) {
        musicContract = MusicContract(_musicContractAddress);
    }

    modifier fileExists(string memory filename) {
        require(musicContract.fileOwners(filename) != address(0), "File does not exist");
        _;
    }

    function voteForAudioFile(string memory filename) external fileExists(filename) {
        audioFiles[filename].votes++;
        musicContract.notifyVoteCasted(filename);
    }

    function getVotesForAudioFile(string memory filename) external view fileExists(filename) returns (uint256) {
        return audioFiles[filename].votes;
    }

}