# Running Kalanfa with local Kalanfa Design System

Kalanfa uses components from [Kalanfa Design System](https://github.com/learningequality/kalanfa-design-system) (KDS). KDS is installed in Kalanfa as a usual npm dependency.

It is sometimes useful to run Kalanfa development server linked to local KDS repository, for example to confirm that a KDS update fixes bug observed in Kalanfa, when developing new KDS feature in support of Kalanfa feature, etc.

For this purpose, Kalanfa provides `devserver-with-kds` command that will run the development server with Kalanfa using local KDS:

```bash
pnpm run devserver-with-kds <kds-path>
```

where `<kds-path>` is the path of the local `kalanfa-design-system` repository.

.. warning::
  Some developers have reported issues when running the command with a relative path. If you encounter any problems, try using an absolute KDS path.
