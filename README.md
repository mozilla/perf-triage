# perf-triage
Tools used for triaging performance bugs.

`rotation.py` is the main script that runs regularly in CI to generate a new rotation, update the [performance triage rotation website](https://mozilla.github.io/perf-triage/), and post a reminder to Google Calendar.

## Development
The first time you run, you'll need to create a virtualenv and install the
dependencies:
```sh
# Create virtualenv
python3 -m venv venv

# Activate virtualenv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

You always need to run `rotation.py` from the activated virtualenv so if you start a new shell, be sure to activate it.

If you need to make changes to the Google Calendar (e.g. for testing), you may need to pass the `--production` flag to `rotation.py`: without it, the code will not access the Google Calendar API.

### Sending a triage reminder manually (for errors)
If `rotation.py` fails to send a triage reminder, you may need to send a reminder manually. Assuming you have downloaded the credentials to our Google Cloud project and installed the dependencies:
```sh
git fetch upstream && git checkout upstream/main # Get the latest cached rotation.
source venv/bin/activate
python3
>>> from rotation import *; add_gcal_reminder_manually('2022-08-09')
```

You will be prompted to select the rotation to send a reminder for.
