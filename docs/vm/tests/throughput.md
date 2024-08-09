### Throughput measurement experiment
The goal of the attacker during the NRDelegation is to consume resources, preventing the resolver from servicing benign clients. To observe the impact of the attack on victims, you will run two "sub"-experiments.

The first experiment will test the effect of the attack on benign client throughput. Benign and malicious commands will be executed with an instance of the Resperf tool on the respective client. The malicious command will simulate the attacker and issue malicious queries at a fixed rate, while the benign command will issue the benign requests until failure.

The second experiment will test the throughput without any attack. Commands will be executed with the resperf tool on each client, and both the benign and malicious commands will issue benign requests.

In the following tests, the malicious user command should be run first, but ultimately in parallel, to the benign user command. 

SSH into the seven nodes.

From the resolver, run
```
cd bind9
sudo make install
sudo named -g
```
to start BIND9.16.6 (vulnerable to NRDelegationAttack) on the resolver.

For each of the four authoritative servers, run
```
sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db
```
to start NSD on the servers.

From the malicious-client, run
```
resperf -d attackerNames.txt -s 10.0.2.1 -v -m 15000 -c 60 -r 0 -R -P ~/with_attack
```
where `-d attackerNames.txt` is the input file with a list of queries that rely on the malicious referral response, and these queries are sent to the resolver with IP address `-s 10.0.2.1` at a rate of `-m 15000` queries per second, for a duration of `-c 60` seconds, sending the packets in constant time after ramping up for `-r 0`seconds. The output file `with_attack` will show the results of this test.

From the benign-client machine, run
```
resperf -d benignNames.txt -s 10.0.1.1 -v -R -P ~/with_attack
```
where `-d benignNames.txt` is the input file with a list of benign names serviced by the benign-server, `-s 10.0.1.1` is the resolver IP address, and `with_attack` is the output file.

Once the commands have finished executing, stop the resolver (Ctrl + C) in order to clear the cache. Restart the resolver with `named -g`.

Next, to measure the throughput without any attack, "benignNames.txt" will be used as the input file for both commands (no malicious queries will be issued).

From the malicious-client run
```
resperf -d benignNames.txt -s 10.0.2.1 -v -m 15000 -c 60 -r 0 -R -P ~/no_attack
```
and from the benign-client run
```
resperf -d benignNames.txt -s 10.0.1.1 -v -R -P ~/no_attack
```

<!-- Analyze results -->
To view the results, open only the benign-client output files from both sub-experiments (`with_attack` and `no_attack`). Compare the benign user throughput, the "actual_qps" versus the "responses_per_sec" column, between the two tests. In ideal conditions, the responses per second should match the actual queries per second. In real network conditions without any malicious actors, there might be slight variation between queries and responses per second. During the NRDelegationAttack, you should observe a degradation in the resolver throughput for benign clients, indicated by 0 responses per seconds.

The following script can be used to graphically represent your results:
```
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
```

