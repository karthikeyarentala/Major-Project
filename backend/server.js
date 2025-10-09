const express = require('express');
const { Web3 } = require('web3');
const HDWalletProvider = require('@truffle/hdwallet-provider');
const IDSLogsContract = require('../build/contracts/IDSLogs.json');

const app = express();
const port = 3001;

app.use(express.json());

const privateKey = '600ca01ced89c9cf5590e494c5105d12b98daaf716357825b6c4da9dd6d02f77';
const provider = new HDWalletProvider(privateKey, 'http://127.0.0.1:8545');
const web3 = new Web3(provider);

//legacy transactions for compatibility with ganache-cli
web3.eth.transactionConfirmationBlocks = 1;
web3.eth.transactionBlockTimeout = 5;
web3.eth.defaultTransactionType = 0;

const contractAddress = '0xFD8D25D0d6174492C4723b537E0EbAe4EDC646a8';

let idsLogsContract;
let trustedReporterAddress;

// Function to analyze log data for suspecious keywords
const analyzeLogData = (logData) =>{
        if(!logData || typeof logData != 'string') return false;

        const SUSPICIOUS_KEYWORDS = [
            "revert", "error", "failed", "unauthorized", "attack", "malware", "phishing", "breach", 
            "exploit", "error", "ssh denied", "vulnerability", "ddos", "ransomware", "spyware", 
            "trojan", "worm", "suspicious", "hack", "compromise"
        ];

        const lowerCaseLogData = logData.toLowerCase();
        return SUSPICIOUS_KEYWORDS.some(keyword => lowerCaseLogData.includes(keyword));
}

// Function to initialize the contract
const initialize = async () => {
    web3.eth.getBlockNumber()
    .then(blockNumber => {
        console.log(`Successfully connected to Ganache. Current block number: ${blockNumber}`);
    })
    .catch(error => {
        console.error('Failed to connect to Ganache:', error);
    });

    idsLogsContract = new web3.eth.Contract(
        IDSLogsContract.abi,
        contractAddress
    );
    //getting the trusted reporter address directly from the deployed contract
    trustedReporterAddress = await idsLogsContract.methods.owner().call();
    console.log(`Trusted Reporter Address from contract: ${trustedReporterAddress}`);
};

// A POST endpoint to receive security alerts
app.post('/api/log-alert', async (req, res) => {

    const { alertId, sourceType, logData } = req.body;

    const isSuspicious = analyzeLogData(logData);

    if (!alertId || !sourceType || !logData) {
        return res.status(400).json({ error: 'Missing required alert data' });
    }

    try {
        const transaction = idsLogsContract.methods.addAlert(
            alertId,
            sourceType,
            logData,
            isSuspicious
        );
        const gasEstimate = await transaction.estimateGas({ from: trustedReporterAddress });
        await transaction.send({
            from: trustedReporterAddress,
            gas: '2000000',
            gasPrice: '20000000000'
        });
        res.status(200).json({ message: 'Alert successfully logged on the blockchain' });
    } catch (error) {
        console.error('Failed to log alert:', error);
        res.status(500).json({ error: 'Failed to log alert on the blockchain' });
    }
});

//Add a new trusted reporter 
app.post('/api/add-reporter', async (req,res)=>{
    const {reporterAddress} = req.body;

    if(!reporterAddress){
        return res.status(400).json({error: 'Missing reporter address'})
    }

    try{
        const trustedReporterAddress = await idsLogsContract.methods.owner().call();
        const transaction = idsLogsContract.methods.addTrustedReporter(reporterAddress);
        const gasEstimate = await transaction.estimateGas({from: trustedReporterAddress});
        await transaction.send({
            from: trustedReporterAddress,
            gas: gasEstimate + 20000n,
            gasPrice: '20000000000'
        })
        res.status(200).json({message: `Reporter ${reporterAddress} successfully added.`});
    } catch(error){
        console.error('Failed to add reporter:',error);
        res.status(500).json({error: 'Failed to add reporter on blockchain'});
    }
});

//Remove a truster reporter
app.post('/api/remove-reporter', async (req, res) => {
    const { reporterAddress } = req.body;
    
    if (!reporterAddress) {
        return res.status(400).json({ error: 'Missing reporter address' });
    }

    try {
        const trustedReporterAddress = await idsLogsContract.methods.owner().call();
        const transaction = idsLogsContract.methods.removeTrustedReporter(reporterAddress);
        const gasEstimate = await transaction.estimateGas({from: trustedReporterAddress});
        await transaction.send({
            from: trustedReporterAddress,
            gas: gasEstimate + 20000n,
            gasPrice: '20000000000'
        });
        res.status(200).json({ message: `Reporter ${reporterAddress} successfully removed.`});
    } catch (error) {
        console.error('Failed to remove reporter:', error);
        res.status(500).json({ error: 'Failed to remove reporter on the blockchain'});
    }
});

//Getting a index-based alert
app.get('/api/get-alert/:index', async (req, res) => {
    const index = req.params.index;

    try {
        const alert = await idsLogsContract.methods.getAlert(index).call();
        //converting the bigInt values to string to prevent serialization errors
        const sanitizedAlert = {
            alertId: alert.alertId,
            sourceType: alert.sourceType,
            logData: alert.logData,
            timestamp: alert.timestamp.toString(),
            reporter: alert.reporter,
            isSuspicious: alert.isSuspicious
        }
        res.status(200).json(sanitizedAlert);
    } catch (error) {
        console.error('Failed to get alert:', error);
        res.status(500).json({ error: 'Failed to get alert from the blockchain'});
    }
});

// A GET endpoint to get the total number of alerts
app.get('/api/get-alert-count', async (req, res) => {
    try {
        const count = await idsLogsContract.methods.alerts.length.call();
        res.status(200).json({ count: count.toString() });
    } catch (error) {
        console.error('Failed to get alert count:', error);
        res.status(500).json({ error: 'Failed to get alert count from the blockchain'});
    }
});

// Start the server and initialize web3
app.listen(port, () => {
    console.log(`Backend server listening at http://localhost:${port}`);
    initialize();
});