const MusicContract = artifacts.require("MusicContract");
const LibraryContract = artifacts.require("LibraryContract");

module.exports = function (deployer) {
  deployer.deploy(LibraryContract).then(() => {
    return deployer.deploy(MusicContract, LibraryContract.address);
  });
};
