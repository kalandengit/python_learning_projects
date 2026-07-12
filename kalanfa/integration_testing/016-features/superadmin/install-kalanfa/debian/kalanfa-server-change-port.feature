Feature: kalanfa-server manages ports correctly
  If the user changes the port after installing kalanfa-server, those changes must be applied upon restart. This test should be done in Debian Buster and Ubuntu bionic.

  Background:
    Given that the kalanfa-server is installed and running

  Scenario: Change Kalanfa port
    When I edit the file '~/.kalanfa/options.ini' to change the HTTP_PORT option to one of the allowed options: 80, 8008 or 8080
      And I restart kalanfa-server
      And I reload the browser with the new port
    Then I see Kalanfa running with the new port
