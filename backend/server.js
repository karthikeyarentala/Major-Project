require('dotenv').config();

const express = require('express');
const { Web3 } = require('web3');
const HDWalletProvider = require('@truffle/hdwallet-provider');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const crypto = require('crypto');
const http = require('http');
const { Server } = require('socket.io');
const IDSLogsContract = require('../build/contracts/IDSLogs.json');

const app = express();
app.use(bodyParser.json());
app.use(cors());

const MNEMONIC = 'worry drink banner alter behave someone vendor settle jacket forum frozen lady';
const RPC_URL = 'http://127.0.0.1:8545';
const CONTRACT_ADDRESS = '0x9706DB6E3331553FedFb0399Ec63b77755D4E926';
const API_KEY = process.env.API_KEY;
const PORT = 3001;

let web3, contract, account, web3Ready = false;

(async () => {
  const provider = new HDWalletProvider({
      mnemonic: MNEMONIC,
      providerOrUrl: RPC_URL,
  })
  web3 = new Web3(provider);
  const accounts = await web3.eth.getAccounts();
  account = accounts[0];

  contract = new web3.eth.Contract(
    IDSLogsContract.abi,
    CONTRACT_ADDRESS
  );

  web3Ready = true;

  console.log(`Blockchain Connected`);
})();

app.use((req, res, next) => {
if (!web3Ready) return res.status(503).json({error: "Blockchain connection not ready"});
if (req.headers['x-api-key'] !== API_KEY) {
  return res.status(403).json({error: "Unauthorized source"});
}
next();
});

const server = http.createServer(app);
const io = new Server(server, {cors: {origin: "*"}});

app.post('/api/log-alert', async (req, res) => {
  try{
    const { alertId, sourceType, severity, logData } = req.body;

    if(!alertId || !sourceType || !severity || !logData){
      return res.status(400).json({error: "Invalid payload"});
    }
    const isSuspicious = severity === "High";

    io.emit('new-live-log', {
      alertId,
      sourceType,
      logData,
      severity,
      isSuspicious,
      timestamp: Math.floor(Date.now()/1000)
    });
    
    if(!isSuspicious){
      return res.json({success: true});
    }

    const hash = crypto.createHash('sha256').update(logData).digest('Hex');

    await contract.methods.addAlert(
      alertId,
      sourceType,
      '0x'+hash,
      true,
      100,
      "Snort-Rule-Engine"
    ).send({from: account, gas: 500000});
    res.json({success: true});
  }
  catch(err){
    console.error(err);
    res.status(500).json({ error: "Backend error" });
  }
});

app.get('/api/alerts', async (req, res) => {
    try {
        const count = await contract.methods.getAlertsCount().call();
        const calls = [];

        for (let i = 0; i < count; i++) {
            calls.push(contract.methods.getAlert(i).call());
        }

        const data = await Promise.all(calls);
        res.json(data);
    } catch {
        res.status(500).json({ error: "Fetch failed" });
    }
});

server.listen(PORT, () => {
    console.log(`🚀 Backend running on ${PORT}`);
});
