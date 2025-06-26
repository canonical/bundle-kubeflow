.. _automatic-checks-spelling:

Spelling check
==============

The spelling check uses ``pyspelling`` to check the spelling in your documentation.
It ignores code (both code blocks and inline code) and URLs (but it does check the link text).

Run the spelling check
----------------------

Run the following commands from within your documentation folder.

Ensure there are no spelling errors in the documentation::

  make spelling

If you only want to check the existing output and do not want to build the HTML again, run the spelling check separately::

  make spellcheck

Configure the spelling check
----------------------------

The spelling check uses ``pyspelling``, which in turn relies on ``aspell``.
Its configuration is located in the :file:`.sphinx/spellingcheck.yaml` file.

The starter pack includes a common list of words that should be excluded from the check (:file:`.sphinx/.wordlist.txt`).
You shouldn't edit this file, because it is maintained and updated centrally and contains words that apply across all projects.
To add custom exceptions for your project, add them to the :file:`.custom_wordlist.txt` file.

If you need to add systematic exceptions for specific HTML tags or CSS classes (for example, all image captions or H2 headings), you can do this in the :file:`.sphinx/spellingcheck.yaml` file.
You can configure which HTML elements to exclude under ``pyspelling.filters.html``.

Exclude specific terms
----------------------

Sometimes, you need to use a term in a specific context that should usually fail the spelling check.
(For example, you might need to refer to a product called ``ABC Docs``, but you do not want to add ``docs`` to the word list because it isn't a valid word.)

In this case, you can use the ``:spellexception:`` role.
See :ref:`More useful markup <section_more_useful_markup>` in the |RST| style guide (also available in MyST).
