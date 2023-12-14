Fork and PR Model
=================

Overview
--------

Contributions to the ``workflow-tools`` project are made via a `Fork <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks>`_ and `Pull Request (PR) <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_ model. GitHub provides a thorough description of this contribution model in their `Contributing to projects` `Quickstart <https://docs.github.com/en/get-started/quickstart/contributing-to-projects>`_, but the steps, with respect to ``workflow-tools`` contributions, can be summarized as:

#. `Fork <https://docs.github.com/en/get-started/quickstart/contributing-to-projects#forking-a-repository>`_ the ``workflow-tools`` `repository <https://github.com/ufs-community/workflow-tools>`_ into your personal GitHub account.
#. `Clone <https://docs.github.com/en/get-started/quickstart/contributing-to-projects#cloning-a-fork>`_ your fork onto your development system.
#. `Create a branch <https://docs.github.com/en/get-started/quickstart/contributing-to-projects#creating-a-branch-to-work-on>`_ in your clone for your changes.
#. `Make, commit, and push changes <https://docs.github.com/en/get-started/quickstart/contributing-to-projects#making-and-pushing-changes>`_ in your clone / to your fork. (Refer to the :doc:`Developer Setup <developer_setup>` page for setting up a development shell, formatting and testing your code, etc.)
#. When your work is complete, `create a pull request <https://docs.github.com/en/get-started/quickstart/contributing-to-projects#making-a-pull-request>`_ to merge your changes.

For future contributions, you may delete and then re-create your fork, or configure the official ``workflow-tools`` repo as `remote repository <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-repository-for-a-fork>`_ on your clone and `sync upstream changes <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork>`_ to stay up-to-date with the official repo.

Specifics for ``workflow-tools``
--------------------------------

When creating your PR, please follow these guidelines, specific to the ``workflow-tools`` project:

* Ensure that your PR is targeting base repository ``ufs-community/workflow-tools`` and base branch ``develop``.
* Your PR's **Add a description** field will appear pre-populated with a template that you should complete. Provide an informative synopsis of your contribution, then mark appropriate checklist items by placing an "x" between their square brackets. You may tidy up the description by removing boilerplate text and non-selected checklist items.
* Use the pull-down arrow on the green button below the description to initially create a `Draft pull request <https://github.blog/2019-02-14-introducing-draft-pull-requests/>`_.
* Once your draft PR is open, visit its **Files changed** tab and add comments on any lines of code that you think reviewers will benefit from. Try to save time by proactively answering questions you suspect reviewers will ask.
* Once your draft PR is marked up with your comments, return to the **Conversation** tab and click the **Ready for review** button.

A default set of reviewers will automatically be added to your PR. You may add others, if appropriate. Reviewers may make comments, ask questions, or request changes on your PR. Respond to these as needed, making commits in your clone and pushing to your fork/branch. Your PR will automatically be updated when commits are pushed to its source branch in your fork, so reviewers will immediately see your updates.

Merging
-------

Your PR is ready to merge when:

#. It has been approved by a required number of ``workflow-tools`` core-developer reviewers.
#. All conversations have been marked as resolved.
#. All required checks have passed.

These criteria and their current statuses are detailed in a section at the bottom of your PR's **Conversation** tab. Checks take some time to run, so please be patient.

If you have write access to the ``workflow-tools`` repo, you may merge your PR yourself once the above conditions are met. If not, a ``workflow-tools`` core developer will perform the merge for you.

Need Help?
----------

Please use comments in the **Conversation** tab of your PR to ask for help with any difficulties you encounter using this procedure!
