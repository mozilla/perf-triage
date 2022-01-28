# perf-triage
Tools used for triaging performance bugs.

## Setup

For convenience, you can use poetry to manage dependencies and virtual environments.

When running for the first time, you will need to [install poetry](https://python-poetry.org/docs/#installation) and then run `poetry install` to create the virtual environment and install dependencies.

Then, you can simply run `poetry run python` followed by the path to the script you'd like to run. For example, `poetry run python rotation.py`.

You can update the dependencies by running `poetry update` and can add dependencies using `poetry add`. See the [poetry documentation](https://python-poetry.org/docs/) for more details.

## rotation.py
Generate new triage rotation.

Run `poetry run python rotation.py`

## send-reminder.py
Send triage reminders.

Note: this script is a WIP and we're working on integrating it with the other scripts.

Run `poetry run python send-reminder.py` for details on running.
