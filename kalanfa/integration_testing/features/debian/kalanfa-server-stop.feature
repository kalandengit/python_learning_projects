Feature: Stopping kalanfa-server service stops kalanfa too
  After kalanfa-server service is stopped, there should not be any kalanfa instances running either. This test should be done in Debian Buster and Ubuntu Bionic.

  Background:
    Given that the kalanfa-server is installed and running

  Scenario: Stop kalanfa-server
    When I run the 'sudo service kalanfa-server stop' command in the Terminal
      And I run 'sudo service kalanfa status'
    Then I see the '...Stopped LSB: kalanfa daemon...' text in the last line of the output
