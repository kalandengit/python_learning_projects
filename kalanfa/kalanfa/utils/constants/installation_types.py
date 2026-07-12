"""
This module contains constants representing the type of "installers" used to install Kalanfa.
"""

APK = "apk"
DEB = "deb"
FLATPAK = "flatpak"
GNOME = "gnome"
KALANFA_SERVER = "kalanfaserver"
MACOS = "mac"
PEX = "pex"
WHL = "whl"
WINDOWS = "windows"
WINDOWS_APP = "windowsapp"

install_type_map = {
    APK: "apk - {}",
    DEB: "deb kalanfa - {}",
    FLATPAK: "Flatpak - {}",
    GNOME: "GNOME - {}",
    KALANFA_SERVER: "deb kalanfa-server - {}",
    MACOS: "Mac - {}",
    PEX: "pex",
    WHL: "whl",
    WINDOWS: "Windows - {}",
    WINDOWS_APP: "Windows App - {}",
}
