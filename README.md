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
If `rotation.py` fails to send a triage reminder, you may need to send a reminder manually. Since this is intended as a back-up only, it's not graceful. You will need to start a python interpreter and call the functions manually, e.g.:
```python
import gcal
creds = gcal.auth_as_user()
service = gcal.get_calendar_service(creds)
gcal.send_triage_reminder(service, ...)
```
