const LibraryContract = artifacts.require("LibraryContract");

contract("LibraryContract", (accounts) => {
  let libraryContract;
  const owner = accounts[0];

  before(async () => {
    libraryContract = await LibraryContract.deployed();
  });

  it("should return true for owner", async () => {
    const result = await libraryContract.isOwner(owner);
    assert.isTrue(result, "Expected owner to be true");
  });

  it("should return false for non-owner", async () => {
    const nonOwner = accounts[1];
    const result = await libraryContract.isOwner(nonOwner);
    assert.isFalse(result, "Expected non-owner to be false");
  });
});
