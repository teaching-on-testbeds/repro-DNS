import matplotlib.pyplot as plt
import pandas as pd
import io

# Insert your with_attack outfile data
with_attack = """ 
time target_qps actual_qps responses_per_sec failures_per_sec avg_latency connections conn_avg_latency

"""
# Insert your no_attack outfile data
no_attack = """
time target_qps actual_qps responses_per_sec failures_per_sec avg_latency connections conn_avg_latency

"""

with_attack = pd.read_csv(io.StringIO(with_attack), sep='\s+')
no_attack = pd.read_csv(io.StringIO(no_attack), sep='\s+')

# Plot points
plt.figure(figsize=(10, 5))
plt.scatter(with_attack['time'], with_attack['actual_qps'], label='actual_qps with attack', marker='o', color='lightblue')
plt.scatter(with_attack['time'], with_attack['responses_per_sec'], label='responses_per_sec with attack', marker='x', color = 'red')
plt.scatter(no_attack['time'], no_attack['actual_qps'], label='actual_qps no attack', marker='o', color='lightblue')
plt.scatter(no_attack['time'], no_attack['responses_per_sec'], label='responses_per_sec no attack', marker='x', color = 'green')

plt.title('Throughput comparison with and without NRDelegationAttack')
plt.xlabel('Time (seconds)')
plt.ylabel('Queries/Responses per Second')
plt.legend()
plt.grid(True)
plt.xticks(with_attack['time'])

plt.show()

