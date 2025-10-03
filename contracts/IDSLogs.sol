// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title IDSLogs
 * @dev A smart contract to store and manage immutable security logs on the Ethereum blockchain.
 * This prevents attackers from tampering with forensic evidence.
 */
contract IDSLogs {
    // A struct to represent a single security alert entry.
    // Structs are custom data types that group multiple variables.
    struct Alert {
        // A unique identifier for the alert.
        string alertId;
        // The type of the source that generated the alert (e.g., "Firewall", "Web Server", "IDS").
        string sourceType;
        // The raw log data or a summary of the event.
        string logData;
        // The Unix timestamp when the alert was logged on the blockchain.
        uint256 timestamp;
        // The Ethereum address of the entity that reported the alert.
        address reporter;
    }

    // A dynamic array to store all the security alerts.
    // The `public` visibility automatically creates a getter function to read the array.
    Alert[] public alerts;

    // An event to signal that a new alert has been successfully added to the blockchain.
    // Events are useful for off-chain applications (like your backend and frontend)
    // to efficiently listen for new data without constantly polling.
    event AlertAdded(
        string indexed alertId,
        address indexed reporter,
        uint256 timestamp
    );

    // A mapping to keep track of trusted entities (e.g., specific IDS instances or server agents)
    // that are allowed to report alerts.
    // The key is an address, and the value is a boolean indicating if it's trusted.
    mapping(address => bool) public isTrustedReporter;

    // The address of the contract's owner. This is typically the address that deployed the contract.
    address public owner;

    // A modifier is a piece of code that can be used to change the behavior of functions.
    // This one ensures a function can only be called by the contract owner.
    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can perform this action");
        _; // The `_` tells the compiler to run the rest of the function's code.
    }

    // The constructor is a special function that runs only once when the contract is deployed.
    // It sets the `owner` to the address that deployed it.
    constructor() {
        owner = msg.sender;
        isTrustedReporter[msg.sender] = true;
    }

    /**
     * @dev Function to add a new trusted reporter.
     * Only the contract owner can call this function.
     * @param _reporter The Ethereum address to be granted trusted reporter status.
     */
    function addTrustedReporter(address _reporter) public onlyOwner {
        require(_reporter != address(0), "Invalid address");
        isTrustedReporter[_reporter] = true;
    }

    /**
     * @dev Function to revoke the trusted status of a reporter.
     * Only the contract owner can call this function.
     * @param _reporter The Ethereum address whose trusted status should be removed.
     */
    function removeTrustedReporter(address _reporter) public onlyOwner {
        require(_reporter != address(0), "Invalid address");
        isTrustedReporter[_reporter] = false;
    }

    /**
     * @dev The main function to log a new security alert on the blockchain.
     * This function can only be called by a trusted reporter.
     * @param _alertId The unique ID for the alert.
     * @param _sourceType The type of the alert source.
     * @param _logData The raw log data.
     */
    function addAlert(
        string memory _alertId,
        string memory _sourceType,
        string memory _logData
    ) public {
        // A require statement checks for a condition and reverts the transaction if it's false.
        // This ensures only trusted reporters can add alerts.
        require(isTrustedReporter[msg.sender], "Not a trusted reporter");
        
        // Push the new alert to the `alerts` array.
        alerts.push(
            Alert({
                alertId: _alertId,
                sourceType: _sourceType,
                logData: _logData,
                timestamp: block.timestamp,
                reporter: msg.sender
            })
        );
        
        // Emit the `AlertAdded` event to make the new entry easily discoverable.
        emit AlertAdded(_alertId, msg.sender, block.timestamp);
    }

    /**
     * @dev A view function to get a specific alert by its index.
     * 'view' functions don't modify the state and are free to call.
     * @param _index The index of the alert in the `alerts` array.
     * @return The Alert struct at the given index.
     */
    function getAlert(uint256 _index) public view returns (Alert memory) {
        require(_index < alerts.length, "Index out of bounds");
        return alerts[_index];
    }

    function getAlertsCount() public view returns (uint256){
        return alerts.length;
    }
}