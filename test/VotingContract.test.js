// const VotingContract = artifacts.require("VotingContract");
// const MusicContract = artifacts.require("MusicContract");

// contract("VotingContract", (accounts) => {
//   let votingContract;
//   let musicContract;
//   const owner = accounts[0];
//   const uploader = accounts[1];
//   const filename = "test.mp3";

//   before(async () => {
//     musicContract = await MusicContract.new();
//     votingContract = await VotingContract.new(musicContract.address);
//   });

//   it("should allow voting for an existing audio file", async () => {
//     await musicContract.uploadFile(filename, { from: uploader, value: web3.utils.toWei("1", "ether") });
//     await votingContract.voteForAudioFile(filename, { from: owner });

//     const votes = await votingContract.getVotesForAudioFile(filename);
//     assert.equal(votes, 1, "Votes not incremented correctly");
//   });

//   it("should revert when voting for a non-existing audio file", async () => {
//     const nonExistingFilename = "non_existing_file.mp3";

//     try {
//       await votingContract.voteForAudioFile(nonExistingFilename, { from: owner });
//       assert.fail("Voting for non-existing file should revert");
//     } catch (error) {
//       assert(error.message.includes("File does not exist"), "Unexpected revert reason");
//     }
//   });
// });
