# Running another Kalanfa instance alongside the development server

This guide will walk you through the process of setting up and running another instance of Kalanfa alongside your development server using the `pex` executable.

## Introduction

As Kalanfa's features continue to expand into remote content browsing, it's often necessary to test and experiment with another Kalanfa instance running alongside your development server. One effective approach is to use the `pex` executable. This workflow is straightforward and can be employed independently of ZeroTier or even internet network access. By following these steps, you can effectively simulate real-world scenarios and enhance your development workflow.

## Steps

- **Locate the .pex executable:**

  - Navigate to the [Kalanfa GitHub repository](https://github.com/learningequality/kalanfa).
  - Click on the "Actions" tab at the top of the repository.
  - Select the "Kalanfa Build Assets for Pull Request" option from the sidebar.
  - Select a workflow build from the list.
  - Scroll down the workflow build page to find the "Artifacts" section. In this section, you will find the `.pex` file that you need to download.

- **Save and unzip the .pex file:**

  Save the downloaded `.pex` file to a suitable location on your machine. Unzip the downloaded `pex` file to a folder where you want to run the additional Kalanfa instance from.

- **Run another Kalanfa instance:**

  First, make sure you are using Python version <= 3.9.

  Then, open your terminal and navigate to the folder where you unzipped the `pex` file. Use the following command to start another Kalanfa instance:

  ```sh
  KALANFA_HOME="<foldername>" python <filename>.pex start
  ```
  Replace `<filename>` with the actual filename of the `pex` executable and replace `<foldername>` with the desired name for the folder that will store the settings and data for this instance.

  Be sure to choose a meaningful folder name and avoid leaving it blank to ensure it doesn't overwrite your default `.kalanfa`directory.

  **Note:** You don't need to create the folder beforehand; it will be automatically generated if not already present when you run the command.



- **Complete initial setup:**

  In the terminal, you'll find the URL of the new Kalanfa instance. Open the URL in your browser and complete the initial device setup as you would for a regular Kalanfa instance. Additionally, import a few resources from desired channels.

- **Run your development server:**

  Once the additional Kalanfa instance is up and running, start your development server as usual. You should now see the new device on your network.

- **Stop the other Kalanfa instance:**

  When you're done testing, you can stop the additional Kalanfa instance using the following command:
  ```sh
  python <filename>.pex stop
  ```
  This will gracefully shut down the instance.
