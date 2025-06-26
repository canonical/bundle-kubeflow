.. _automatic-checks-accessibility:

Accessibility check
===================

The accessibility check uses `Pa11y`_ to check for accessibility issues in the documentation output.

It is configured to use the `Web Content Accessibility Guidelines (WCAG) 2.2`_, requiring `Level AA conformance`_.

.. note::

   This check is only available locally.

Install prerequisite software
-----------------------------

``Pa11y`` must be installed through ``npm``. If you need to install ``npm``, run the following command from any location on your system::

   sudo apt install npm

Once ``npm`` is installed, install ``Pa11y`` by running this command from within your documentation folder.

.. code-block:: bash

   make pa11y-install

Run the accessibility check
---------------------------

Run the following command from within your documentation folder.

Look for accessibility issues in rendered documentation::

   make pa11y

Configure the accessibility check
---------------------------------

The :file:`pa11y.json` file in the :file:`.sphinx` folder provides basic defaults.

To browse the available settings and options, see ``Pa11y``'s `README <Pa11y readme_>`_ on GitHub.
