.. _automatic-checks-styleguide:

Style guide linting
===================

The starter pack includes a method to run the `Vale`_ documentation linter configured with `the Vale rules for the current style guide <Vale rules_>`_.


Run the style guide linting
---------------------------

Run the following commands from within your documentation folder.

Check documentation with Vale::

   make vale

Vale can run against individual files, folders, or globs.
To set a specific target::

    make vale TARGET=example.file
    make vale TARGET=example-folder

.. note::

    Running Vale against a folder will also run against its subfolders.

You can use wildcards to run against all files matching a string, or an extension.

For example, to run against all :code:`.md` files within a folder::

    make vale TARGET=*.md

To match, for example, :code:`doc_1.md` and :code:`doc_2.md`::

    make vale TARGET=doc*


Exempt paragraphs
-----------------

To disable Vale linting within individual files, specific markup can be used.

For Markdown:

.. code-block:: Markdown

   <!-- vale off -->

   This text will be ignored by Vale.

   <!-- vale on -->

For |RST|:

.. code-block:: rest

   .. vale off

   This text will be ignored by Vale.

   .. vale on


Exempt directives
-----------------

To disable Vale linting for a specific directive, you can apply a class to the section.

For Markdown:

.. code-block:: Markdown

    ````{class} vale-ignore
    ```{code-block}

    This content will be ignored by Vale.
    ```
    ````

.. note::
    
    This should not be necessary for Markdown, as Vale has an expanded scope for ignoring Markdown content by default.

For |RST|:

.. code-block:: rst

    .. class:: vale-ignore
    .. code-block::

        This content will be ignored by Vale.

.. note:: 

    The `.. class::` directive does not need to encapsulate content, it applies to the next logical block (which can be another directive or even a paragraph of content).