 Feature: Debian/Ubuntu app installation
  A user needs to be able to install Kalanfa on a supported Debian/Ubuntu device

  Background:
    Given that I have downloaded the kalanfa .deb file on a supported Debian/Ubuntu device

  Scenario: Install Kalanfa from a .deb file
    When I run the *sudo dpkg -i kalanfa-installer-filename.deb* command from the location where I have downloaded the .deb file
    Then I see that the installation is in progress
    When the installation has finished
    	And I run the *kalanfa start* command
    	And I open the default browser at http://127.0.0.1:8080
    Then I see the first step of the *Setup wizard*
