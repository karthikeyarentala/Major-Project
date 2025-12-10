const express = require('express');
const { Web3 } = require('web3');
const HDWalletProvider = require('@truffle/hdwallet-provider');
const IDSLogsContract = require('../build/contracts/IDSLogs.json');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const crypto = require('crypto');

const app = express();
app.use(bodyParser.json());
app.use(cors());

const MNEMONIC = 'glove flee direct embrace theory leaf forum tragic shuffle hole connect feel';
const RPC_URL = 'http://127.0.0.1:8545';
const CONTRACT_ADDRESS = '0x29Ff6Cb0AE9e25Ea8724d2E34234A6a1fc0eC8F9';
const ML_API_URL = 'http://127.0.0.1:5000/predict';
const PORT = 3001;

const contractPath = path.resolve(__dirname, '../build/contracts/IDSLogs.json');
const contractJson = JSON.parse(fs.readFileSync(contractPath, 'utf8'));
const contractABI = contractJson.abi;

//Initialize Web3 connection and get account
let web3, idsLogsContract, acc;

(async () => {
  try {
    console.log("🔄 Initializing provider...");
    const provider = new HDWalletProvider({
        mnemonic: MNEMONIC,
        providerOrUrl: RPC_URL,
    });

    web3 = new Web3(provider);
        
    //legacy transactions for compatibility with ganache-cli
    /*web3.eth.transactionConfirmationBlocks = 1;
    web3.eth.transactionBlockTimeout = 5;
    web3.eth.defaultTransactionType = 0;*/

    await web3.eth.net.isListening();
    console.log("✅ Connected to Ethereum network");

    const accounts = await web3.eth.getAccounts();
    acc = accounts[0];
    console.log(`✅ Using account: ${acc}`);

    const contractPath = path.resolve(__dirname, '../build/contracts/IDSLogs.json');
    const contractJson = JSON.parse(fs.readFileSync(contractPath, 'utf8'));
    const contractABI = contractJson.abi;

    idsLogsContract = new web3.eth.Contract(contractABI, CONTRACT_ADDRESS);
    console.log(`✅ Contract loaded at: ${CONTRACT_ADDRESS}`);
  } catch (err) {
    console.error("❌ Web3 initialization failed:", err.message);
    process.exit(1);
  }
})();


app.post('/api/log-alert', async (req,res)=>{
    try {
    const { alertId, sourceType, logData } = req.body;

    if (!alertId || !sourceType || !logData) {
      return res.status(400).json({ error: "Missing required fields." });
    }

    console.log(`🔍 Received new log: ${alertId}`);

    const logHash = crypto.createHash('sha256').update(logData).digest('hex');
    const logHashBytes32 = '0x' + logHash;  // prefixes the 0x for web3 to treat as bytes32
    console.log(`Log Hash (SHA-256): ${logHashBytes32}`);

    // Step 1: Call ML microservice
    let mlResult;
    try {
      const response = await axios.post(ML_API_URL, {
        logData: logData,
      });
      mlResult = response.data;
    } catch (err) {
      console.error("❌ Error contacting ML service:", err.message);
      return res.status(500).json({ error: "ML service unavailable" });
    }

    const isSuspicious = mlResult.isSuspicious || false;
    const confidence = mlResult.confidence || 0;
    const modelVersion = mlResult.modelVersion || "unknown";
    const confidencePct = Math.round(confidence * 100);

    console.log(
      `🤖 ML Result: Suspicious=${isSuspicious}, Confidence=${confidencePct}%, Model=${modelVersion}`
    );

    // Step 2: Store in blockchain
    const transaction = idsLogsContract.methods.addAlert(
      alertId,
      sourceType,
      logHashBytes32,
      isSuspicious,
      confidencePct,
      modelVersion
    );

    //const gasEstimate = await transaction.estimateGas({ from: acc });
    const fixedGasLimit = 500000n; // Set a fixed gas limit
    const txReceipt = await transaction.send({
    from: acc,
    gas: fixedGasLimit,
    });


    console.log(`✅ Transaction successful: ${txReceipt.transactionHash}`);

    // Step 3: Return response
    res.json({
      success: true,
      txHash: txReceipt.transactionHash,
      isSuspicious,
      confidencePct,
      modelVersion,
    });
  } catch (err) {
    console.error("❌ Error adding alert:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

//Getting an alert
app.get("/api/alerts", async (req, res) => {
  try {
    const count = await idsLogsContract.methods.getAlertsCount().call();
    const alerts = [];

    for (let i = 0; i < count; i++) {
      const alert = await idsLogsContract.methods.getAlert(i).call();
      alerts.push(alert);
    }

    res.json(alerts);
  } catch (err) {
    console.error("❌ Error fetching alerts:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

// Start the server and initialize web3
app.listen(PORT, () => {
    console.log(`Backend server listening at http://localhost:${PORT}`);
});