Feature: Load Kalanfa with content fallback directories
	Kalanfa users should see content in any content fallback directories that have been specified.

# KALANFA_CONTENT_FALLBACK_DIRS is a semi-colon (;) separated list of directories that contain directories with Kalanfa content. This is used for distributions like Endless to provide system content packages that are automatically loaded on first start-up.

# Follow the steps in the 'Background' to  prepare the VM

	Background:
		Given that there is an 'options.ini' file in the Kalanfa home folder
			And that there is a '[Paths]' section in the 'options.ini' file
			And that there is a 'CONTENT_FALLBACK_DIRS' variable set to a list of directories
			And these directories exist on disk with Kalanfa channel content in them
			And the 'KALANFA_HOME' environment variable has been set to a non-existing directory

		Scenario: Running Kalanfa for the first time with content fallback dirs
			When I open Kalanfa in the browser for the first time
				And I complete the "Super admin goes through the 'Quick Start' setup wizard" scenario
			When I am redirected to *Device > Channels*
			Then I see all the channels that exist in the directories specified in 'CONTENT_FALLBACK_DIRS'
