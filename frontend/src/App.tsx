import { useState, useEffect, useCallback } from 'react';
// FIX 1: Import Web3 from a CDN to make it available in the browser preview
import Web3 from 'web3';

// FIX 2: Remove the file import. We will define the minimal ABI we need right here.
// import IDSLogsContract from './IDSLogs.json';

// Define a TypeScript interface for the Alert data structure
interface Alert {
    alertId: string;
    sourceType: string;
    logData: string;
    timestamp: bigint; // BigInt is the correct type for Solidity's uint256
    reporter: string;
    isSuspicious: boolean;
    // These fields are from your contract
    confidence: bigint;
    modelVersion: string;
}

// --- MINIMAL CONTRACT ABI ---
// This replaces the need for the IDSLogs.json file *for this preview*
// In your local project, replace this with: import IDSLogsContract from './IDSLogs.json';
const IDSLogsContract = {
    abi: [
        {
            "inputs": [],
            "name": "getAlertsCount",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "index",
                    "type": "uint256"
                }
            ],
            "name": "getAlert",
            "outputs": [
                {
                    "components": [
                        {
                            "internalType": "string",
                            "name": "alertId",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "sourceType",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "logData",
                            "type": "string"
                        },
                        {
                            "internalType": "uint256",
                            "name": "timestamp",
                            "type": "uint256"
                        },
                        {
                            "internalType": "address",
                            "name": "reporter",
                            "type": "address"
                        },
                        {
                            "internalType": "bool",
                            "name": "isSuspicious",
                            "type": "bool"
                        },
                        {
                            "internalType": "uint256",
                            "name": "confidence",
                            "type": "uint256"
                        },
                        {
                            "internalType": "string",
                            "name": "modelVersion",
                            "type": "string"
                        }
                    ],
                    "internalType": "struct IDSLogs.Alert",
                    "name": "",
                    "type": "tuple"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]
};
// --- END MINIMAL ABI ---


const contractAddress = '0x77090e1AFd87D9f54aF665E2b15D85850dFE0DCf'; // PASTE YOUR CONTRACT ADDRESS
const ganachePort = 8545;
// backendApiUrl is no longer needed as we removed the form
// const backendApiUrl = 'http://localhost:3001/api/log-alert';

// --- Simple Styles ---
// We'll add class names for the animations later
const styles: { [key: string]: React.CSSProperties } = {
    container: { fontFamily: 'Arial, sans-serif', width: '1470px', margin: '0 auto', padding: '20px', backgroundColor: '#000000' },
    h1: { color: '#240572ff', textAlign: 'center' },
    h2: { color: '#240572ff', borderBottom: '2px solid #bdc3c7', paddingBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
    message: { padding: '12px', borderRadius: '4px', marginTop: '10px', textAlign: 'center', fontWeight: 'bold' },
    error: { background: '#e74c3c', color: 'white', border: '1px solid #c0392b' },
    logList: { listStyleType: 'none', padding: '0' },
    logItem: {
        background: '#000',
        border: '1px solid #ddd', // Base border
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '10px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.5)',
        transition: 'background-color 0.2s ease-in-out', // Keep hover transition
        position: 'relative', // Needed for potential border-image or pseudo-elements if box-shadow fails
        overflow: 'hidden' // Keep glow contained
    },
    // Keep border styles for color indicator
    logSuspiciousBorder: { borderLeft: '5px solid #ad1b0bff' },
    logSafeBorder: { borderLeft: '5px solid #067d38ff' },
    statusText: { fontWeight: 'bold', textTransform: 'uppercase' },
    suspiciousText: { color: '#e74c3c' },
    safeText: { color: '#2ecc71' },
    smallText: { color: '#7f8c8d', fontSize: '0.9em', wordBreak: 'break-all' },
    refreshButton: {
        background: '#95a5a6',
        color: 'white',
        padding: '8px 15px',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 'bold',
        marginLeft: '10px'
    },
    refreshButtonLoading: {
        background: '#bdc3c7',
        cursor: 'not-allowed',
    }
};
// --- End Styles ---

// --- CSS Keyframes for Electric Border ---
const electricBorderStyles = `
  @keyframes electric-red {
    0% { box-shadow: 0 0 3px 1px rgba(231, 76, 60, 0.7); }
    50% { box-shadow: 0 0 7px 3px rgba(231, 76, 60, 0.7); }
    100% { box-shadow: 0 0 3px 1px rgba(231, 76, 60, 0.7); }
  }
  @keyframes electric-green {
    0% { box-shadow: 0 0 3px 1px rgba(46, 204, 113, 0.7); }
    50% { box-shadow: 0 0 7px 3px rgba(46, 204, 113, 0.7); }
    100% { box-shadow: 0 0 3px 1px rgba(46, 204, 113, 0.7); }
  }

  .electric-border-red {
    animation: electric-red 1.5s infinite linear;
  }

  .electric-border-green {
    animation: electric-green 1.5s infinite linear;
  }
`;
// --- End Keyframes ---

function App() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [apiError, setApiError] = useState<string | null>(null);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);


    const fetchAlerts = useCallback(async () => {
        console.log("Fetching alerts...");
        setLoading(true);
        setApiError(null);
        try {
            const web3 = new Web3(`http://127.0.0.1:${ganachePort}`);
            const idsLogsContract = new web3.eth.Contract(
                IDSLogsContract.abi as any,
                contractAddress
            );

            const alertCount = await idsLogsContract.methods.getAlertsCount().call();
            console.log("Alert count from blockchain:", String(alertCount));

            const fetchedAlerts: Alert[] = [];
            for (let i = 0; i < Number(alertCount); i++) {
                const alert = await idsLogsContract.methods.getAlert(i).call() as any;
                fetchedAlerts.push({
                    alertId: alert[0],
                    sourceType: alert[1],
                    logData: alert[2],
                    timestamp: alert[3],
                    reporter: alert[4],
                    isSuspicious: alert[5],
                    confidence: alert[6],
                    modelVersion: alert[7],
                });
            }

            setAlerts(fetchedAlerts.reverse());
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
            setApiError('Failed to connect to blockchain or fetch alerts. Is Ganache running?');
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        fetchAlerts();
    }, [fetchAlerts]);

    const handleRefresh = () => {
        fetchAlerts();
    };


    return (
        <div style={styles.container}>
            {/* Inject the CSS animations */}
            <style>{electricBorderStyles}</style>

            <h1 style={styles.h1}>Decentralized Intrusion Detection System</h1>

            {apiError && <div style={{ ...styles.message, ...styles.error }}>{apiError}</div>}

            <h2 style={styles.h2}>
                Stored Immutable Logs
                <button
                    onClick={handleRefresh}
                    style={loading ? {...styles.refreshButton, ...styles.refreshButtonLoading} : styles.refreshButton}
                    disabled={loading}
                >
                    {loading ? 'Refreshing...' : 'Refresh'}
                </button>
            </h2>

            {loading && alerts.length === 0 ? (
                <div>Loading alerts...</div>
            ) : !loading && alerts.length === 0 && !apiError ? (
                <p>No alerts found on the blockchain.</p>
            ) : (
                <ul style={styles.logList}>
                    {alerts.map((alert, index) => {
                        const isHovered = hoveredIndex === index;
                        const baseBorderStyle = alert.isSuspicious ? styles.logSuspiciousBorder : styles.logSafeBorder;
                        const hoverStyle = isHovered
                            ? (alert.isSuspicious ? styles.logItemHoverSuspicious : styles.logItemHoverSafe)
                            : {};
                        // NEW: Determine the animation class
                        const animationClass = alert.isSuspicious ? 'electric-border-red' : 'electric-border-green';

                        return (
                            <li
                                key={index}
                                className={animationClass} // Apply the animation class
                                style={{
                                    ...styles.logItem,
                                    ...baseBorderStyle,
                                    ...hoverStyle
                                }}
                                onMouseEnter={() => setHoveredIndex(index)}
                                onMouseLeave={() => setHoveredIndex(null)}
                            >
                                <strong>ID:</strong> {alert.alertId}<br />
                                <strong>Source:</strong> {alert.sourceType}<br />
                                <strong>Data:</strong> {alert.logData}<br />
                                <strong>Status:</strong> {alert.isSuspicious ?
                                    <span style={{ ...styles.statusText, ...styles.suspiciousText }}>🔴 SUSPICIOUS</span> :
                                    <span style={{ ...styles.statusText, ...styles.safeText }}>🟢 SAFE</span>
                                }<br />
                                <strong>Confidence:</strong> {String(alert.confidence)}%<br />
                                <strong>Model:</strong> {alert.modelVersion}<br />
                                <strong>Timestamp:</strong> {new Date(Number(alert.timestamp) * 1000).toLocaleString()}<br />
                                <small style={styles.smallText}><strong>Reporter:</strong> {alert.reporter}</small>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}

export default App;