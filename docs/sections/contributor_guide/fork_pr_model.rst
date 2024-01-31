Fork and PR Model
=================

Overview
--------

Contributions to the ``uwtools`` project are made via a :github-docs:`Fork<pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks>` and :github-docs:`Pull Request (PR)<pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>` model. GitHub provides a thorough description of this contribution model in their `Contributing to a project` :github-docs:`Quickstart<get-started/exploring-projects-on-github/contributing-to-a-project>`, but the steps, with respect to ``uwtools`` contributions, can be summarized as:

#. :github-docs:`Fork<get-started/exploring-projects-on-github/contributing-to-a-project#forking-a-repository>` the :uwtools:`uwtools repository<>` into your personal GitHub account.
#. :github-docs:`Clone<get-started/exploring-projects-on-github/contributing-to-a-project>` your fork onto your development system.
#. :github-docs:`Create a branch<get-started/exploring-projects-on-github/contributing-to-a-project#creating-a-branch-to-work-on>` in your clone for your changes.
#. :github-docs:`Make, commit, and push changes<get-started/exploring-projects-on-github/contributing-to-a-project#making-and-pushing-changes>` in your clone / to your fork. (Refer to the :doc:`Developer Setup <developer_setup>` page for setting up a development shell, formatting and testing your code, etc.)
#. When your work is complete, :github-docs:`create a pull request<get-started/exploring-projects-on-github/contributing-to-a-project#making-a-pull-request>` to merge your changes.

For future contributions, you may delete and then recreate your fork or configure the official ``uwtools`` repository as a :github-docs:`remote repository<pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-repository-for-a-fork>` on your clone and :github-docs:`sync upstream changes<pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork>` to stay up-to-date with the official repository.

Specifics for ``uwtools``
-------------------------

When creating your PR, please follow these guidelines, specific to the ``uwtools`` project:

* Ensure that your PR is targeting base repository ``ufs-community/uwtools`` and base branch ``main``.
* Your PR's **Add a description** field will appear pre-populated with a template that you should complete. Provide an informative synopsis of your contribution, then mark appropriate checklist items by placing an "x" between their square brackets. You may tidy up the description by removing boilerplate text and non-selected checklist items.
* Use the pull-down arrow on the green button below the description to initially create a :github-docs:`draft pull request<pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests>`.
* Once your draft PR is open, visit its **Files changed** tab and add comments on any lines of code that you think reviewers will benefit from. Try to save time by proactively answering questions you suspect reviewers will ask.
* Once your draft PR is marked up with your comments, return to the **Conversation** tab and click the **Ready for review** button.

A default set of reviewers will automatically be added to your PR. You may add others, if appropriate. Reviewers may make comments, ask questions, or request changes on your PR. Respond to these as needed, making commits in your clone and pushing to your fork/branch. Your PR will automatically be updated when commits are pushed to its source branch in your fork, so reviewers will immediately see your updates.

Merging
-------

Your PR is ready to merge when:

#. It has been approved by a required number of ``uwtools`` core-developer reviewers.
#. All conversations have been marked as resolved.
#. All required checks have passed.

These criteria and their current statuses are detailed in a section at the bottom of your PR's **Conversation** tab. Checks take some time to run, so please be patient.

If you have write access to the ``uwtools`` repo, you may merge your PR yourself once the above conditions are met. If not, a ``uwtools`` core developer will perform the merge for you.

Need Help?
----------

Please use comments in the **Conversation** tab of your PR to ask for help with any difficulties you encounter using this process!
