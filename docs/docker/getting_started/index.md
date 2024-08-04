## Run my experiment using Docker containers
<!-- Get resources -->
This experiment will measure the cost of a malicious NRDelegationAttack query in instructions executed on the resolver CPU. For this experiment, we will use a topology of a single node:

![docker_ex_topology](https://github.com/user-attachments/assets/e29def83-8bc5-4d78-b17c-29d7ecdb7a1d)

Open this profile page: [https://www.cloudlab.us/p/PortalProfiles/small-lan](https://www.cloudlab.us/p/PortalProfiles/small-lan) 
Click "Next", then choose 1 node, select UBUNTU 20.04 as the disk image, and check the box for "Start X11 VNC on your nodes".
![Screenshot 2024-08-04 184446](https://github.com/user-attachments/assets/608e65d3-8f67-4ad6-8f66-9d66110f497d)
Click "Next", then select the Cloudlab project that you are part of and a Cloudlab cluster with available resources. Click "Next" and then "Finish".

It will take a few minutes for your resources to be allocated. Wait until the node has turned green with a check mark in the upper right corner in the "Topology View" tab signaling that your node is ready for you to log in. Then, click on "List View" to get SSH login details for the host. Use these details to SSH into the node.

When you have logged in to each node, continue to the next section to configure your resources.
