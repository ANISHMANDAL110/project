// Firebase configuration and initialization
const firebaseConfig = {
    apiKey: "AIzaSyDIIIbG1db5zPsKXntpJBwWziQdfg18yrs",
    authDomain: "stock-chart-app-42d80.firebaseapp.com",
    databaseURL: "https://stock-chart-app-42d80-default-rtdb.firebaseio.com",
    projectId: "stock-chart-app-42d80",
    storageBucket: "stock-chart-app-42d80.firebasestorage.app",
    messagingSenderId: "270249202899",
    appId: "1:270249202899:web:c294221fa156310a75b026",
    measurementId: "G-ZGCS3LG68T"
};

let database;
let isConnected = false;
let lastLoadTime = 0;
let currentlyLoadingStock = null;

function initializeFirebase() {
    try {
        if (firebase.apps.length === 0) {
            firebase.initializeApp(firebaseConfig);
        }
        database = firebase.database();
        testDatabaseConnection();
    } catch (error) {
        handleConnectionError(error);
    }
}

function testDatabaseConnection() {
    const connectionRef = database.ref('.info/connected');
    const timeout = setTimeout(() => {
        updateStatus('error');
        showTroubleshooting();
    }, 10000);
    connectionRef.on('value', (snapshot) => {
        clearTimeout(timeout);
        if (snapshot.val() === true) {
            isConnected = true;
            updateStatus('connected');
            hideTroubleshooting();
            setTimeout(() => loadAvailableStocks(), 1000);
        } else {
            isConnected = false;
            updateStatus('disconnected');
        }
    }, (error) => {
        clearTimeout(timeout);
        handleConnectionError(error);
    });
}

function handleConnectionError(error) {
    updateStatus('error');
    showTroubleshooting();
}

function updateStatus(status) {
    const statusEl = document.getElementById('status');
    switch (status) {
        case 'connected':
            statusEl.className = 'status connected';
            statusEl.innerHTML = '🟢 Connected to Firebase - Ready to use!';
            break;
        case 'disconnected':
            statusEl.className = 'status disconnected';
            statusEl.innerHTML = '🔴 Disconnected from Firebase - Retrying...';
            break;
        case 'error':
            statusEl.className = 'status disconnected';
            statusEl.innerHTML = '🔴 Connection failed - Check settings below';
            break;
    }
}

function showTroubleshooting() {
    document.getElementById('troubleshootingPanel').style.display = 'block';
}
function hideTroubleshooting() {
    document.getElementById('troubleshootingPanel').style.display = 'none';
}

// Call initializeFirebase on load
window.addEventListener('DOMContentLoaded', initializeFirebase);
