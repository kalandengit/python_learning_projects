 Feature: MacOS app installation
  A user needs to be able to install Kalanfa on a supported MacOS device

  Background:
    Given that I have downloaded the kalanfa-0.19.dmg file on a supported MacOS device

  Scenario: Mac app installation
  	Given that the kalanfa app is not installed and running (not intended for use as a server).
  	When I download the .dmg installer for Kalanfa
    	And I double-click the downloaded *.dmg* file
    Then I see a new window open
    When I drag the app icon to the Applications folder icon in that window
    Then I see the *Copying "Kalanfa" to Applications* progress bar
    When the copying process has finished
    	And I click the *Launchpad*
    Then I see the *Kalanfa* icon
    When I click the *Kalanfa* icon
    Then I see a *Starting Kalanfa* screen
    	And I see the first step of the installation wizard
