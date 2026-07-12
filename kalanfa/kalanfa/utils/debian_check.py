import getpass
import os
import sys
from builtins import input
from shutil import rmtree

from .conf import KALANFA_HOME
from .server import installation_type


def check_debian_user(noinput=False):
    """
    A user account is selected to run the system service during the initial setup
    of the Debian package installation. This function checks whether the current
    user who tries to run Kalanfa is the user account set in the configuration.
    Users are free to choose whether they want to continue as the current user even
    if it is not the user defined in the configuration.
    """
    if noinput:
        return

    # Check if Kalanfa is installed through the Kalanfa Debian package or kalanfa-server
    # Debian package
    install_type = installation_type()
    if install_type not in ["dpkg", "apt"] and not install_type.startswith("kalanfa"):
        return

    with open("/etc/kalanfa/username", "r") as f:
        kalanfa_user = f.read().rstrip()

    current_user = getpass.getuser()

    # If kalanfa user does not exist or is the same as the current user, then do not
    # prompt the user with the warning.
    if not kalanfa_user or kalanfa_user == current_user:
        return

    # If the database file exists in the KALANFA_HOME directory, then kalanfa was
    # started with the current user before. There is no need to prompt the user
    # with the warning.
    if os.path.exists(os.path.join(KALANFA_HOME, "db.sqlite3")):
        return

    sys.stderr.write(
        (
            "You are running this command as the user '{current_user}', "
            "but Kalanfa was originally installed to run as the user '{kalanfa_user}'.\n"
            "This may result in unexpected behavior, "
            "because the two users will each use their own local databases and content.\n\n"
        ).format(current_user=current_user, kalanfa_user=kalanfa_user)
    )
    sys.stderr.write(
        (
            "If you'd like to run the command as '{}', you can try:\n\n"
            "    sudo su {} -c '<command>'\n\n"
        ).format(kalanfa_user, kalanfa_user)
    )
    cont = input(
        "Alternatively, would you like to continue and "
        "run the command as '{}'? [y/N] ".format(current_user)
    )
    if not cont.strip().lower() == "y":
        # Remove the previously created KALANFA_HOME directory
        rmtree(KALANFA_HOME)
        sys.exit(0)
