## nebdeb

A automated means to manage nebula host configurations, specifically:

- Building of nebula configurations for hosts.
- Detect when a new host is added and just build a config for that.
- Allow re-building if a new nebula binary is released.
- Build a .deb package for ease of installation/ distribution of fully configured installation.
- Allow a simple method to rebuild everything e.g. in the case a cert is or expires.

### Initial automation flow on program run will be:

1. Check for `purgeall` flag, if exist purge the output directory and re-generate everything.
1. Check for binary hash change, if changed rebuild everything (_retaining existing host certs_)
1. Check for systems csv hash for change, if changed rebuild everything (_retaining existing host certs_)
1. Check for output folder for each system in systems csv, if one doesn't exist build it.
1. Run the scrip in a Docker container, ensures availability at any time.

### TODO

- Allow selection of services, initial requirement is only for ssh.
- Allow multiple LightHouses, initial requirement only has one LightHouse.