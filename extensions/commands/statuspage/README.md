## Status Page report commands

In order to update the stats.conan.io page, the Atlassian Status Page API is wrapped by these commands. It can be re-used for any other project.

### Authentication

To obtain a Token API, you need to go to your statuspage.io account and generate a new token.
It should be available at the following URL: `https://manage.statuspage.io/organizations/<your_organization>/api-info`
For more information, please, read the [Authentication](https://developer.statuspage.io/#section/Authentication) documentation.

#### Keychain (Only macOS)

Storing token as environment variable is too risky, so it's recommended to use the keychain to store it.
To do so, you can use the following command:

```
$ security add-generic-password -a $USER -s statuspage-token -w <statuspage-api-token> secrets.keychain
```

The `secrets.keychain` is the name of the keychain where the token will be stored.

All commands have support to automatically retrieve the token from the keychain, so you don't need to pass it as a parameter.


### Commands

All commands are available under the `statuspage` namespace. All them are wrappers to the [Status Page API](https://developer.statuspage.io/).

#### [Create a new incident](cmd_create_incident.py)

In case some unexpect event occurs (e.g server failure, Artifactory downtime), this command can be used to create a new incident in the status page.

Incidents are created in the same time as reported, and may affect more than one component (e.g Artifactory and ConanCenter) at same time.

**Parameters**
- **token** _Required_: The Status Page API Token.
- **page** _Required_: The Status Page - Page ID. It works like an ID for your status page.
- **components** _Optional_: A list of components IDs that are affected by the incident.
- **component-status** _Optional_: The status of the components affected by the incident. Choices: operational, degraded_performance, partial_outage, major_outage.
- **status** _Optional_: The working status of the incident. Choices: investigating, identified, monitoring, resolved.
- **impact** _Optional_: The impact of the incident. Choices: none, maintenance, minor, major, critical.
- **title** _Optional_: The title of the incident.
- **message** _Optional_: The message of the incident. No new lines are allowed.
- **ignore-ssl** _Optional_: Ignore SSL verification.
- **keychain-user** _Optional_: Keychain username.
- **keychain-service** _Optional_: Keychain name used to store Status page token. Default: statuspage-token.


```
$ conan statuspage:create_incident --token=<yourapitoken> --page=<yourpageid> -s investigating -i major -cs major_outage -c <yourcomponentid> -t "Critical server error" -m "Our jenkins is down right now, but we are working on it. Sorry, we will update asap!"
Created incident:
Incident ID: hc9qf30zv16c
Created at: 2023-12-19T15:56:32Z
Name: Jenkins is overloaded
Status: investigating
Impact: major
URL: https://stspg.io/fhwg565ns7x9
```
