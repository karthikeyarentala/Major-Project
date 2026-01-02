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
const http = require('http');
const { Server } = require('socket.io');

const app = express();
app.use(bodyParser.json());
app.use(cors());

const MNEMONIC = 'recall wheel produce eye habit must human space card expand exotic miracle';
const RPC_URL = 'http://127.0.0.1:8545';
const CONTRACT_ADDRESS = '0xCB90DADa293C1e7457bff228493a87DB8409C18E';
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

const server = http.createServer(app);
const io = new Server(server, {
  cors: {origin: "*"}
})

app.post('/api/log-alert', async (req, res) => {
    console.log("Recieved Body:", req.body);
    try {
        const { alertId, sourceType, logData, severity } = req.body;

        if (!alertId || !sourceType || !logData) {
            return res.status(400).json({ error: "Missing required fields." });
        }
        const isSus = (severity === 'Suspicious' || severity === 'Malicious' || severity === 'High'); 

        // This sends the data to the UI before it even touches the blockchain
        io.emit('new-live-log', {
            alertId,
            sourceType,
            logData,
            severity: severity || 'Safe', 
            isSuspicious: isSus,
            timestamp: Math.floor(Date.now() / 1000)
        });

        console.log(`📡 Broadcasted live log: ${alertId} (${severity})`);

        if(!isSus) {
          return res.json({ success: true, message: "Safe traffic broadcasted." });
        }
        console.log(`🚨 Archiving Suspicious Alert to Blockchain: ${alertId}`);        // IF SAFE TRAFFIC, STOP HERE

        const logHash = crypto.createHash('sha256').update(logData).digest('hex');
        const logHashBytes32 = '0x' + logHash;

        const confPct = 100;
        const modelVer = "Snort-Rule-Engine";


        // Storing in blockchain
        const transaction = idsLogsContract.methods.addAlert(
            alertId,
            sourceType,
            logHashBytes32,
            true,
            confPct,
            modelVer
        );

        const txReceipt = await transaction.send({
            from: acc,
            gas: 500000n,
        });

        console.log(`✅ Blockchain transaction successful: ${txReceipt.transactionHash}`);

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
    console.log(`WebSocket server is active for live logs...`);
});