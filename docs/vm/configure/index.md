<!-- Configure resources -->
### Configure resources
In your choice of terminal application, open a window for each of the seven nodes.

#### Client machines
The experiment will use the resperf[4] tool to send queries, both malicious and benign, at a fixed rate and track the response rate from the resolver. SSH into the malicious-client and benign-client nodes and run
```
sudo apt update
sudo apt-get install -y build-essential libssl-dev libldns-dev libck-dev libnghttp2-dev
wget https://www.dns-oarc.net/files/dnsperf/dnsperf-2.8.0.tar.gz
tar xzf dnsperf-2.8.0.tar.gz
cd dnsperf-2.8.0
./configure
make
sudo make install
```
on both client machines to install Resperf.

For the resperf tool, we need to provide input files containing a list of queries. On the malicious-client run
```
cd ~
sudo cp /local/repository/vm_experiment/reproduction/genAttackNamesToCheck.py ~
sudo cp /local/repository/vm_experiment/reproduction/genBenignNamesToCheck.py ~
python genAttackNamesToCheck.py
python genBenignNamesToCheck.py
```
to generate an `attackerNames.txt` file with a list of malicious names and a `benignNames.txt` file with a list of benign names.

And On the benign-client run
```
cd ~
sudo cp /local/repository/vm_experiment/reproduction/genBenignNamesToCheck.py ~
python genBenignNamesToCheck.py
```
to generate the `benignNames.txt` file.

#### Resolver
Next, we will install BIND9[5], an open-source implementation of the DNS protocol, on the resolver. SSH into the resolver node and run
```
git clone -b 9_16_6 https://github.com/ShaniBenAtya/bind9.git 
cd bind9 
sudo apt update 
sudo apt-get install -y python3 python3-ply libuv1-dev pkg-config autoconf automake libtool libssl-dev libcap-dev
autoreconf -fi 
./configure 
make -j 4
sudo make install
```
to install BIND9.16.6. Now provide the necessary directories and configuration files by running:
```
sudo touch /usr/local/etc/named.conf
sudo cp /local/repository/vm_experiment/resolver/named.conf /usr/local/etc/named.conf
sudo touch /usr/local/etc/db.root
sudo cp /local/repository/vm_experiment/resolver/db.root /usr/local/etc/db.root
sudo mkdir -p /usr/local/var/cache/bind
cd /usr/local/etc; sudo rndc-confgen -a
```
You can verify the installation by running `named -v` and should this message:
```
BIND 9.16.6 (Stable Release)
```
We use version 9.16.6 because it is a NXNS-patched version and most vulnerable to the NRDelegationAttack.

#### Authoritative nameservers
The authoritative servers will use Name Server Daemon (NSD), an open-source implementation of an authoritative DNS nameserver. 

To configure the malicious referral authoritative, the authoritative server that responds to queries with the malicious referral response, SSH into the malicious-ref-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_attack/referral.lan.forward /etc/nsd/referral.lan.forward
sudo cp /local/repository/vm_experiment/nsd_attack/referral.lan.reverse /etc/nsd/referral.lan.reverse
sudo cp /local/repository/vm_experiment/nsd_attack/nsd.conf /etc/nsd/nsd.conf
```
to move the zone and configuration files used by NSD into the correct directory. To install NSD on the server, run:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted with the following message:
```
Configuration file '/etc/nsd/nsd.conf'
 ==> File on system created by you or by a script.
 ==> File also in package provided by package maintainer.
   What would you like to do about it ?  Your options are:
    Y or I  : install the package maintainer's version
    N or O  : keep your currently-installed version
      D     : show the differences between the versions
      Z     : start a shell to examine the situation
 The default action is to keep your current version.
*** nsd.conf (Y/I/N/O/D/Z) [default=N] ? N
```
choose "N" to use the configuration file we created in the previous step. After the installation you might get the message:
```
Job for nsd.service failed because the control process exited with error code.
See "systemctl status nsd.service" and "journalctl -xe" for details.
invoke-rc.d: initscript nsd, action "start" failed.
● nsd.service - Name Server Daemon
     Loaded: loaded (/lib/systemd/system/nsd.service; disabled; vendor preset: enabled)
     Active: activating (auto-restart) (Result: exit-code) since Mon 2024-07-29 01:33:39 CDT; 37ms ago
       Docs: man:nsd(8)
    Process: 2126 ExecStart=/usr/sbin/nsd -d (code=exited, status=1/FAILURE)
   Main PID: 2126 (code=exited, status=1/FAILURE)
```
The following steps will handle the error. To finish configuring the server, add the necessary directories and permissions for NSD:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```

To configure the malicious delegation authoritative, the authoritative server that responds to queries with the IP address of a DNS non-responsive server, SSH into the malicious-del-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_attack2/delegation.lan.forward /etc/nsd/delegation.lan.forward
sudo cp /local/repository/vm_experiment/nsd_attack2/delegation.lan.reverse /etc/nsd/delegation.lan.reverse
sudo cp /local/repository/vm_experiment/nsd_attack2/nsd.conf /etc/nsd/nsd.conf
```
to load the zone and configuration files into the correct directory. Next, install Name Server Daemon (NSD) on the server by running:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted about the `etc/nsd/nsd.conf` configuration file, choose 'N' to keep your currently-installed version. Once NSD is installed run:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```
to finish the server configuration.

To configure the benign server, SSH into the benign-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_benign/benign.lan.forward /etc/nsd/benign.lan.forward
sudo cp /local/repository/vm_experiment/nsd_benign/benign.lan.reverse /etc/nsd/benign.lan.reverse
sudo cp /local/repository/vm_experiment/nsd_benign/nsd.conf /etc/nsd/nsd.conf
```
to load the zone and configuration files into the correct directory. Install NSD on the server by running:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted about the `etc/nsd/nsd.conf` configuration file, choose 'N' to keep your currently-installed version. Once NSD is installed run:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```
to finish the server configuration.

And to configure the root server, SSH into the root-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_root/net.forward /etc/nsd/net.forward
sudo cp /local/repository/vm_experiment/nsd_root/net.reverse /etc/nsd/net.reverse
sudo cp /local/repository/vm_experiment/nsd_root/nsd.conf /etc/nsd/nsd.conf
```
to load the zone and configuration files into the correct directory. And install NSD on the server by running:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted about the `etc/nsd/nsd.conf` configuration file, choose 'N' to keep your currently-installed version. Once NSD is installed, run:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```
to finish the server configuration.
