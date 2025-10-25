// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract IDSLogs {
    struct Alert {
        string alertId;
        string sourceType;
        string logData;
        uint256 timestamp;
        address reporter;
        bool isSuspicious;        // ML-detected flag
        uint16 confidencePct;     // ML model confidence (0–100)
        string modelVersion;      // Version identifier of model
    }

    address public owner;
    Alert[] public alerts;
    mapping(address => bool) public trustedReporters;

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
        require(trustedReporters[msg.sender] || msg.sender == owner, "Not authorized reporter");
        _;
    }

    constructor() {
        owner = msg.sender;
        trustedReporters[msg.sender] = true;
    }

    function addTrustedReporter(address _reporter) public onlyOwner {
        trustedReporters[_reporter] = true;
    }

    function removeTrustedReporter(address _reporter) public onlyOwner {
        trustedReporters[_reporter] = false;
    }

    function addAlert(
        string memory _alertId,
        string memory _sourceType,
        string memory _logData,
        bool _isSuspicious,
        uint16 _confidencePct,
        string memory _modelVersion
    ) public onlyTrustedReporter {
        uint256 ts = block.timestamp;
        alerts.push(Alert({
            alertId: _alertId,
            sourceType: _sourceType,
            logData: _logData,
            timestamp: ts,
            reporter: msg.sender,
            isSuspicious: _isSuspicious,
            confidencePct: _confidencePct,
            modelVersion: _modelVersion
        }));
        emit AlertAdded(alerts.length - 1, _alertId, _isSuspicious, _confidencePct, _modelVersion, ts);
    }

    function getAlert(uint256 _index) public view returns (Alert memory) {
        require(_index < alerts.length, "Index out of bounds");
        return alerts[_index];
    }

    function getAlertsCount() public view returns (uint256){
        return alerts.length;
    }
}
