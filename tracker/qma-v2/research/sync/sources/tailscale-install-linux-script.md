<!-- Source: https://tailscale.com/kb/1031/install-linux
     Fetched: 2026-10-28. Text extracted from the HTML page (markup, scripts and navigation removed). -->

Install Tailscale on Linux · Tailscale Docs

See everything you missed at TailscaleUp.Read the recap →
- 
- 
- 
- 

- 

- 
- 
- 
- 
- 
- 
- 

- 
- 
- 
- 
- 
- 
- 

- 

- 
- 
- 
- 
- 
- 
- 
- 

- 
- 
- 
- 
- 

- 
- 
- 
- 

- 
- 
- 

- 
- 
- 
- 

- 

- 
- 
- 
- 
- 
- 
- 

- 
- 
- 
- 

- 
- 
- 
- 
- 
- 
- 

- 
- 
- 
- 
- 
- 
- 

- 
- 
- 
- 
- 
- 
- 

- 
- 
- 
- 

- 
- 
- 
- 

- 
- 
- 

- 
- 
- 
- 

- 
- 
- 
- 
- 
- 

- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

- 
- 
- 

### DocumentationClose navigation

- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

# Install Tailscale on Linux
Last validated: Jan 5, 2026|Copy as Markdown|View as Markdown

You can install the Tailscale client on a variety of Linux distributions using either our automated install script or distribution-specific package managers. This topic covers both mainstream distributions and those with alternative package management systems.

## Mainstream distributions

If you're installing the client on a distribution of Linux that contains a package manager such as apt, yum, or zypper, run the following command:

curl -fsSL https://tailscale.com/install.sh | sh

This is the same script available on our Download page. If you prefer not to use curl | sh, visit the Tailscale Packages - stable track page for manual installation instructions for your distribution.

After installation completes, start the Tailscale client:

sudo tailscale up

The output will display a URL that you can use to authenticate to your Tailscale network (known as a tailnet). After you authenticate, check the Machines page of the admin console to confirm the device appears in your tailnet.

This method works on the following distributions:

- Ubuntu-based distributions

- Debian-based distributions

- Red Hat Enterprise Linux (RHEL), CentOS, Fedora, and derivatives

- Raspberry Pi OS

- Amazon Linux

- openSUSE and SUSE Linux Enterprise

- Oracle Linux

- VMware Photon OS

For detailed list of version-specific instructions for supported platforms, refer to the Tailscale Packages - stable track page.

If there is a distribution that you would like us to officially support, contact Tailscale Support so that we can consider adding official support for the distribution.

## Other distributions

You can install the Tailscale client on distributions with alternative package managers.

- Arch Linux

- NixOS

## Static binaries

For other Linux distributions not covered by the install script, we provide static binaries as an alternative.

To install a static binary version of the Tailscale client:

- 

Download the static binaries for your CPU architecture.

- 

Unpack the archive:

tar xvf tailscale_<version>_<architecture>.tgz

For example, if you've downloaded version 1.90.6 of the Tailscale client for AMD64, the command is tar xvf tailscale_1.90.6_amd64.tgz.

- 

Start tailscaled daemon:

sudo tailscaled --state=tailscaled.state

If you want to configure systemd to run tailscaled automatically, a service configuration is available in the systemd/ subdirectory of the unpacked archive.

- 

Start the Tailscale client:

sudo tailscale up

The output will display a URL that you can use to authenticate to your tailnet. After you authenticate, check the Machines page of the admin console to confirm the device appears in your tailnet.

## Verify the installation

When you add a machine to a tailnet, it's assigned a Tailscale IPv4 and IPv6 address. This helps other machines, nodes, and devices know how to reach it over the secure tailnet.

To display the Tailscale IPv4 and IPv6 addresses for your device, run:

tailscale ip

Check the connection status:

tailscale status

## Further exploration

### Disable key expiry

Devices in a tailnet periodically re-authenticate to stay secure through device key expiry, which requires re-authentication after a set period. For devices that should remain continuously connected, such as servers, Raspberry Pis, media centers, smart home hubs, Docker hosts, and NAS devices, you can disable key expiry to avoid any unnecessary disruptions.

To disable key expiry for a device, go to the Machines page of the admin console, select the icon next to the device, then select Disable key expiry.

Disabling key expiry reduces security and can expose your network if the device or key is compromised. Only do this for trusted devices and revoke the key immediately if the device is lost or replaced. For more information, refer to Key expiry.

If your device's key is already expired, you can use the following command to force re-authentication:

sudo tailscale up --force-reauth

### Use Tailscale SSH

Tailscale SSH lets you manage SSH access to your machine, secure SSH access through your tailnet without exposing SSH to the public internet.

You can enable Tailscale SSH on your machine by running the following:

tailscale set --ssh

### Install unstable versions

We offer unstable versions of the Tailscale client for users who want to test new features and fixes before they're distributed to the wider community. If you'd like to help test new features, you can download and install unstable clients from the Tailscale Packages - unstable track page.

For more information, refer to Tailscale client versions and release tracks.

## Troubleshooting

### Issues using the install script

If the install script fails, it displays diagnostic output information in the terminal session. Include this output when contacting our support team.

### Missing kernel modules

Tailscale requires the tun kernel module. Most distributions include this by default. If you encounter errors about missing tun, load it manually:

sudo modprobe tun

To load it automatically on boot, add tun to /etc/modules or /etc/modules-load.d/tun.conf.

### Disable logging

By default, Tailscale sends logs to Tailscale servers about device connectivity to a tailnet. We use this data to diagnose and troubleshoot issues when users reach out to Tailscale with an issue. To disable logging:

Edit /etc/default/tailscaled and add:

TS_NO_LOGS_NO_SUPPORT=true

Or add --no-logs-no-support to the FLAGS variable.

Disabling logs may prevent Tailscale from providing technical support.

On this page
- Mainstream distributions
- Other distributions
- Static binaries
- Verify the installation
- Further exploration
- Disable key expiry
- Use Tailscale SSH
- Install unstable versions
- Troubleshooting
- Issues using the install script
- Missing kernel modules
- Disable logging
Scroll to top

### 
- 
- 
- 
- 

### 
- 
- 
- 
- 
- 
- 

### 
- 
- 
- 
- 
- 
- 

### 
- 
- 
- 
- 
- 
- 
-
