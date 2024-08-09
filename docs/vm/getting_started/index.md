## Run my experiment using VMs
<!-- Get resources -->
First, reserve your resources. For this experiment, we will use a topology of a 7 nodes&mdash;a malicious client, a benign client, the resolver, two malicious authoritative servers, a benign authoritative server, and a root authoritative server. Your complete topology will be:
<!-- image of topology -->
![vm_topology](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/vm_topology.svg)

To reserve these resources on Cloudlab, open this profile page:
<!-- link to pre-established CloudLab profile -->
[https://www.cloudlab.us/p/nyunetworks/NRDelegationAttack](https://www.cloudlab.us/p/nyunetworks/NRDelegationAttack)

Click "Next", then select the Cloudlab project that you are part of and a Cloudlab cluster with available resources. Then click "Next", and "Finish".

Wait until all of the sources have turned green and have a small check mark in the top right corner of the "Topology View" tab, indicating that they are fully configured and ready to log in. Then, click on "List View" to get SSH login details for the hosts. Use these details to SSH into each.

When you have logged in to each node, continue to the next section to configure your resources.
