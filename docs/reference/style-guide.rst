:relatedlinks: https://github.com/canonical/lxd-sphinx-extensions, [reStructuredText&#32;Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html), [Canonical&#32;Documentation&#32;Style&#32;Guide](https://docs.ubuntu.com/styleguide/en)

.. _style-guide:

reStructuredText style guide
============================

The documentation files use `reStructuredText`_ (reST) syntax.

See the following sections for syntax help and conventions.

.. note::
   This style guide assumes that you are using the `Sphinx documentation starter pack`_.
   Some of the mentioned syntax requires Sphinx extensions (which are enabled in the starter pack).

For general style conventions, see the `Canonical Documentation Style Guide`_.

Headings
--------

.. list-table::
   :header-rows: 1

   * - Input
     - Description
   * - .. code::

          Title
          =====
     - Page title and H1 heading
   * - .. code::

          Heading
          -------
     - H2 heading
   * - .. code::

          Heading
          ~~~~~~~
     - H3 heading
   * - .. code::

          Heading
          ^^^^^^^
     - H4 heading
   * - .. code::

          Heading
          .......
     - H5 heading

Underlines must be at least as long as the title or heading.

Adhere to the following conventions:

- Do not use consecutive headings without intervening text.
- Be consistent with the characters you use for each level.
  Use the ones specified above.
- Use sentence style for headings (capitalise only the first word).

Inline formatting
-----------------

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - ``:guilabel:`UI element```
     - :guilabel:`UI element`
   * - ````code````
     - ``code``
   * - ``:file:`file path```
     - :file:`file path`
   * - ``:command:`command```
     - :command:`command`
   * - ``:kbd:`Key```
     - :kbd:`Key`
   * - ``*Italic*``
     - *Italic*
   * - ``**Bold**``
     - **Bold**

Adhere to the following conventions:

- Use italics sparingly. Common uses for italics are titles and names (for example, when referring to a section title that you cannot link to, or when introducing the name for a concept).
- Use bold sparingly. Avoid using bold for emphasis and rather rewrite the sentence to get your point across.

Code blocks
-----------

To start a code block, either end the introductory paragraph with two colons (``::``) and indent the following code block, or explicitly start a code block with ``.. code::``.
In both cases, the code block must be surrounded by empty lines.

When explicitly starting a code block, you can specify the code language to enforce a specific lexer, but in many cases, the default lexer works just fine.

For a list of supported languages and their respective lexers, see the official `Pygments documentation`_.

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          Demonstrate a code block::

            code:
             - example: true
     - Demonstrate a code block::

         code:
         - example: true
   * - .. code::

          .. code::

             # Demonstrate a code block
             code:
             - example: true
     - .. code::

          # Demonstrate a code block
          code:
          - example: true
   * - .. code::

          .. code:: yaml

             # Demonstrate a code block
             code:
             - example: true
     - .. code:: yaml

          # Demonstrate a code block
          code:
          - example: true

Terminal output
~~~~~~~~~~~~~~~

Showing a terminal view can be useful to show the output of a specific command or series of commands, where it is important to see the difference between input and output.
In addition, including a terminal view can help break up a long text and make it easier to consume, which is especially useful when documenting command-line-only products.

To include a terminal view, use the following directive:

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          .. terminal::
             :input: command number one
             :user: root
             :host: vm

             output line one
             output line two
             :input: another command
             more output
     - .. terminal::
          :input: command number one
          :user: root
          :host: vm

          output line one
          output line two
          :input: another command
          more output

Input is specified as the ``:input:`` option (or prefixed with ``:input:`` as part of the main content of the directive).
Output is the main content of the directive.

To override the prompt (``user@host:~$`` by default), specify the ``:user:`` and/or ``:host:`` options.
To make the terminal scroll horizontally instead of wrapping long lines, add ``:scroll:``.

Links
-----

Link markup depends on whether you need an external URL
or a page in the same documentation set.


External links
~~~~~~~~~~~~~~

For external links, use one of the following methods.

Link inline:
  Define occasional links directly within the surrounding text.
  To make the link text show up in code-style (which excludes it from the spelling check), use the ``:literalref:`` role.

  .. list-table::
     :header-rows: 1

     * - Input
       - Output

     * - ```Canonical website <https://canonical.com/>`_``
       - `Canonical website <https://canonical.com/>`_

     * - ``:literalref:`ubuntu.com```
       - :literalref:`ubuntu.com`
     * - ``:literalref:`xyzcommand <https://example.com>```
       - :literalref:`xyzcommand <https://example.com>`

  You can also use a URL as is (``https://example.com``),
  but that might cause spellchecker errors.

  .. tip::

     To prevent a URL from appearing as a link,
     add an escaped space character (``https:\ //``).
     The space won't be rendered:

     .. list-table::
        :header-rows: 1

        * - Input
          - Output

        * - ``https:\ //canonical.com/``
          - :spellexception:`https://canonical.com/`


Define the links at the bottom of the page:
  To keep the text readable, group the link definitions below.

  .. list-table::
     :header-rows: 1

     * - Input
       - Output
       - Description

     * - ```Canonical website`_``
       - `Canonical website`_
       - Using the below defined link

     * - .. code::

            .. LINKS
            .. _Canonical website: https://canonical.com/
       - *n/a*
       - Defining links at the bottom


Define the links in a shared file:
  To keep the text readable and links maintainable,
  put all link definitions in a file named :file:`reuse/links.txt`
  to include it in a custom ``rst_epilog`` directive
  (see the `Sphinx documentation <rst_epilog_>`_).

  .. code-block:: python
     :caption: :spellexception:`custom_conf.py`

     custom_rst_epilog = """
         .. include:: reuse/links.txt
         """

  .. list-table::
     :header-rows: 1

     * - Input
       - Output

     * - ```Canonical website`_``
       - `Canonical website`_

Related links
^^^^^^^^^^^^^

You can add links to related websites or Discourse topics to the sidebar.

To add a link to a related website, add the following field at the top of the page::

  :relatedlinks: https://github.com/canonical/lxd-sphinx-extensions, [RTFM](https://www.google.com)

To override the title, use Markdown syntax. Note that spaces are ignored; if you need spaces in the title, replace them with ``&#32;``, and include the value in quotes if Sphinx complains about the metadata value because it starts with ``[``.

To add a link to a Discourse topic, configure the Discourse instance in the :file:`custom_conf.py` file.
Then add the following field at the top of the page (where ``12345`` is the ID of the Discourse topic)::

  :discourse: 12345

Manual-page links
^^^^^^^^^^^^^^^^^

When mentioning command line utilities, you may wish to link to the
corresponding manual page for the command. Ensure that the ``manpages_url``
setting in your :file:`conf.py` is set appropriately and use the ``:manpage:``
inline role within your text to create a link.

For example, to link to man pages from the 24.04 LTS (Noble Numbat) release,
include the following in your :file:`conf.py`:

.. code-block:: python

    manpages_url = "https://manpages.ubuntu.com/manpages/noble/en/man{section}/{page}.{section}.html"

Then within your documentation, use the following reST:

.. code-block:: rst

    You can use the :manpage:`dd(1)` utility to write the disk image to your
    SD card. If the image is compressed, use :manpage:`aunpack(1)` to extract
    it first.


YouTube links
^^^^^^^^^^^^^

To add a link to a YouTube video, use the following directive:

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          .. youtube:: https://www.youtube.com/watch?v=iMLiK1fX4I0
             :title: Demo

     - .. youtube:: https://www.youtube.com/watch?v=iMLiK1fX4I0
          :title: Demo

The video title is extracted automatically and displayed when hovering over the link.
To override the title, add the ``:title:`` option.

Internal references
~~~~~~~~~~~~~~~~~~~

You can reference pages and targets in this documentation set, and also in other documentation sets using Intersphinx.

.. _section_target:

Referencing a section
^^^^^^^^^^^^^^^^^^^^^

To reference a section within the documentation (either on the same page or on another page), add a target to that section and reference that target.

.. _a_random_target:

You can add targets at any place in the documentation. However, if there is no heading or title for the targeted element, you must specify a link text.

.. list-table::
   :header-rows: 1

   * - Input
     - Output
     - Description
   * - ``.. _target_ID:``
     -
     - Adds the target ``target_ID``.

       .. note::
          When defining the target, you must prefix it with an underscore. Do not use the starting underscore when referencing the target.
   * - ``:ref:`a_section_target```
     - :ref:`a_section_target`
     - References a target that has a title.
   * - ``:ref:`Link text <a_random_target>```
     - :ref:`Link text <a_random_target>`
     - References a target and specifies a title.
   * - ``:ref:`starter-pack:home```
     - :ref:`starter-pack:home`
     - You can also reference targets in other doc sets.

Adhere to the following conventions:

- Never use external links to reference a section in the same doc set or a doc set that is linked with Intersphinx. It would likely cause a broken link in the future.
- Override the link text only when it is necessary. If you can use the referenced title as link text, do so, because the text will then update automatically if the title changes.
- Never "override" the link text with the same text that would be generated automatically.

Referencing a page
^^^^^^^^^^^^^^^^^^

If a documentation page does not have a target, you can still reference it by using the ``:doc:`` role with the file name and path.

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - ``:doc:`index```
     - :doc:`index`
   * - ``:doc:`Link text <index>```
     - :doc:`Link text <index>`
   * - ``:doc:`starter-pack:how-to/index```
     - :doc:`starter-pack:how-to/index`
   * - ``:doc:`Link text <starter-pack:how-to/index>```
     - :doc:`Link text <starter-pack:how-to/index>`

Adhere to the following conventions:

- Only use the ``:doc:`` role when you cannot use the ``:ref:`` role, thus only if there is no target at the top of the file and you cannot add it. When using the ``:doc:`` role, your reference will break when a file is renamed or moved.
- Override the link text only when it is necessary. If you can use the document title as link text, do so, because the text will then update automatically if the title changes.
- Never "override" the link text with the same text that would be generated automatically.

Navigation
----------

Every documentation page must be included as a sub-page to another page in the navigation.

This is achieved with the `toctree`_ directive in the parent page::

  .. toctree::
     :hidden:

     sub-page1
     sub-page2

If a page should not be included in the navigation, you can suppress the resulting build warning by putting ``:orphan:`` at the top of the file.
Use orphan pages sparingly and only if there is a clear reason for it.

.. tip::
   Instead of hiding pages that you do not want to include in the documentation from the navigation, you can exclude them from being built.
   This method will also prevent them from being found through the search.

   To exclude pages from the build, add them to the ``custom_excludes`` variable in the :file:`custom_conf.py` file.

Lists
-----

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          - Item 1
          - Item 2
          - Item 3
     - - Item 1
       - Item 2
       - Item 3
   * - .. code::

          1. Step 1
          #. Step 2
          #. Step 3
     - 1. Step 1
       #. Step 2
       #. Step 3
   * - .. code::

          a. Step 1
          #. Step 2
          #. Step 3
     - a. Step 1
       #. Step 2
       #. Step 3

You can also nest lists:

.. tab-set::

   .. tab-item:: Input

      .. code::

         1. Step 1

            - Item 1

              * Sub-item
            - Item 2

              i. Sub-step 1
              #. Sub-step 2
         #. Step 2

            a. Sub-step 1

               - Item
            #. Sub-step 2
   .. tab-item:: Output



       1. Step 1

          - Item 1

            * Sub-item
          - Item 2

            i. Sub-step 1
            #. Sub-step 2
       #. Step 2

          a. Sub-step 1

             - Item
          #. Sub-step 2



Adhere to the following conventions:

- In numbered lists, number the first item and use ``#.`` for all subsequent items to generate the step numbers automatically.
- Use ``-`` for unordered lists. When using nested lists, you can use ``*`` for the nested level.

Definition lists
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          Term 1:
            Definition
          Term 2:
            Definition
     - Term 1:
         Definition
       Term 2:
         Definition

Tables
------

reST supports different markup for tables. Grid tables are most similar to tables in Markdown, but list tables are usually much easier to use.
See the `Sphinx documentation <tables_>`_ for all table syntax alternatives.

Both markups result in the following output:

.. list-table::
   :header-rows: 1

   * - Header 1
     - Header 2
   * - Cell 1

       Second paragraph cell 1
     - Cell 2
   * - Cell 3
     - Cell 4

Grid tables
~~~~~~~~~~~

See `grid tables`_ for reference.

.. code::

   +----------------------+------------+
   | Header 1             | Header 2   |
   +======================+============+
   | Cell 1               | Cell 2     |
   |                      |            |
   | 2nd paragraph cell 1 |            |
   +----------------------+------------+
   | Cell 3               | Cell 4     |
   +----------------------+------------+

List tables
~~~~~~~~~~~

See `list tables`_ for reference.

.. code::

   .. list-table::
      :header-rows: 1

      * - Header 1
        - Header 2
      * - Cell 1

          2nd paragraph cell 1
        - Cell 2
      * - Cell 3
        - Cell 4

Notes
-----

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          .. note::
             A note.
     - .. note::
          A note.
   * - .. code::

          .. warning::
             This might damage your hardware!
     - .. warning::
          This might damage your hardware!

Adhere to the following conventions:

- Use notes sparingly.
- Only use the following note types: ``note``, ``warning``
- Only use a warning if there is a clear hazard of hardware damage or data loss.

Images
------

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - ``.. image:: https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png``
     - .. image:: https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png
   * - .. code::

          .. figure:: https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png
             :width: 100px
             :alt: Alt text

             Figure caption
     - .. figure:: https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png
          :width: 100px
          :alt: Alt text

          Figure caption

Adhere to the following conventions:

- For local pictures, start the path with :file:`/` (for example, :file:`/images/image.png`).
- Use ``PNG`` format for screenshots and ``SVG`` format for graphics.
- If producing multiple output formats, use ``*`` as the file extension to have
  Sphinx select the best image format for the output
- See `Five golden rules for compliant alt text`_ for information about how to word the alt text.

Reuse
-----

A big advantage of reST in comparison to plain Markdown is that it allows to reuse content.

Substitution
~~~~~~~~~~~~

To reuse sentences and entire paragraphs
that have little markup or special formatting,
define `substitutions`_ for them in two possible ways.

**Globally**, in a file named :file:`reuse/substitutions.txt`
that is included in a custom ``rst_epilog`` directive
(see the `Sphinx documentation <rst_epilog_>`_):

.. code-block:: python
   :caption: :spellexception:`conf.py`

   rst_epilog = """
       .. include:: reuse/substitutions.txt
       """


.. code-block:: rest
   :caption: :spellexception:`reuse/substitutions.txt`

   .. |version_number| replace:: 0.1.0

   .. |rest_text| replace:: *Multi-line* text
                            that uses basic **markup**.

   .. |site_link| replace:: Website link
   .. _site_link: https://example.com


**Locally**, putting the same directives in any reST file:

.. code-block:: rest
   :caption: :spellexception:`index.rst`

   .. |version_number| replace:: 0.1.0

   .. |rest_text| replace:: *Multi-line* text
                            that uses basic **markup**.

   .. And so on


.. note::

   Mind that substitutions can't be redefined;
   for instance, accidentally including a definition twice causes an error:

   .. code-block:: none

      ERROR: Duplicate substitution definition name: "rest_text".


The definitions from the above examples are rendered as follows:

.. list-table::
   :header-rows: 1

   * - Input
     - Output

   * - ``|version_number|``
     - |version_number|

   * - ``|rest_text|``
     - |rest_text|

   * - ``|site_link|_``
     - |site_link|_


.. tip::

   Use substitution names that hint at the included content
   (for example, ``note_not_supported`` instead of ``note_substitution``).


File inclusion
~~~~~~~~~~~~~~

To reuse longer sections or text with more advanced markup, you can put the content in a separate file and include the file or parts of the file in several locations.

To select parts of the text in a file, use ``:start-after:`` and ``:end-before:`` if possible. You can combine those with ``:start-line:`` and ``:end-line:`` if required (if the same text occurs more than once). Using only ``:start-line:`` and ``:end-line:`` is error-prone though.

You cannot put any targets into the content that is being reused (because references to this target would be ambiguous then). You can, however, put a target right before including the file.

By combining file inclusion and substitutions defined directly in a file, you can even replace parts of the included text.

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          .. include:: index.rst
             :start-after: Also see the following information:
             :end-before: Contents
     - .. include:: index.rst
          :start-after: Also see the following information:
          :end-before: Contents

Adhere to the following conventions:

- Files that only contain text that is reused somewhere else should be placed in the :file:`reuse` folder and end with the extension ``.txt`` to distinguish them from normal content files.
- To make sure inclusions don't break, consider adding comments (``.. some comment``) to the source file as markers for starting and ending.

Tabs
----

The recommended way of creating tabs is to use the tabs that the `Sphinx design`_ extension provides.

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          .. tab-set::

             .. tab-item:: Tab 1
                :sync: key1

                Content Tab 1

             .. tab-item:: Tab 2
                :sync: key2

                Content Tab 2
     - .. tab-set::

         .. tab-item:: Tab 1
            :sync: key1

            Content Tab 1

         .. tab-item:: Tab 2
            :sync: key2

            Content Tab 2

Alternatively, you can use the `Sphinx tabs`_ extension, which is also enabled by default. This was previously recommended due to limitations in Sphinx Design that are now fixed.

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          .. tabs::

             .. group-tab:: Tab 1

                Content Tab 1

             .. group-tab:: Tab 2

                Content Tab 2
     - .. tabs::

          .. group-tab:: Tab 1

             Content Tab 1

          .. group-tab:: Tab 2

             Content Tab 2

Glossary
--------

You can define glossary terms in any file. Ideally, all terms should be collected in one glossary file though, and they can then be referenced from any file.

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          .. glossary::

             an example term
               Definition of an example term.
     - .. glossary::

          an example term
            Definition of an example term.
   * - ``:term:`an example term```
     - :term:`an example term`

.. _section_more_useful_markup:

More useful markup
------------------

.. list-table::
   :header-rows: 1

   * - Input
     - Output
     - Description
   * - .. code::

          .. versionadded:: X.Y
     - .. versionadded:: X.Y
     - Can be used to distinguish between different versions.
   * - .. code::

          | Line 1
          | Line 2
          | Line 3
     - | Line 1
       | Line 2
       | Line 3
     - Line breaks that are not paragraphs. Use this sparingly.
   * - .. code::

          ----
     - A horizontal line
     - Can be used to visually divide sections on a page.
   * - ``.. This is a comment``
     - .. This is a comment
     - Not visible in the output.
   * - ``:abbr:`API (Application Programming Interface)```
     - :abbr:`API (Application Programming Interface)`
     - Hover to display the full term.
   * - ``:spellexception:`PurposelyWrong```
     - :spellexception:`PurposelyWrong`
     - Explicitly exempt a term from the spelling check.

.. LINKS

.. wokeignore:rule=master
.. _substitutions: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#substitutions

.. wokeignore:rule=master
.. _rst_epilog: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-rst_epilog
