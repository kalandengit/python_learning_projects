Feature: Clean uninstall of kalanfa-server
  Kalanfa needs to continue running after kalanfa-server has been uninstalled. This test should be done in Debian Buster and Ubuntu bionic.

  Background:
    Given that kalanfa-server is installed and running

  Scenario: Uninstall kalanfa-server
    When I run the 'apt remove kalanfa-server' command in the Terminal
	  And the command prompt appears again
    Then I still can access Kalanfa in the browser
      And the file /etc/nginx/conf.d/kalanfa.conf does not exist
      And the folder /etc/kalanfa/nginx.d does not exist
