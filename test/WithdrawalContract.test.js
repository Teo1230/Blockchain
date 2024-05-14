const WithdrawalContract = artifacts.require("WithdrawalContract");

contract("WithdrawalContract", (accounts) => {
  let withdrawalContract;
  const owner = accounts[0];
  const recipient = accounts[1];

  before(async () => {
    withdrawalContract = await WithdrawalContract.deployed();
  });

  it("should allow the owner to withdraw funds", async () => {
    const initialBalance = web3.utils.toBN(await web3.eth.getBalance(recipient));

    // Send some ether to the contract
    const amount = web3.utils.toWei("1", "ether");
    await withdrawalContract.sendTransaction({ from: owner, value: amount });

    // Withdraw funds from the contract
    await withdrawalContract.withdraw(recipient, amount, { from: owner });

    // Check if the recipient received the funds
    const finalBalance = web3.utils.toBN(await web3.eth.getBalance(recipient));
    const expectedFinalBalance = initialBalance.add(web3.utils.toBN(amount));
    assert.equal(finalBalance.toString(), expectedFinalBalance.toString(), "Withdrawal failed");
  });

  it("should revert when a non-owner tries to withdraw funds", async () => {
    // Try to withdraw funds from the contract as a non-owner
    const amount = web3.utils.toWei("1", "ether");
    try {
      await withdrawalContract.withdraw(recipient, amount, { from: recipient });
      assert.fail("Withdrawal by non-owner should have reverted");
    } catch (error) {
      assert.include(error.message, "revert", "Expected revert");
    }
  });
});
