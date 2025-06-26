.. _edit:

Edit content
============

The landing page is stored in the :file:`docs/index.rst` file by default.

The Navigation Menu structure is set by ``.. toctree::`` directives. These directives define the hierarchy of included content throughout the documentation.
The :file:`index.rst` page's ``toctree`` block contains the top level Navigation Menu, default to the `Diátaxis`_ documentation structure.

To add a new page to the documentation:    

1. Create a new file in the `docs/` folder. For example, to create a new **Reference** page, create a document under `docs/reference/` directory called :file:`settings.rst`, insert the following |RST|-formatted heading ``Settings`` at the beginning, and then save the file:

   .. code-block:: rest
      :caption: reStructuredText title example

         Settings
         ========

   If you prefer to use Markdown (MyST) syntax instead of |RST|, you can create a Markdown file. For example, :file:`settings.md` file with the following Markdown-formatted heading at the beginning:

   .. code-block:: markdown
      :caption: Markdown title example
         
         # Settings

2. Add the new page to the Navigation Menu: open the :file:`docs/reference/index.rst` file or another file where you want to nest the new page; at the bottom of the file, locate the ``toctree`` directive and add a properly indented line containing the relative path (without a file extension) to the new file created in the first step. For example, ``settings``.

   The ``toctree`` block will now look like this:

   .. code-block:: rest
         
         .. toctree::
            :hidden:
            :maxdepth: 2

            Documentation checks <automatic_checks>
            style-guide
            style-guide-myst
            settings

The documentation will now show the new page added to the navigation when rebuilt.

By default, the page's title (the first heading in the file) is used for the Navigation Menu entry. You can overwrite a name of a Menu element by specifying it explicitly in the ``toctree`` block, for example: ``Reference </reference/index>``.
