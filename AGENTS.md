# Coding Agent Instructions

- Always consider your work incomplete until the command `make format && make test` succeeds. The developer will start the agent in an environment in which those commands are available; if you find that not to be the case, report it to the developer.
- Follow existing conventions, idion, styles, etc. in the codebase. If you'd like to deviate from existing conventions, discuss it with the developer.
- If test failures appear to be caused by sandboxing or environment limitations, report them to the developer instead of adding workaround code. Developers will run tests independently and will tell coding agents if any outstanding issues remain.
- Never issue state-changing `git` commands without authorization from the developer.
- Order functions in modules, methods in classes, keys in dictionaries, items in lists, etc. lexicographically unless there is a specific reason for ordering them some other way.
- When writing unit tests, prefer use of the `@mark.parametrize` decorator from `pytest` to writing multiple tests that are largely identical.
