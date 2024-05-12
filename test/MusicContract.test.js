const MusicContract = artifacts.require("MusicContract");

contract("MusicContract", (accounts) => {
  let musicContract;
  const owner = accounts[0];
  const uploader = accounts[1];
  const filename = "test.mp3";
  const amount = web3.utils.toWei("1", "ether");

  before(async () => {
    musicContract = await MusicContract.deployed();
  });

  it("should upload a file", async () => {
    await musicContract.uploadFile(filename, { from: uploader, value: amount });
    const fileOwner = await musicContract.fileOwners(filename);
    assert.equal(fileOwner, uploader, "File owner is incorrect");
  });

  it("should delete a file", async () => {
    await musicContract.uploadFile(filename, { from: uploader, value: amount });
    await musicContract.deleteFile(filename, { from: owner });
    const fileOwner = await musicContract.fileOwners(filename);
    console.log("File owner after deletion:", fileOwner); // Add this line for debugging
    assert.equal(fileOwner, "0x0000000000000000000000000000000000000000", "File was not deleted");
  });
  
});
