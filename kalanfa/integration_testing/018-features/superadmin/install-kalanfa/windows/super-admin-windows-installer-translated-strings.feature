Feature: Super admin can see the Windows installer translated strings
    Super admin can see the Windows installer translated strings during the Kalanfa Windows install/uninstall

    Background:
      Given I am installing Kalanfa on Windows OS
        And Windows UI is configured to display in <language> language by default

# List of translation from Spanish to English
# *Control de cuentas usuario* > *User Account Control*
# *Seleccionar idioma de Configuración* > *Select Setup Language*
# *Kalanfa configuración* > *Kalanfa Setup Wizard*
# *Iniciar Kalanfa* > *Launch Kalanfa*
# *Desinstalar un programa* > *Uninstall a Program*
# *Aceptar* > *Ok*
# *Sí* > *yes*
# *Siguiente* > *Install*
# *Finalizar* > *Finish*
# *Panel de control* > *Control Panel*

    Scenario: Display the translated strings at the Select Setup Language dialog
      When I double click the Kalanfa Windows installer
        And I see the dialog *Control de cuentas usuario*
        And I click the *Sí* button
        And I see the *Seleccionar idioma de Configuración* dialog
      Then I see that the translated strings are displayed properly

    Scenario: Install Kalanfa in <language> language
      When I double click the Kalanfa Windows installer
        And I see the dialog *Control de cuentas usuario*
        And I click the *Sí* button
        And I see the *Seleccionar idioma de Configuración* dialog
        And I select <language>
        And I click the *Aceptar* button
        # If the Python version 3.4 is not yet installed in this Windows environment
        And I see the setup message box that Python is required to install
        And I click *Sí* to install Python
      Then I see that Python is installing # Python installer might not be
        And I click *Siguiente* button
        And I continue the Kalanfa installation
      Then I see that every *Kalanfa configuración* window has translated strings that displayed properly
      When I see the Kalanfa setup has finished installing
        And I checked the *Iniciar Kalanfa* check box
        And I click the *Finalizar* button
      Then I see the task bar notification that Kalanfa is starting in <language> language
        And I see the browser opening with the setup wizard in <language> language

    Scenario: Uninstall Kalanfa with translated strings
        When I navigate at the *Panel de control*
          And I click the *Desinstalar un programa*
          And I double click the entry for Kalanfa
          And I see the dialog *Control de cuentas usuario*
          And I click the *Sí* button
        Then I see the windows and alerts during the uninstall process in <language> language
          And I see that Kalanfa is successfully uninstalled
