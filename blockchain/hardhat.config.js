const path = require("path");
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const { RPC_URL, PRIVATE_KEY } = process.env;

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    // Local dev/testing network — run with `npm run node`, deploy with
    // `npm run deploy:local`. Free, instant, no MATIC required.
    localhost: {
      url: "http://127.0.0.1:8545",
    },
    // Polygon Amoy testnet — needs RPC_URL and PRIVATE_KEY in the repo
    // root .env (never commit real values; see .env.example).
    amoy: {
      url: RPC_URL || "https://rpc-amoy.polygon.technology",
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
      chainId: 80002,
    },
  },
};
