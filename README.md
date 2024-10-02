### IMPORTANT NOTE
this script cannot be run on Windows (work in progress but may never happen)

### Usage:
* install the dependencies with `python3 -m pip install -r requirements.txt`
* configure the env file (default env file is `./.env`, it's location can be changed in the script itself)
* run the script with `python3 ./ws_remote_logs.py`
* check the `ws_remote_logs.txt` to get the results, or `ws_remote_logs.log` to see the script and websocket logs

### ENV File:

| property | type | example | description |
| --- | --- | --- | --- |
| MIST_HOST | str | api.mist.com | Mist API Host |
| MIST_APITOKEN | str | xxxxxxxxxxxxxxxxxxx | Super User API Token |
| MIST_ORG_ID | str | 9777c1a0-xxxxx-xxxxx-xxxxx-xxxxxxxxxxxx | Mist API Org ID |
| MIST_SITE_ID | str | 978c48e6-xxxxx-xxxxx-xxxxx-xxxxxxxxxxxx | Mist Site ID where the device is assigned to |
| MIST_DEVICE_ID | str | 0000000-xxxxx-xxxxx-xxxxx-xxxxxxxxxxxx | Mist Device ID (must be a Junos Device - EX or SRX) |
| LOG_MATCH | str | "\\"IKE negotiation failed with error: Authentication failed\\"" | string to match in the device logs. |

**Note:**
If the `LOG_MATCH` property has spaces, be sure to add all the required double quotes like in the example

example:
```
MIST_HOST=api.mist.com
MIST_APITOKEN=xxxxxxxxxxxxxxxxxxx
MIST_ORG_ID=9777c1a0-xxxxx-xxxxx-xxxxx-xxxxxxxxxxxx
MIST_SITE_ID=978c48e6-xxxxx-xxxxx-xxxxx-xxxxxxxxxxxx
MIST_DEVICE_ID=00000000-xxxxx-xxxxx-xxxxx-xxxxxxxxxxxx
LOG_MATCH = "\"IKE negotiation failed with error: Authentication failed\""
```
