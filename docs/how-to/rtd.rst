.. _rtd:

Set up Read the Docs
====================

For Canonical-specific information on how to set up your documentation on Read the Docs, see the `Read the Docs at Canonical <https://library.canonical.com/documentation/read-the-docs-at-canonical>`_ and `How to publish documentation on Read the Docs <https://library.canonical.com/documentation/publish-on-read-the-docs>`_ guides.

In general, after enabling the starter pack for your documentation, follow these steps to build and publish your documentation on Read the Docs:

1. Make sure your documentation :ref:`builds without errors or warnings <build-clean>`.
#. Log into Read the Docs.
#. In your account settings, navigate to :guilabel:`Connected services` and check that your GitHub account is listed.
   If it's not listed, add a connection to GitHub. See `How to connect your Read the Docs account to your Git provider`_.
#. Use the `manual import`_ to create a project.
#. Specify the path to the :file:`.readthedocs.yaml` file for your build.
   To do this, navigate to :guilabel:`Admin` > :guilabel:`Settings` and specify the path under "Path for ``.readthedocs.yaml``".
   
   For example, if your documentation folder is :file:`docs/`, specify the path as ``docs/.readthedocs.yaml``.
#. Update the relative paths in the :file:`.readthedocs.yaml` file to match the structure of your project. You might need to update the file paths specified in the following fields:

   * ``job.post_checkout``
   * ``sphinx.configuration``
   * ``python.install.requirements``

After this initial setup, your documentation should build successfully if your project is hosted from a public repository.
If you get any errors, check the build log for indications on what the problem is.

If your project was imported from a private repository, your initial build will fail because Read the Docs won't have access to clone the repository.
You need to copy your project's private key from Read the Docs and add it as a deploy key to the repository, then re-run the build in Read the Docs.

Configure the webhook
---------------------

If you have administrator privileges for the GitHub repository that you are adding, the integration webhook (which is responsible for automatically building the documentation when the repository changes) is created automatically.

If you don't have administrator privileges, the webhook must be set up by someone who does.
The person with administrator privileges must have connected their Read the Docs account to GitHub.
See `How to connect your Read the Docs account to your Git provider`_.

See `How to manually configure a Git repository integration`_ if you want to set up the webhook manually.

Make your documentation public
------------------------------

By default, Read the Docs publishes your documentation for logged-in users only.

To make the documentation public, you must configure the privacy level for each version of the documentation separately.
You can do this by navigating to the :guilabel:`Versions` tab and changing the :guilabel:`Privacy Level` for each version.

Enable PR previews
------------------

To make Read the Docs automatically build your documentation when a pull request is opened or updated on GitHub, enable PR reviews for your project.

To do so, navigate to :guilabel:`Admin` > :guilabel:`Settings` and select :guilabel:`Build pull requests for this project`.

Read the Docs will then automatically build the documentation for each pull request, and the link to the output will be available as one of the checks in the pull request.
