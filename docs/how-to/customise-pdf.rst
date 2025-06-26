.. _pdf-customise:

Customise PDF output
====================

Overview
--------

The starter pack supports PDF output via LaTeX using the ``make pdf`` command. This build process relies on system packages, Sphinx configurations, and a LaTeX template from the ``canonical-sphinx`` extension.

Customising PDF output involves two levels of configuration:

* **Sphinx configuration**: built-in options for configuring LaTeX build process in :file:`conf.py`, for example: the engine used to generate the PDF, output file name, and input file paths.
* **LaTeX configuration**: the LaTeX packages, styling, and configuration for the PDF output, set through the `latex_elements <https://www.sphinx-doc.org/en/master/latex.html#the-latex-elements-configuration-setting>`_ dictionary in the project :file:`conf.py`. In the starter-pack, a default set of LaTeX elements is provided by the ``canonical-sphinx`` extension. Changing the LaTeX configuration requires overriding the default values loaded from the extension.

This guide covers common practices and tips for customising PDF output from your documentation project using the starter pack and the ``canonical-sphinx`` extension.

For basic instructions about building the PDF, see :doc:`build`.

Configure document properties
-----------------------------

The `latex_documents <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-latex_documents>`_ variable in the Sphinx :file:`conf.py` file controls properties of the intermediate LaTeX file and the final PDF output. The values are defined in a tuple of six elements:

.. code-block:: python

   latex_documents = [
       (
           'startdocname',   # Root document (e.g., 'index' or 'pdf-index')
           'targetname.tex', # Output LaTeX file name (no spaces)
           'title',          # Document title (can be empty to use the root doc's title)
           'author',         # Author name(s).
           'theme',          # Document type: 'manual' or 'howto'
           True,             # toctree_only: if True, only include docs in toctree
       ),
   ]

* ``startdocname``: The root document for the PDF (without the .rst extension).
* ``targetname``: The filename for the generated LaTeX source file. The PDF file name is derived from this filename with the ``.pdf`` extension. Blank space characters are not allowed.
* ``title``: The title for the PDF document on the cover page.
* ``author``: The author(s) of the document. Use ``\\and`` to separate multiple authors.
* ``theme``: Either ``manual`` or ``howto``.

  * ``manual``: This is the default and is intended for comprehensive, book-style documentation. It produces a PDF with chapters, sections, and a table of contents. Use this for user guides, reference manuals, or any documentation that should be structured as a book.
  * ``howto``: This type is for shorter, task-oriented documents. It produces a simpler PDF without chapters, and is best for single-topic guides or tutorials.

* ``toctree_only``: Boolean. If set to True, the ``startdocname`` document itself is not included in the output, only the documents referenced by the ``toctree`` directive are included. This is useful for creating a PDF-specific index file.

For more details, see `latex_documents`_ in the Sphinx documentation.


Change PDF document filename
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the PDF output filename is derived from the ``project`` name in the :file:`conf.py` file: lowercase characters with blank spaces removed. 

To override the filename, update the second element (``targetname``) of the ``latex_documents`` tuple in :file:`conf.py`. The following example shows how to replace blank spaces in the project name with underscores:

.. code-block:: python

   latex_documents = [
      (
         'index',
         f"{project.replace(' ', '_')}.tex",
         '',
         'Author Name',
         'manual',
         True,
      ),
   ]

Change PDF document title
~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the PDF title on the cover page comes from the title of the main index document. To override it, update the third element (title) of the ``latex_documents`` tuple in :file:`conf.py`. Use an empty string (``''``) to keep the default behaviour.

Use a different index document for PDF builds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because the PDF output has a different usage and structure from the HTML output, it is sometimes useful to create a PDF-specific index document. For example, you may want to create a PDF-specific index file that includes only a subset of the pages in the HTML index.

To use a different index document for PDF builds:

1. Create a PDF-specific index document, for example, :file:`pdf-index.rst`.
2. Update the first element (``startdocname``) of the ``latex_documents`` tuple in :file:`conf.py` to point to the new index document.
3. Set the last element (``toctree_only``) of the ``latex_documents`` tuple in :file:`conf.py` to ``False`` to ensure only referenced documents are included in the PDF output.
4. Exclude the PDF-specific index document from the HTML build. This is done by changing the ``exclude_patterns`` list in :file:`conf.py`:

   .. code-block:: python

      # Identify the Sphinx builder being used
      if '-b' in sys.argv:
         builder = sys.argv[sys.argv.index('-b') + 1]
      elif '-M' in sys.argv:
         builder = sys.argv[sys.argv.index('-M') + 1]
      else:
         builder = 'html'  # default builder

      # Exclude the PDF-specific index from the HTML build
      if builder in ['html', 'dirhtml']:
         exclude_patterns.append('pdf-index.rst')

Check both the HTML and PDF outputs to confirm that different index documents are used for each output.

.. note::
   The order and hierarchy of your ``toctree`` entries determine the chapters and sections in the PDF.

   Any headings placed before the main ``toctree`` in your root document will cause all referenced documents to be nested under that heading in the PDF. To avoid this, do not add extra headings before the ``toctree``.


Override the LaTeX template
-----------------------------

The LaTeX template is a text file in the ``canonical-sphinx`` extension that provides the default styling and layout of the PDF document. The template contains a Python dictionary of LaTeX elements, which will be imported by Sphinx when the PDF is built.

Any additions or changes to the default settings of LaTeX elements in the PDF document requires overriding the default template.

1. Download the default template file `latex_elements_template.txt <https://github.com/canonical/canonical-sphinx/blob/main/canonical_sphinx/theme/PDF/latex_elements_template.txt>`_ from the ``canonical/canonical-sphinx`` GitHub repository, and save it to your documentation project directory. For example, at :file:`.sphinx/latex_elements_custom.txt`.

2. In the Python dictionary, add or modify the LaTeX elements you want to change. Details of changing the dictionary are covered in the sub-sections below.

3. In your project :file:`conf.py`, add or update the ``latex_elements`` dictionary to load the local override of the LaTeX template. Change the file path to the location of your local override file.

.. code-block:: python

   # Replace with the path to your local override file
   latex_elements_file = ".sphinx/latex_elements_custom.txt"  
   
   with open(latex_elements_file, "rt") as file:
      latex_config = file.read()
      if latex_elements == {}:
         latex_elements = ast.literal_eval(latex_config)

.. warning::

   Defining other settings directly in ``latex_elements`` will override the values loaded from the template file or your local file.


Add more LaTeX packages to the preamble
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use two methods to add additional LaTeX packages to the preamble:

* Add the ``extrapackages`` key in your local template file:

  .. code-block:: python
     :emphasize-lines: 3

     {
       ...
       'extrapackages': r'\usepackage{packagename}',
       ...
     }

* Modify the values of the ``preamble`` key in your local template file. This is more flexible for adding LaTeX configurations and commands to the preamble.

.. note:: 
   The format of the element values is a multi-line string, so use a raw string with the ``r`` prefix.


Remove the table of contents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a short, compact document where navigation is not needed, you may want to remove the table of contents from the PDF output. 

To do this, provide a local copy of the default template file, and add a new key ``tableofcontents`` with an empty string as the value:

.. code-block:: python
   :emphasize-lines: 3

   {
      ...
      'tableofcontents': '',
      ...
   }
   

Include images or other assets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the local template requires additional images or other assets, for example, a custom title page or header, the file paths must be added to the Sphinx :file:`conf.py` file to be included in the PDF build.

Provide a ``latex_additional_files`` variable in :file:`conf.py` as a list of file paths to the additional assets. If the variable already exists, add the new file paths to the list. The paths should be relative to the :file:`conf.py` file.

.. code-block:: python

   # path relative to the conf.py file
   latex_additional_files = [
      'path/to/image.svg',
      'path/to/other-asset.pdf',
   ]

.. note:: 
   For better quality in the PDF output, it is recommended to use vector images (like SVG or PDF) rather than raster images (like PNG or JPEG). Raster images may lose quality when scaled up in the PDF.

   Do not use ``.tex`` as suffix, otherwise the file is processed as source files for the PDF build process. Instead, use ``.tex.txt`` or ``.sty``  to avoid conflicts with the LaTeX build process.

Use landscape layout
~~~~~~~~~~~~~~~~~~~~

The PDF output uses portrait orientation by default. To use landscape orientation, you need to add more packages to the LaTeX preamble and use a specific LaTeX environment to rotate the content.

1. Add the ``extrapackages`` key to your local template file, and set the value to the ``pdflscape`` package:

   .. code-block:: python
      :emphasize-lines: 3

      {
         ...
         'extrapackages': r'\usepackage{pdflscape}',
         ...
      }

   .. note:: 
      The format of the element values is a multi-line string, so use a raw string with the ``r`` prefix.

2. Use the landscape environment in your documentation source file, and only in the PDF output.

   Wherever you want a section (such as a wide table or figure) to appear in the landscape view, use the ``.. raw:: latex`` directive to include raw LaTeX code that opens and closes the landscape environment. Only the content between ``\begin{landscape}`` and ``\end{landscape}`` will be rotated:

   .. code-block:: rst

      .. only:: latex

         .. raw:: latex

            \begin{landscape}

      .. list-table:: Example of a landscape table
         :header-rows: 1

         * - Column 1
           - Column 2
           - Column 3
         * - Data 1
           - Data 2
           - Data 3

      .. only:: latex

         .. raw:: latex

            \end{landscape}


Check PDF build log files
-------------------------

If you encounter an issue that requires further debugging, check the PDF build logs for more detailed error messages. The full logs are generated in the :file:`_build/latex` output directory, and then cleaned up after the build completes.

To temporarily save the log files for debugging:

1. Open the ``Makefile`` and locate the ``pdf`` target. Disable the cleanup step by commenting out the ``@rm -r $(BUILDDIR)/latex`` line.
2. Run the ``make pdf`` again.
3. Navigate to the output directory :file:`_build/latex` and check the ``*.log`` and ``*.tex`` files.
4. After debugging, restore the cleanup step by uncommenting the same line.

.. warning::

    Keeping the build log files from the previous build might cause conflicts with the current build

Related
-------
- :doc:`build`
- :doc:`customise`
