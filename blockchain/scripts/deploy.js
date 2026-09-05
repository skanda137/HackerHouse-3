const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const MatchRegistry = await hre.ethers.getContractFactory("MatchRegistry");
  const contract = await MatchRegistry.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  const network = hre.network.name;
  const deployTx = contract.deploymentTransaction();
  const chainId = (await hre.ethers.provider.getNetwork()).chainId.toString();

  console.log(`MatchRegistry deployed to ${address} on network "${network}" (chainId ${chainId})`);
  console.log(`Deployment tx: ${deployTx.hash}`);

  const artifact = await hre.artifacts.readArtifact("MatchRegistry");
  const deploymentInfo = {
    network,
    chainId,
    address,
    deployTxHash: deployTx.hash,
    deployedAt: new Date().toISOString(),
    abi: artifact.abi,
  };

  const outDir = path.resolve(__dirname, "..", "deployments");
  fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, `${network}.json`);
  fs.writeFileSync(outPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`Deployment info written to ${outPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
