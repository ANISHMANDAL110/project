// Firebase data loading, storing, and stock list logic
// Assumes database and isConnected are set in firebase-config.js

function storeStockData(symbol, dataPoints) {
    if (!database || !isConnected) {
        alert('❌ Database not connected. Please check your Firebase setup.');
        return;
    }
    try {
        const ref = database.ref(`stocks/${symbol}`);
        ref.remove().then(() => {
            const minimalPoints = dataPoints.map(d => ({ date: d.date, price: d.price }));
            const promises = minimalPoints.map(dataPoint => ref.push(dataPoint));
            Promise.all(promises).then(() => {
                alert(`✅ Sample data generated for ${symbol}!`);
                loadAvailableStocks();
                const currentSymbol = document.getElementById('stockSelect').value;
                if (currentSymbol === symbol) {
                    setTimeout(() => loadStockData(symbol, true), 500);
                }
            }).catch((error) => {
                alert('Failed to store data: ' + error.message);
            });
        }).catch((error) => {
            alert('Failed to clear old data: ' + error.message);
        });
    } catch (error) {
        alert('Database connection error: ' + error.message);
    }
}

function loadStockData(symbol, forceReload = false, model = 'prophet') {
    if (!database || !isConnected || !symbol) {
        console.error('❌ Database not connected or symbol missing');
        return;
    }
    const now = Date.now();
    if (!forceReload && (currentlyLoadingStock === symbol || (now - lastLoadTime) < 1000)) {
        return;
    }
    currentlyLoadingStock = symbol;
    lastLoadTime = now;
    try {
        const ref = database.ref(`stocks/${symbol}`);
        ref.once('value', (snapshot) => {
            const data = [];
            if (snapshot.exists()) {
                // Handle both array and object (date-keyed) data
                snapshot.forEach((child) => {
                    const val = child.val();
                    // If val has no date, use the key as date
                    if (val && val.price !== undefined && !val.date) {
                        data.push({ date: child.key, price: val.price, id: child.key });
                    } else {
                        data.push({ date: val.date, price: val.price, id: child.key });
                    }
                });
            }
            const sortedData = data.sort((a, b) => {
                // If timestamp exists, sort by it, else by date string
                if (a.timestamp && b.timestamp) return a.timestamp - b.timestamp;
                if (a.date && b.date) return new Date(a.date) - new Date(b.date);
                return 0;
            });
            // Use the selected model for predicted data (dashes, not underscores)
            const predRef = database.ref(`predicted_stocks/${symbol}-${model}`);
            predRef.once('value', (predSnap) => {
                const predData = [];
                if (predSnap.exists()) {
                    predSnap.forEach((child) => {
                        const val = child.val();
                        // If val has no date, use the key as date
                        if (val && val.price !== undefined && !val.date) {
                            predData.push({ date: child.key, price: val.price, id: child.key });
                        } else {
                            predData.push({ date: val.date, price: val.price, id: child.key });
                        }
                    });
                }
                let merged = sortedData.slice();
                if (predData.length > 0) {
                    const lastReal = merged.length > 0 ? merged[merged.length-1] : null;
                    let lastTimestamp = lastReal && lastReal.timestamp ? lastReal.timestamp : Date.now();
                    predData.forEach((p, idx) => {
                        if (!p.timestamp && p.date) {
                            p.timestamp = new Date(p.date).getTime();
                        }
                        if (p.price === undefined && p.Forecasted_Price !== undefined) {
                            p.price = parseFloat(p.Forecasted_Price);
                        }
                        if (!p.price && p.price !== 0 && p.Forecasted_Price) {
                            p.price = parseFloat(p.Forecasted_Price);
                        }
                        if (!p.price && p.price !== 0 && p.predicted_price) {
                            p.price = parseFloat(p.predicted_price);
                        }
                        if (!p.timestamp) {
                            lastTimestamp += 86400000;
                            p.timestamp = lastTimestamp;
                        }
                    });
                    merged = merged.concat(predData);
                }
                updateChart(symbol, merged);
                currentlyLoadingStock = null;
            });
        }).catch((error) => {
            currentlyLoadingStock = null;
        });
    } catch (error) {
        currentlyLoadingStock = null;
    }
}

function loadAvailableStocks() {
    if (!database || !isConnected) {
        return;
    }
    const stockSelect = document.getElementById('stockSelect');
    const currentValue = stockSelect.value;
    try {
        const stocksRef = database.ref('stocks');
        stocksRef.once('value', (snapshot) => {
            const stocks = [];
            if (snapshot.exists()) {
                snapshot.forEach((child) => {
                    stocks.push(child.key);
                });
                stocks.sort();
                stockSelect.innerHTML = '';
                if (stocks.length === 0) {
                    addDefaultStockOptions(stockSelect);
                } else {
                    stocks.forEach(symbol => {
                        const option = document.createElement('option');
                        option.value = symbol;
                        option.textContent = symbol;
                        if (symbol === currentValue) {
                            option.selected = true;
                        }
                        stockSelect.appendChild(option);
                    });
                }
            } else {
                addDefaultStockOptions(stockSelect);
            }
        }).catch((error) => {
            addDefaultStockOptions(stockSelect);
        });
    } catch (error) {
        addDefaultStockOptions(stockSelect);
    }
}

function addDefaultStockOptions(selectElement) {
    const defaultStocks = [
        { value: 'AAPL', text: 'Apple (AAPL)' },
        { value: 'GOOGL', text: 'Google (GOOGL)' },
        { value: 'MSFT', text: 'Microsoft (MSFT)' },
        { value: 'TSLA', text: 'Tesla (TSLA)' },
        { value: 'RELIANCE', text: 'Reliance (RELIANCE)' },
        { value: 'TCS', text: 'TCS (TCS)' },
        { value: 'INFY', text: 'Infosys (INFY)' },
        { value: 'NABIL', text: 'NABIL Bank (NABIL)' },
        { value: 'ADBL', text: 'Agriculture Development Bank (ADBL)' }
    ];
    selectElement.innerHTML = '';
    defaultStocks.forEach(stock => {
        const option = document.createElement('option');
        option.value = stock.value;
        option.textContent = stock.text;
        selectElement.appendChild(option);
    });
}
