:orphan:

.. TODO: Replace all mentions of ACME with your project name
.. TODO: Update all sections containing TODOs; make sure no TODOs are left


How to contribute
=================

We believe that everyone has something valuable to contribute,
whether you're a coder, a writer or a tester.
Here's how and why you can get involved:

- **Why join us?** Work with like-minded people, develop your skills,
  connect with diverse professionals, and make a difference.

- **What do you get?** Personal growth, recognition for your contributions,
  early access to new features and the joy of seeing your work appreciated.

- **Start early, start easy**: Dive into code contributions,
  improve documentation, or be among the first testers.
  Your presence matters,
  regardless of experience or the size of your contribution.


The guidelines below will help keep your contributions effective and meaningful.


Code of conduct
---------------

When contributing, you must abide by the
`Ubuntu Code of Conduct <https://ubuntu.com/community/ethos/code-of-conduct>`_.


Licence and copyright
---------------------

.. TODO: Update with your license details or drop if excessive

By default, all contributions to ACME are made under the AGPLv3 licence.
See the `licence <https://github.com/canonical/ACME/blob/main/COPYING>`_
in the ACME GitHub repository for details.

All contributors must sign the `Canonical contributor licence agreement
<https://ubuntu.com/legal/contributors>`_,
which grants Canonical permission to use the contributions.
The author of a change remains the copyright owner of their code
(no copyright assignment occurs).


Releases and versions
---------------------

.. TODO: Add your release and versioning details or drop if excessive

ACME uses `semantic versioning <https://semver.org/>`_;
major releases occur once or twice a year.

The release notes can be found `TODO: here <https://example.com>`_.


Environment setup
-----------------

.. TODO: Update with your prerequisites or drop if excessive

To work on the project, you need the following prerequisites:

- `TODO: Prerequisite 1 <http://example.com>`_
- `TODO: Prerequisite 2 <http://example.com>`_


To install and configure these tools:

.. code-block:: console

   TODO: prerequisite command 1
   TODO: prerequisite command 2


Submissions
-----------

.. TODO: Suggest your own PR process or drop if excessive

If you want to address an issue or a bug in ACME,
notify in advance the people involved to avoid confusion;
also, reference the issue or bug number when you submit the changes.

- `Fork
  <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks>`_
  our `GitHub repository <https://github.com/canonical/ACME>`_
  and add the changes to your fork,
  properly structuring your commits,
  providing detailed commit messages
  and signing your commits.

- Make sure the updated project builds and runs without warnings or errors;
  this includes linting, documentation, code and tests.

- Submit the changes as a `pull request (PR)
  <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork>`_.


Your changes will be reviewed in due time;
if approved, they will be eventually merged.


Describing pull requests
~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO: Update with your own checklist or drop if excessive

To be properly considered, reviewed and merged,
your pull request must provide the following details:

- **Title**: Summarise the change in a short, descriptive title.

- **Description**: Explain the problem that your pull request solves.
  Mention any new features, bug fixes or refactoring.

- **Relevant issues**: Reference any
  `related issues, pull requests and repositories <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls>`_.

- **Testing**: Explain whether new or updated tests are included.

- **Reversibility**: If you propose decisions that may be costly to reverse,
  list the reasons and suggest steps to reverse the changes if necessary.


Commit structure and messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO: Update with your own guidelines or drop if excessive

Use separate commits for each logical change,
and for changes to different components.
Prefix your commit messages with names of components they affect,
using the code tree structure,
e.g. start a commit that updates the ACME service with ``ACME/service:``.

Use `conventional commits <https://www.conventionalcommits.org/>`_
to ensure consistency across the project:

.. code-block:: none

   Ensure correct permissions and ownership for the content mounts
    
    * Work around an ACME issue regarding empty dirs:
      https://github.com/canonical/ACME/issues/12345
    
    * Ensure the source directory is owned by the user running a container.

   Links:
   - ...
   - ...


Such structure makes it easier to review contributions
and simplifies porting fixes to other branches.


Signing commits
~~~~~~~~~~~~~~~

.. TODO: Update with your suggestions or drop if excessive

To improve contribution tracking, we use the developer certificate of origin
(`DCO 1.1 <https://developercertificate.org/>`_) and require signed commits
(using the ``-S`` or ``--gpg-sign`` option) for all changes that go into the
ACME project.

.. code-block:: none

   git commit -S -m "acme/component: updated life cycle diagram"

Signed commits will have a GPG, SSH, or S/MIME signature that is
cryptographically verifiable, and will be marked with a "Verified" or
"Partially verified" badge in GitHub. This verifies that you made the changes or
have the right to commit it as an open-source contribution.

To set up locally signed commits and tags, see `GitHub Docs - About commit
signature verification <https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification>`_.

.. tip::

   You can configure your Git client to sign commits by default for any local
   repository by running ``git config --global commit.gpgsign true``.
   Once you have configured this, you no longer need to add ``-S`` to your
   commits explicitly.

   See `GitHub Docs - Signing commits <https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits>`_ for more information.

If you've made an unsigned commit and encounter the "Commits must have verified
signatures" error when pushing your changes to the remote:

1. Amend the most recent commit by signing it without changing the commit
   message, and push again:

   .. code-block:: none

      git commit --amend --no-edit -n -S
      git push
#. If you still encounter the same error, confirm that your GitHub account has
   been set up properly to sign commits as described in the `GitHub Docs - About
   commit signature verification <https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification>`_.

   .. tip::

      If you use SSH keys to sign your commits, make sure to add a "Signing Key"
      type in your GitHub account. See
      [GitHub Docs - Adding a new SSH key to your account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
      for more information.

Code
----

Formatting and linting
~~~~~~~~~~~~~~~~~~~~~~

.. TODO: Update with your linting configuration setup or drop if excessive

ACME relies on these formatting and linting tools:

- `TODO: Tool 1 <http://example.com>`_
- `TODO: Tool 2 <http://example.com>`_


To configure and run them:

.. code-block:: console

   TODO: lint command 1
   TODO: lint command 2


Structure
~~~~~~~~~

- **Check linked code elements**:
  Check that coupled code elements, files and directories are adjacent.
  For instance, store test data close to the corresponding test code.

- **Group variable declaration and initialisation**:
  Declare and initialise variables together
  to improve code organisation and readability.

- **Split large expressions**:
  Break down large expressions
  into smaller self-explanatory parts.
  Use multiple variables where appropriate
  to make the code more understandable
  and choose names that reflect their purpose.

- **Use blank lines for logical separation**:
  Insert a blank line between two logically separate sections of code.
  This improves its structure and makes it easier to understand.

- **Avoid nested conditions**:
  Avoid nesting conditions to improve readability and maintainability.

- **Remove dead code and redundant comments**:
  Drop unused or obsolete code and comments.
  This promotes a cleaner code base and reduces confusion.

- **Normalise symmetries**:
  Treat identical operations consistently, using a uniform approach.
  This also improves consistency and readability.


Best practices
~~~~~~~~~~~~~~

.. TODO: Update with your best practices or drop if excessive


Tests
-----

.. TODO: Update with your testing framework details or drop if excessive

All code contributions must include tests.

To run the tests locally before submitting your changes:

.. code-block:: console

   TODO: test command 1
   TODO: test command 2


Documentation
-------------

ACME's documentation is stored in the ``DOCDIR`` directory of the repository.
It is based on the `Canonical starter pack
<https://canonical-starter-pack.readthedocs-hosted.com/latest/>`_
and hosted on `Read the Docs <https://about.readthedocs.com/>`_.

For syntax help and guidelines,
refer to the Canonical style guides
(:ref:`reStructuredText <style-guide>` and :ref:`MyST <myst_style_guide>`).

In structuring,
the documentation employs the `Diátaxis <https://diataxis.fr/>`_ approach.

To run the documentation locally before submitting your changes:

.. code-block:: console

   make run


Automatic checks
~~~~~~~~~~~~~~~~

GitHub runs automatic checks on the documentation
to verify spelling, validate links and suggest inclusive language.

You can (and should) run the same checks locally:

.. code-block:: console

   make spelling
   make linkcheck
   make woke
