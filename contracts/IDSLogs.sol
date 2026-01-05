// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract IDSLogs {

    struct Alert {
        string alertId;
        string sourceType;
        bytes32 logHash;
        uint256 timestamp;
        address reporter;
        bool isSuspicious;        
        uint16 confidencePct;     
        string modelVersion;      
    }

    address public owner;
    Alert[] public alerts;

    mapping(address => bool) public trustedReporters;
    mapping(bytes32 => bool) public usedLogHashes;

    event AlertAdded(
        uint256 indexed index,
        string alertId,
        bool isSuspicious,
        uint16 confidencePct,
        string modelVersion,
        uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    modifier onlyTrustedReporter() {
        require(trustedReporters[msg.sender] || msg.sender == owner, "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
        trustedReporters[msg.sender] = true;
    }

    function addTrustedReporter(address reporter) external onlyOwner {
        trustedReporters[reporter] = true;
    }

    function removeTrustedReporter(address reporter) external onlyOwner {
        trustedReporters[reporter] = false;
    }

    function addAlert(
        string memory alertId,
        string memory sourceType,
        bytes32 logHash,
        bool isSuspicious,
        uint16 confidencePct,
        string memory modelVersion
    ) external onlyTrustedReporter {

        require(!usedLogHashes[logHash], "Duplicate log");
        require(confidencePct <= 100, "Invalid confidence");

        usedLogHashes[logHash] = true;

        alerts.push(Alert({
            alertId: alertId,
            sourceType: sourceType,
            logHash: logHash,
            timestamp: block.timestamp,
            reporter: msg.sender,
            isSuspicious: isSuspicious,
            confidencePct: confidencePct,
            modelVersion: modelVersion
        }));

        emit AlertAdded(
            alerts.length - 1, 
            alertId, 
            isSuspicious, 
            confidencePct, 
            modelVersion,
            block.timestamp
        );
    }

    function getAlert(uint256 index) external view returns (
            string memory,
            string memory,
            bytes32,
            uint256,
            address,
            bool,
            uint16,
            string memory
    ) {
        require(index < alerts.length, "Out of bounds");
        Alert memory a = alerts[index];
        return (
            a.alertId,
            a.sourceType,
            a.logHash,
            a.timestamp,
            a.reporter,
            a.isSuspicious,
            a.confidencePct,
            a.modelVersion
        );
    }

    function getAlertsCount() public view returns (uint256){
        return alerts.length;
    }

    function verifyLog(bytes32 logHash) external view returns (bool){
        return usedLogHashes[logHash];
    }
}
