import { useState, useEffect } from 'react';
import Web3 from 'web3';
import IDSLogsContract from './IDSLogs.json';

// Define a TypeScript interface for the Alert data structure
interface Alert {
    alertId: string;
    sourceType: string;
    logData: string;
    timestamp: bigint; // BigInt is the correct type for Solidity's uint256
    reporter: string;
    isSuspecious: boolean;
}

const contractAddress = '0xB1d0BE6166C64A980a12957C7cBfF33D1481649d'; // PASTE OUR CONTRACT ADDRESS HERE
const ganachePort = 8545;

function App() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                const web3 = new Web3(`http://127.0.0.1:${ganachePort}`);
                const idsLogsContract = new web3.eth.Contract(
                    IDSLogsContract.abi,
                    contractAddress
                );

                // This is the key line to verify
                const alertCount = await idsLogsContract.methods.getAlertsCount().call();

                // ADD THIS LOG: This will tell us if your frontend sees any alerts.
                console.log("Alert count from blockchain:", String(alertCount));

                const fetchedAlerts: Alert[] = [];
                // The Number() conversion is important here for the loop
                for (let i = 0; i < Number(alertCount); i++) {
                    const alert = await idsLogsContract.methods.alerts(i).call() as Alert;
                    fetchedAlerts.push(alert);
                }

                setAlerts(fetchedAlerts);
                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch alerts:', error);
                setLoading(false);
            }
        };

        fetchAlerts();
    }, []);

    if (loading) {
        return <div>Loading alerts...</div>;
    }

    return (
        <div className="App">
            <h1>Blockchain-based IDS Logs</h1>
            {alerts.length > 0 ? (
                <ul>
                    {alerts.map((alert, index) => (
                        <li key={index}>
                            <strong>ID:</strong> {alert.alertId}<br />
                            <strong>Source:</strong> {alert.sourceType}<br />
                            <strong>Data:</strong> {alert.logData}<br />
                            <strong>Status:</strong> {alert.isSuspecious ? '🔴 SUSPICIOUS' : '🟢 SAFE'}<br />
                            <strong>Timestamp:</strong> {new Date(Number(alert.timestamp) * 1000).toLocaleString()}<br />
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No alerts found on the blockchain.</p>
            )}
        </div>
    );
}

export default App;