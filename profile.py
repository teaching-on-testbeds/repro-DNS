"""For reproducing NRDelegationAttack"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal object,
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Node benign-client
node_benign_client = request.XenVM('benign-client')
node_benign_client.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD'
iface0 = node_benign_client.addInterface('interface-0', pg.IPv4Address('10.0.1.100','255.255.255.0'))

# Node malicious-client
node_malicious_client = request.XenVM('malicious-client')
node_malicious_client.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD'
iface1 = node_malicious_client.addInterface('interface-2', pg.IPv4Address('10.0.2.200','255.255.255.0'))

# Node resolver
node_resolver = request.XenVM('resolver')
node_resolver.routable_control_ip = True
node_resolver.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD'
iface2 = node_resolver.addInterface('interface-1', pg.IPv4Address('10.0.1.1','255.255.255.0'))
iface3 = node_resolver.addInterface('interface-3', pg.IPv4Address('10.0.2.1','255.255.255.0'))
iface4 = node_resolver.addInterface('interface-res', pg.IPv4Address('10.0.0.1','255.255.255.0'))
node_resolver.startVNC()

# Node malicious-ref-server
node_malicious_ref_server = request.XenVM('malicious-ref-server')
node_malicious_ref_server.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD'
iface5 = node_malicious_ref_server.addInterface('interface-mal-ref', pg.IPv4Address('10.0.0.200','255.255.255.0'))

# Node root-server
node_root_server = request.XenVM('root-server')
node_root_server.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD'
iface6 = node_root_server.addInterface('interface-root-ser', pg.IPv4Address('10.0.0.101','255.255.255.0'))

# Node benign-server
node_benign_server = request.XenVM('benign-server')
node_benign_server.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD'
iface7 = node_benign_server.addInterface('interface-ben-ser', pg.IPv4Address('10.0.0.100','255.255.255.0'))

# Node malicious-del-server
node_malicious_del_server = request.XenVM('malicious-del-server')
node_malicious_del_server.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD'
iface8 = node_malicious_del_server.addInterface('interface-mal-del', pg.IPv4Address('10.0.0.201','255.255.255.0'))

# Link link-1
link_1 = request.Link('link-1')
link_1.addInterface(iface0)
link_1.addInterface(iface2)

# Link link-2
link_2 = request.Link('link-2')
link_2.addInterface(iface1)
link_2.addInterface(iface3)

# Link link-0
link_0 = request.Link('link-0')
link_0.addInterface(iface4)
link_0.addInterface(iface5)
link_0.addInterface(iface6)
link_0.addInterface(iface7)
link_0.addInterface(iface8)


# Print the generated rspec
pc.printRequestRSpec(request)
