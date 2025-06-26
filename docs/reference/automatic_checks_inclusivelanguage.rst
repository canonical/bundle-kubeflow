.. _automatic-checks-inclusivelanguage:

Inclusive language check
========================

The inclusive language check uses `Vale`_ to check for violations of inclusive language guidelines.

Run the inclusive language check
--------------------------------

Run the following command from within your documentation folder::

   make woke

Configure the inclusive language check
--------------------------------------

By default, the inclusive language check is applied to Markdown and |RST| files located in the documentation folder (usually :file:`docs/`).

Inclusive language check exemptions
-----------------------------------

Sometimes, you might need to use some non-inclusive words.
In such cases, you may exclude them from the check.

Exempt a word in a single instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To exempt an individual word, give the word the ``woke-ignore`` role::

   :woke-ignore:`<SOME_WORD>`

For instance::

   This is your text. The word in question is here: :woke-ignore:`whitelist`.

.. note::

   Vale will lint the displayed text of a link, not the URL of a link. If you
   wish to use a link that contains non-inclusive language, use appropriate link
   text with the syntax appropriate for your source file. 

Exempt a word globally
~~~~~~~~~~~~~~~~~~~~~~

Vale will ignore any word listed in the ``.custom_wordlist.txt`` file.
To exempt a word, add it to this file globally.

.. note::

   Entries in ``.custom-wordlist`` are case-sensitive only when a capitalised word is used. For instance:

   - Adding ``kustom`` will cause all instances of ``Kustom`` and ``kustom`` to be ignored.
   - Adding ``Kustom`` will cause only instances of ``Kustom`` to be ignored.

Exclude multiple lines from a file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vale can be switched on and off within a file using syntax appropriate to that
format.

To turn Vale off entirely for a section of Markdown::

   <!-- vale off -->

   This text will be ignored.

   <!-- vale on -->

.. important::

   Only use this when other options are not suitable.

To turn Vale off entirely for a section of |RST|::

   .. vale off

   This text will be ignored.

   .. vale on