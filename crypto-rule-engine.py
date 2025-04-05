
# !pip install pycoingecko

from pycoingecko import CoinGeckoAPI
import pandas as pd
import matplotlib.pyplot as plt

# Fetch ETH price & volume
cg = CoinGeckoAPI()
data = cg.get_coin_market_chart_by_id(id='ethereum', vs_currency='usd', days='1')

# Prices
prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')

# Volume
volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
volumes['timestamp'] = pd.to_datetime(volumes['timestamp'], unit='ms')

# Merge both
df = pd.merge(prices, volumes, on='timestamp')
df = df.sort_values(by="timestamp").reset_index(drop=True)

# Detect Anomalies
# Rule 1: Price Spike > 2% in 15 mins (~3 rows at 5-min intervals)
df['price_pct_change'] = df['price'].pct_change(periods=3) * 100
price_spike_flags = df[df['price_pct_change'] > 2.0].copy()
price_spike_flags['rule'] = 'price_spike'

# Rule 2: Volume Spike > 1.5x rolling average
df['volume_avg'] = df['volume'].rolling(window=5).mean()
df['volume_spike'] = df['volume'] > 1.5 * df['volume_avg']
volume_spike_flags = df[df['volume_spike']].copy()
volume_spike_flags['rule'] = 'volume_spike'

# Combine alerts
alerts = pd.concat([price_spike_flags, volume_spike_flags]).sort_values(by="timestamp")
alerts = alerts[['timestamp', 'price', 'volume', 'rule']].drop_duplicates()
alerts.reset_index(drop=True, inplace=True)

## Show flagged alerts
alerts.head()

## Visualize flagged price points
plt.figure(figsize=(14,6))
plt.plot(df['timestamp'], df['price'], label='ETH Price', color='black')

for _, row in alerts.iterrows():
    color = 'red' if row['rule'] == 'price_spike' else 'blue'
    plt.axvline(x=row['timestamp'], color=color, linestyle='--', alpha=0.5, label=row['rule'])

plt.title("ETH Price Anomalies Detected")
plt.xlabel("Time")
plt.ylabel("Price (USD)")
plt.legend()
plt.tight_layout()
plt.show()

alerts.to_csv("eth_alerts.csv", index=False)
