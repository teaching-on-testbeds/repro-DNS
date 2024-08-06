So far, our experiments used a referral response list with 1500 NS names per malicious query (i.e. the referral response delegates the resolution of attack0.home.lan. to 1500 different NS names). We can modify the malicious referral list size, e.g. 100, 500, 1000 records per malicious queries, and test the cost of a malicious query.

To edit the file that generates the referral response, run:
```
sudo nano /env/reproduction/genAttackers.py
```
and change the range in line 6 (`for i in range(1500)`) to your desired value. Write out, exit the editor, and run
```
python /env/reproduction/genAttackers.py
```
to run the updated script that generates the output file `attackerNameServers.txt` with the referral list. Next run
```
cp /env/nsd_attack/home.lan.forward.bak /env/nsd_attack/home.lan.forward
sed -i '/ns2        IN     A    127.0.0.201/r attackerNameServers.txt' /env/nsd_attack/home.lan.forward
```
to update the malicious server zone file with the new referral response list.

You now can perform the instructions measurment experiments again to explore how the cost of a query varies with the number of referrals. Repeat the previous steps to change the number of referrals to another value. 

After you have performed the experiments for different numbers of referrals, you can generate a graphical representation of your data. Create a .py file and copy and paste the following code into the file:
```
import matplotlib.pyplot as plt

# Generate points
x = [0, 100, 500, 1000, 1500] # referral list lengths (modify for your values)
nxns_patched = [] # array for nxns_patched results (nxns_patched[i] is the result for list length x[i])
nxns_unpatched = [] # array for nxns_unpatched results
nrdelegation_patched = [] # array for nrdelegation_patched results

# Adjust figure size
plt.figure(figsize=(6.75, 4.5))

# Plot points
plt.plot(x, nxns_patched, marker='^', linestyle='-', color='b', label = "BIND9 with NXNS patch")
plt.plot(x, nxns_unpatched, marker='o', linestyle='-', color='gray', label = "BIND9 without NXNS patch")
plt.plot(x, nrdelegation_patched, marker='s', linestyle='-', color='green', label = "BIND9 with NRDelegation")

# Label x- and y-axis
plt.xlabel("Number of Referrals", fontdict={'fontname': 'Calibri', 'fontsize': 12}, labelpad=5)
plt.ylabel("Number of Instructions (millions)", fontdict={'fontname': 'Calibri', 'fontsize': 13}, labelpad=3) 

# Set x-axis and y-axis limits and tick marks
plt.xticks(range(0, 1600, 100))
plt.yticks(range(0, 4000, 500))
plt.xlim(0, 1500)
plt.ylim(0, 3500)
plt.tick_params(axis='both', which='both', length=0, pad=10)
for tick in plt.gca().get_xticklabels() + plt.gca().get_yticklabels():
    tick.set_fontname('Calibri')
    tick.set_fontsize(11.5)
    tick.set_fontweight('normal')

# Add grid
plt.grid(True)

# Annotate points 
""" # uncomment to annotate points
for xi, yi in zip(x, nxns_patched):
    if xi != 0 or yi != 0:
        plt.annotate(f'{yi:,}', xy=(xi, yi), xytext=(-5, 5), textcoords='offset points', ha='right', va='bottom', color='black', fontsize=10, fontname='Calibri', bbox=dict(facecolor='white', edgecolor='blue', boxstyle='square', linewidth=0.5, alpha=1.0))

for xi, yi in zip(x, nxns_unpatched):
    if xi != 0 or yi != 0:
        plt.annotate(f'{yi:,}', xy=(xi, yi), xytext=(-5, 5), textcoords='offset points', ha='right', va='bottom', color='black', fontsize=10, fontname='Calibri', bbox=dict(facecolor='white', edgecolor='gray', boxstyle='square', linewidth=0.5, alpha=1.0))

for xi, yi in zip(x, nrdelegation_patched):
    if xi != 0 or yi != 0:
        plt.annotate(f'{yi:,}', xy=(xi, yi), xytext=(5, 5), textcoords='offset points', ha='right', va='bottom', color='black', fontsize=10, fontname='Calibri', bbox=dict(facecolor='white', edgecolor='green', boxstyle='square', linewidth=0.5, alpha=1.0))
"""

# Add legend
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, prop={'family': 'Calibri', 'size': 10})
plt.tight_layout(rect=[0, 0.05, 1, 1])

# Generate
plt.show()
```
