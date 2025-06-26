.. _prereqs:

Install prerequisites
=====================

The documentation framework that the starter pack uses bundles most prerequisites in a Python virtual environment, so you don't need to worry about installing them.
There are only a few packages that you need to install on your host system.

Install prerequisite software
-----------------------------

Before you start, make sure that you have ``make``, ``python3``, ``python3-venv``, and ``python3-pip`` on your system::

   sudo apt update
   sudo apt install make python3 python3-venv python3-pip

Python environment
------------------

The Python prerequisites from the :file:`.sphinx/requirements.txt` file are automatically installed when you build the documentation.

If you want to install them manually, you can run the following command from within your documentation folder::

   make install

This command creates a virtual environment (:file:`.sphinx/venv/`) and installs dependency software within it.

If you want to remove the installed Python packages (for example, to enforce a re-installation), run the following command from within your documentation folder::

  make clean

.. note::
   - By default, the starter pack uses the latest compatible version of all tools and does not pin its requirements.
     This might change temporarily if there is an incompatibility with a new tool version.
     There is therefore no need to use a tool like Renovate to automatically update the requirements.

   - If you encounter the error ``locale.Error: unsupported locale setting`` when activating the Python virtual environment, include the environment variable in the command and try again: ``LC_ALL=en_US.UTF-8 make run``
