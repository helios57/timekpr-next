# Timekpr-nExT

## Keep Control of Computer Usage

Timekpr-nExT is a simple, robust, and easy-to-use screen time managing application. It helps optimize and limit time spent on computers for children, subordinates, or yourself.

**NEW: Multi-Device Syncing**: Need to synchronize time limits seamlessly across multiple computers or coordinate overlapping users? Check out the new [Timekpr-Next Delta Sync Server](sync-server/README.md) integration!

---

## Features

* **Precise Time Accounting**: Accounts time every 3 seconds (configurable). Intelligently stops accounting when the screen is locked, the screensaver is active, or the computer is suspended.
* **Flexible Limits**: 
  * Set daily, weekly, and monthly time allowances.
  * Define specific allowed time intervals per day (e.g., allow usage only between 09:00 and 18:00).
* **PlayTime Mode**: Limit the usage of specific applications or games based on process names or RegExp masks (e.g., restrict Steam or Minecraft to 1 hour, without limiting total computer usage).
* **"Freeride" Intervals**: Allow usage during specific time intervals without deducting from the global time limit (e.g., for mandatory school work or online classes).
* **Multiple Restriction Types**: Choose what happens when limits run out:
  * *Terminate Sessions* (Log out)
  * *Kill Sessions* (Force log out)
  * *Lock Screen*
  * *Suspend Computer*
* **Configurable Notifications**: Inform users of remaining time before restrictions are applied. Users can tailor their own notification preferences so they are always aware of approaching limits.

---

## Installation

Timekpr-nExT consists of three components: a persistent background daemon, a client indicator icon, and an administration control panel.

| OS / Distribution | Install | Remove |
| :--- | :--- | :--- |
| **Ubuntu / Mint / Pop!_OS** <br>*(via PPA)* | `sudo add-apt-repository ppa:mjasnik/ppa`<br>`sudo apt update`<br>`sudo apt install timekpr-next` | `sudo apt remove --purge timekpr-next` |
| **Debian** | `sudo apt update`<br>`sudo apt install timekpr-next` | `sudo apt remove --purge timekpr-next` |
| **ArchLinux / Manjaro** <br>*(via AUR)* | `yay -S timekpr-next` | `sudo pacman -Rdd timekpr-next` |

*(For Fedora, openSUSE, and manual installation, please refer to your distribution's community repositories).*

**Note:** After installation, a system restart or a full log out/in is highly recommended to properly launch the daemon and the client indicator.

---

## Usage Guide

### Administration Panel
Launch the **(SU) Timekpr-nExT Control Panel** from your application menu. You will need superuser (`sudo`) privileges.
If you prefer password-less access, add your administration user to the `timekpr` system group (`sudo gpasswd -a $USER timekpr`) and restart your session.

#### Managing Users
Select a user from the dropdown menu to configure their limits:
* **Info & Today**: Track time spent and add/subtract temporary time rewards or penalties.
* **Limit Configuration**: Configure which days the user can log in, set daily time allowances, and define specific hour intervals during which usage is allowed. E.g., allow 2 hours between 14:00 and 20:00.
* **PlayTime**: Enable enhanced process monitoring to limit specific applications without limiting overall computer usage.
* **Additional Options**: Configure what happens when time runs out (Log Out, Lock, Suspend) and toggle session tracking mechanisms.

### Client Application
Users can view their current status, limits, and PlayTime allowances by clicking the **Timekpr-nExT indicator icon** in the system tray. Users can adjust their own notification settings to warn them when they are about to run out of time (e.g. at 10 minutes left).

*Note: On GNOME 3 Desktop Environments, you may need to install the [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/) extension for the system tray icon to appear.*

---

## Command Line Interface (CLI)

Timekpr-nExT can be fully managed directly from the terminal. This allows easy integration into other scripts and headless server management.

Use `sudo timekpra --help` for an introduction to the administration CLI.

---

## Troubleshooting & Quirks

Because of the diverse Linux ecosystem, Timekpr-nExT operates differently depending on your Desktop Environment (DE).

* **Screen Locking**: Some DEs require the screen to be turned off completely before the session is considered "inactive".
* **Session Termination**: If user sessions don't successfully terminate to the login screen (resulting in a blank screen with a cursor), try changing the restriction type from `Terminate Sessions` to `Kill Sessions`.
* **Sound Notifications**: Bell notifications can occasionally override OS notification bubbles; check the configuration if critical popups aren't appearing.

For full technical logs, view `/var/log/timekpr.log`. You can adjust the logging verbosity level in the *Timekpr-nExT Configuration* tab.

---

## Support and Contributions

Timekpr-nExT is completely free and open source. If you appreciate the software or it brings value to your family, please consider supporting its ongoing development, features, and maintenance!

* **PayPal**: [Donate Here](https://tinyurl.com/yc9x85v2)
* **Bitcoin**: `bc1q57wapz6lxfyxex725x3gs7nntm3tazw2n96nk3`

If you encounter issues or have feature suggestions, please visit the [Launchpad Project Page](https://bugs.launchpad.net/timekpr-next) to file a bug report or ask a question.
