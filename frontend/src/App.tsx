import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import Web3 from 'web3';

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


const contractAddress = '0xa2FC9C6E4A5313F39d27f2a5D1a70bD34bC4c629'; // PASTE YOUR CONTRACT ADDRESS
const ganachePort = 8545;
const backendApiUrl = 'http://localhost:3001/api/log-alert';

// --- Simple Styles ---
// We'll add class names for the animations later
const styles: { [key: string]: React.CSSProperties } = {
    // UPDATED: Main container width to fit layout
    container: { fontFamily: 'Arial, sans-serif', width: '1470px', margin: '20px auto', padding: '20px', backgroundColor: '#000000', color: '#fff' },
    h1: { color: '#240572ff', textAlign: 'center', marginBottom: '30px' }, // Added margin bottom
    h2: { color: '#240572ff', borderBottom: '2px solid #bdc3c7', paddingBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }, // Added margin bottom
    // NEW: Main layout container
    mainLayout: { display: 'flex', gap: '30px' },
    // NEW: Form column style
    formColumn: { flex: '1 1 350px', maxWidth: '350px' }, // Flex basis 350px, max width 350px
    // NEW: Logs column style
    logsColumn: { flex: '2 1 600px', minWidth: '400px' }, // Takes up remaining space, min width 400px

    message: { padding: '12px', borderRadius: '4px', marginTop: '10px', textAlign: 'center', fontWeight: 'bold' },
    error: { background: '#e74c3c', color: 'white', border: '1px solid #c0392b' },
    success: { background: '#2ecc71', color: 'white', border: '1px solid #27ae60' },
    logList: { listStyleType: 'none', padding: '0', maxHeight: '70vh', overflowY: 'auto' }, // Added max height and scroll
    logItem: {
        background: '#000',
        border: '1px solid #fff',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '22px', // Slightly reduced margin
        boxShadow: '0 2px 4px rgba(0,0,0,0.5)',
        transition: 'background-color 0.2s ease-in-out',
        position: 'relative',
        overflow: 'visible'
    },
    logItemHoverSuspicious: { backgroundColor: '#fadbd8', color: '#000' },
    logItemHoverSafe: { backgroundColor: '#d5f5e3', color: '#000' },
    statusText: { fontWeight: 'bold', textTransform: 'uppercase' },
    suspiciousText: { color: '#e74c3c' },
    safeText: { color: '#2ecc71' },
    smallText: { color: '#aaa', fontSize: '0.9em', wordBreak: 'break-all' },
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
    },
    form: { background: '#222', padding: '20px', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }, // Removed margin bottom
    formGroup: { marginBottom: '15px' },
    label: { display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#eee' },
    input: { width: 'calc(100% - 22px)', padding: '10px', border: '1px solid #555', borderRadius: '4px', fontSize: '1rem', backgroundColor: '#444', color: '#fff' },
    textarea: { width: 'calc(100% - 22px)', padding: '10px', border: '1px solid #555', borderRadius: '4px', minHeight: '60px', /* Reduced height */ resize: 'vertical', fontSize: '1rem', backgroundColor: '#444', color: '#fff' },
    button: { background: '#3498db', color: 'white', padding: '12px 20px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold', width: '100%' },
    buttonDisabled: { background: '#bdc3c7', cursor: 'not-allowed' },
};
// --- End Styles ---

// --- CSS Keyframes for Electric Border ---
/*const electricBorderStyles = `
  @keyframes electric-red {
    0% { box-shadow: 0 0 3px 2px rgba(231, 76, 60, 0.7); }
    50% { box-shadow: 0 0 10px 4px rgba(231, 76, 60, 1); }
    100% { box-shadow: 0 0 3px 2px rgba(231, 76, 60, 0.7); }
  }
  @keyframes electric-green {
    0% { box-shadow: 0 0 3px 2px rgba(46, 204, 113, 0.7); }
    50% { box-shadow: 0 0 10px 4px rgba(46, 204, 113, 1); }
    100% { box-shadow: 0 0 3px 2px rgba(46, 204, 113, 0.7); }
  }

  .electric-border-red {
    animation: electric-red 1.5s infinite linear;
  }

  .electric-border-green {
    animation: electric-green 1.5s infinite linear;
  }
`;*/
// --- End Keyframes ---

function App() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [apiError, setApiError] = useState<string | null>(null);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

    // --- Re-added State for the Form ---
    const [newAlertId, setNewAlertId] = useState('');
    const [newSourceType, setNewSourceType] = useState('');
    const [newLogData, setNewLogData] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [apiSuccess, setApiSuccess] = useState<string | null>(null);


    const fetchAlerts = useCallback(async () => {
        console.log("Fetching alerts...");
        // Keep loading true if it's already true (initial load), otherwise just log refresh
        if (!loading) console.log("Refreshing logs...");
        setLoading(true); // Always set loading true during fetch
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
    }, [loading]); // Added loading to dependency array

    useEffect(() => {
        fetchAlerts();
    }, [fetchAlerts]);

    const handleRefresh = () => {
        fetchAlerts();
    };

    // --- Re-added Submit Handler ---
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setApiError(null);
        setApiSuccess(null);

        // CRITICAL VALIDATION: Check if logData looks like the required format
        const logParts = newLogData.trim().split(' ');
        if (logParts.length < 4) { // Needs at least Request_Type, Status_Code, User_Agent, Location
            setApiError("Log Data format seems incorrect. Must be: Request_Type Status_Code User_Agent Location (at least 4 words)");
            setIsSubmitting(false);
            return;
        }

        try {
            const response = await fetch(backendApiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    alertId: newAlertId,
                    sourceType: newSourceType,
                    logData: newLogData
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'API request failed');
            }

            //setApiSuccess(`Success! Log stored. Prediction: ${result.isSuspicious ? 'Suspicious' : 'Safe'} (Tx: ${result.txHash.substring(0, 10)}...)`);
            setNewAlertId('');
            setNewSourceType('');
            setNewLogData('');
            // Refresh the list after a short delay
            setTimeout(fetchAlerts, 1500); // Give blockchain a moment

        } catch (err: any) {
            console.error("Submit Error:", err);
            if (err.message.includes('Failed to fetch')) {
                setApiError('Error: Cannot connect to backend server. Is it running?');
            } else {
                setApiError(err.message || 'An unknown error occurred.');
            }
        }
        setIsSubmitting(false);
    };


    return (
        <div style={styles.container}>

            <h1 style={styles.h1}>Decentralized Intrusion Detection System</h1>

            {/* NEW: Main Layout Div */}
            <div style={styles.mainLayout}>

                {/* --- Form Column --- */}
                <div style={styles.formColumn}>
                    <h2 style={{...styles.h2}}>Submit New Log</h2>
                    <form onSubmit={handleSubmit} style={styles.form}>
                        <div style={styles.formGroup}>
                            <label htmlFor="alertId" style={styles.label}>Alert ID</label>
                            <input
                                type="text"
                                id="alertId"
                                style={styles.input}
                                value={newAlertId}
                                onChange={(e) => setNewAlertId(e.target.value)}
                                placeholder="e.g., ALERT-700"
                                required
                            />
                        </div>
                        <div style={styles.formGroup}>
                            <label htmlFor="sourceType" style={styles.label}>Source Type</label>
                            <input
                                type="text"
                                id="sourceType"
                                style={styles.input}
                                value={newSourceType}
                                onChange={(e) => setNewSourceType(e.target.value)}
                                placeholder="e.g., Firewall, WebApp, API"
                                required
                            />
                        </div>
                        <div style={styles.formGroup}>
                            <label htmlFor="logData" style={styles.label}>Log Data</label>
                            <textarea
                                id="logData"
                                style={styles.textarea}
                                value={newLogData}
                                onChange={(e) => setNewLogData(e.target.value)}
                                placeholder="CRITICAL: Must match model format, e.g., 'POST 404 Scraper Russia'"
                                required
                            />
                        </div>

                        {/* Display submit errors/success within the form */}
                        {apiError && isSubmitting && <div style={{ ...styles.message, ...styles.error }}>{apiError}</div>}
                        {apiSuccess && <div style={{ ...styles.message, ...styles.success }}>{apiSuccess}</div>}


                        <button
                            type="submit"
                            style={isSubmitting ? { ...styles.button, ...styles.buttonDisabled } : styles.button}
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? 'Submitting...' : 'Analyze & Store'}
                        </button>
                    </form>
                </div>
                {/* --- End Form Column --- */}


                {/* --- Logs Column --- */}
                <div style={styles.logsColumn}>
                    {/* Display blockchain connection error if it occurs */}
                    {apiError && !isSubmitting && <div style={{ ...styles.message, ...styles.error, marginBottom: '20px' }}>{apiError}</div>}

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
                {/* --- End Logs Column --- */}

            </div> {/* End Main Layout Div */}
        </div>
    );
}

export default App;