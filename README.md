## nebdeb

A automated means to manage nebula host configurations, specifically:

- Building of nebula configurations for hosts.
- Detect when a new host is added and just build a config for that.
- Allow re-building if a new nebula binary is released.
- Build a .deb package for ease of installation/ distribution of config.
- Allow simple method to rebuild everything e.g. in the case a cert is exposed.

### Initial automation flow on program run will be:

1. Check for rebuild flag, if exist purge output and re-generate everything
1. Check for binary hash change, if changed rebuild everything (_retaining existing host certs_)
1. Check for systems csv hash for change, if changed rebuild everything (_retaining existing host certs_)
1. Check for output folder for each system in systems csv, if one doesn't exist genrate for it


### TODO

- Allow tayloring of services, my initial requirement is only fo ssh.
- Allow multiple LightHouses, my initial requirement only has one LightHouse.
- Build an ansible inventory to simplify deployment of the deb.
- I'm very late to the container party but it might be nice to have a container running this that monitors the input and output folders and rebuilds the debs as necessary.