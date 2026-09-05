const { expect } = require("chai");
const { ethers } = require("hardhat");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

describe("MatchRegistry", function () {
  async function deployFixture() {
    const [owner, other] = await ethers.getSigners();
    const MatchRegistry = await ethers.getContractFactory("MatchRegistry");
    const contract = await MatchRegistry.deploy();
    await contract.waitForDeployment();
    return { contract, owner, other };
  }

  function hashOf(text) {
    return ethers.keccak256(ethers.toUtf8Bytes(text));
  }

  it("registers a match and verifies it back with the correct block/timestamp", async function () {
    const { contract } = await deployFixture();
    const dataHash = hashOf("original content");
    const postUrl = "https://example.com/original-post";

    const tx = await contract.registerMatch(dataHash, postUrl);
    const receipt = await tx.wait();

    const [verified, returnedUrl, blockNumber, timestamp] = await contract.verifyMatch(dataHash);
    expect(verified).to.equal(true);
    expect(returnedUrl).to.equal(postUrl);
    expect(blockNumber).to.equal(BigInt(receipt.blockNumber));
    expect(timestamp).to.be.greaterThan(0n);
  });

  it("returns verified=false for a hash that was never registered", async function () {
    const { contract } = await deployFixture();
    const dataHash = hashOf("never registered");

    const [verified, postUrl, blockNumber, timestamp] = await contract.verifyMatch(dataHash);
    expect(verified).to.equal(false);
    expect(postUrl).to.equal("");
    expect(blockNumber).to.equal(0n);
    expect(timestamp).to.equal(0n);
  });

  it("is tamper-evident: altering content after hashing changes the hash and fails verification", async function () {
    const { contract } = await deployFixture();
    const originalHash = hashOf("original content");
    await contract.registerMatch(originalHash, "https://example.com/original-post");

    const tamperedHash = hashOf("altered content");
    const [verified] = await contract.verifyMatch(tamperedHash);
    expect(verified).to.equal(false);
  });

  it("reverts with AlreadyRegistered when the same hash is registered twice", async function () {
    const { contract } = await deployFixture();
    const dataHash = hashOf("original content");
    await contract.registerMatch(dataHash, "https://example.com/original-post");

    await expect(
      contract.registerMatch(dataHash, "https://example.com/different-post")
    ).to.be.revertedWithCustomError(contract, "AlreadyRegistered");
  });

  it("emits MatchRegistered with the registering address", async function () {
    const { contract, owner } = await deployFixture();
    const dataHash = hashOf("event content");

    await expect(contract.registerMatch(dataHash, "https://example.com/post"))
      .to.emit(contract, "MatchRegistered")
      .withArgs(dataHash, "https://example.com/post", anyValue, anyValue, owner.address);
  });
});
