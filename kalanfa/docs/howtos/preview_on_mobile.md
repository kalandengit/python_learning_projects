# Preview Kalanfa on a mobile device

_Note: This guide focuses on Kalanfa as a web app rather than the Android version of Kalanfa._

Some tasks may require either an actual or simulated mobile device, such as a phone or tablet.

## Browser development tools

Most browsers provide ways to simulate mobile devices via their development tools. These tools are generally useful for testing:

- Mobile viewports
- Network and CPU throttling
- Touch gestures

Find specific guidance for the browser you are using.

## Real mobile device

Since browser development tools only offer an approximation, some tasks may require you to preview Kalanfa on a real mobile device.

### Option 1 (recommended)

1. Ensure that the mobile device you wish to use for previewing Kalanfa is connected to the same local network as your computer where you run the development server.
2. Run the development server with `pnpm run python-devserver` and `pnpm run watch --write-to-disk`
3. In the section with URLs in the ``pnpm run python-devserver`` terminal output, locate Kalanfa's ``http://A.B.C.D:8000/`` URL on the first line. Open a browser on the mobile device and navigate to that URL, where you should see Kalanfa.

```bash
INFO     2024-11-19 15:14:21,967 Kalanfa running on: http://A.B.C.D:8000/ # use this URL
...
INFO     2024-11-19 15:14:21,967 Kalanfa running on: http://127.0.0.1:8000/
```

### Option 2

1. Ensure that the mobile device you wish to use for previewing Kalanfa is connected to the same local network as your computer where you run the development server.
2. Run the development server with `pnpm run python-devserver` and `pnpm run build`
3. In the section with URLs in the ``pnpm run python-devserver`` terminal output, locate Kalanfa's ``http://A.B.C.D:8000/`` URL on the first line. Open a browser on the mobile device and navigate to that URL, where you should see Kalanfa.

```bash
INFO     2024-11-19 15:14:21,967 Kalanfa running on: http://A.B.C.D:8000/ # use this URL
...
INFO     2024-11-19 15:14:21,967 Kalanfa running on: http://127.0.0.1:8000/
```

.. warning::
   When running the development server as described above, you will need to rebuild frontend assets manually using ``pnpm run build`` after every change.

.. tip::
   Rebuild frontend assets faster by rebuilding only assets related to a plugin where you currently work. For example when developing on files of the Learn plugin, after the initial ``pnpm run build`` run, for all subsequent rebuilds only run ``pnpm exec kalanfa-build prod --plugins kalanfa.plugins.learn`` instead of ``pnpm run build``. Use ``kalanfa plugin list`` to see all plugins.

### Troubleshooting

- If you see an indefinite Kalanfa loader on your mobile device, double-check that you are not running the development server with `pnpm run devserver-hot`. Follow the steps outlined above instead.

- If you cannot access Kalanfa at all, check your firewall, VPN, or similar network settings.
