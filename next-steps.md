Verify that VNC on Cloudlab "resolver" node is working. Alternatively modify instructions to install KCachegrind and `scp` the files on the personal computer. 

CPU instructions measurements on the VM setup do not match the claims/docker experiment results. The function call (`fctx_getaddresses`) that is of interest is not shown as being called in the KCachegrind results for the BIND 9.16.33 test (the version with NRDelegation mitigation). The NXNS-patched version (BIND 9.16.6) does perform worse than the the unpatched (BIND 9.16.2) but the number of instructions is still in the hundreds of millions (~300) not the expected >2 billion.

For the scripts to graphically visualize the various results the necessary software dependencies are Python and Matplotlib (and VNC if using VM rather than personal computer).
