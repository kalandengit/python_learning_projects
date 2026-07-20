
.. _build_pipeline:

Distribution build pipeline
===========================

The Kalanfa Package build pipeline looks like this::

                        Git release branch
                                |
                                |
                               / \
                              /   \
 Python dist, online dependencies  \
    `python setup.py bdist_wheel`   \
                /                    \
               /                Python dist, bundled dependencies
        Upload to PyPi        `python setup.py bdist_wheel --static`
       Installable with                 \
     `pip install kalanfa`               \
                                    Upload to PyPi
                                    Installable with
                              `pip install kalanfa-static`
                                /            |          \
                               /             |           \
                         Windows          Android        Debian
                        installer           APK         installer


Make targets
------------

- To build a wheel file, run ``make dist``
- To build a pex file, run ``make pex`` after ``make dist``
- Builds for additional platforms are triggered from buildkite  based on *.buildkite/pipeline.yml*


More on version numbers
-----------------------

.. note:: The content below is pulled from the docstring of the ``kalanfa.utils.version`` module.

.. automodule:: kalanfa.utils.version
  :undoc-members:
  :show-inheritance:


.. warning:: Tagging is known to break after rebasing, so in case you rebase
    a branch after tagging it, delete the tag and add it again. Basically,
    ``git describe --tags`` detects the closest tag, but after a rebase, its
    concept of distance is misguided.
