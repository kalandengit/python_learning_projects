Feature: Super admin can see error logs during a failed Windows installer setup
  Super admin needs to be able to see the error logs when the Kalanfa Windows installation fails

  Background:
    Given I am installing Kalanfa on Windows OS
      And I double click the Kalanfa Windows installer

  Scenario: Kalanfa Windows installer exits with an error
    When I see the setup message that Python is required to install
      And I click "Yes" to install Python
    Then I see the Python is installing
      And I manually delete or rename the "pip.exe" in the "C:\Python36\Script" path
      And I continue the Kalanfa installation
    Then I see a Kalanfa error message
    When I click the 'Kalanfa-setup.log' link
    Then I see the installation error log file
