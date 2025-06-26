.. _automatic-checks-links:

Link check
==========

The link check uses Sphinx to access the links in the documentation output and validate whether they are working.

Run the link check
------------------

Run the following command from within your documentation folder.

Validate links within the documentation::

   make linkcheck

Configure the link check
------------------------

If you have links in the documentation that you don't want to be checked (for example, because they are local links or give random errors even though they work), you can add them to the ``linkcheck_ignore`` variable in the :file:`conf.py` file.
