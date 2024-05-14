// SPDX-License-Identifier: MIT
const WithdrawalContract = artifacts.require("WithdrawalContract");
const VotingContract = artifacts.require("VotingContract");
const MusicContract = artifacts.require("MusicContract");
const LibraryContract = artifacts.require("LibraryContract");

module.exports = function (deployer) {
  deployer.deploy(WithdrawalContract);
  deployer.deploy(LibraryContract).then(() => {
    return deployer.deploy(MusicContract, LibraryContract.address);
  }).then(() => {
    return deployer.deploy(VotingContract, MusicContract.address);
  });
};
