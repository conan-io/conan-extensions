"""
Validate the Conan Statuspage commands

NOTE: In order to mock requests, we needed to invoke conans.conan.run() instead of running subprocess.run() directly.
      The subcommand is included as module on the fly by Conan command, so we can't mock it directly when using subprocess.run().
      As alternative, we import Conan module and invoke its run() method directly, so we can access requests and mock it.
"""

import tempfile
from responses import matchers
import os
import responses
import pytest
import sys
from unittest.mock import patch
from tools import run
from conans.conan import run as conan_run


@pytest.fixture(autouse=True)
def conan_setup():
    """
    Setup Conan environment for testing.
    """
    old_env = dict(os.environ)
    conan_home = tempfile.mkdtemp(suffix='conans')
    env_vars = {"CONAN_HOME": conan_home}
    os.environ.update(env_vars)
    cwd = os.getcwd()
    os.chdir(conan_home)
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")
    try:
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


@responses.activate
def test_create_incident():
    """
    Test if capable to create a new incident in Status Page.
    """
    json_response = {
        "id": "p31zjtct2jer",
        "components": [
            {
              "id": "component0xs0da",
              "page_id": "page0xc0ffee",
              "group_id": "group0xc0ffee",
              "created_at": "2023-12-20T07:50:03Z",
              "updated_at": "2023-12-20T07:50:03Z",
              "group": True,
              "name": "API Service",
              "description": "API Service Description",
              "position": 0,
              "status": "minor_outage",
              "showcase": True,
              "only_show_if_degraded": True,
              "automation_email": "user@acme.com",
              "start_date": "2023-12-20"
            }
        ],
        "created_at": "2023-12-20T07:50:03Z",
        "impact": "minor",
        "impact_override": "minor",
        "incident_updates": [
            {
              "id": "incident0xid1",
              "incident_id": "incident0xid1",
              "affected_components": [
                {
                  "code": "component0xs0da",
                  "name": "API Service",
                  "old_status": "operational",
                  "new_status": "minor"
                }
              ],
              "body": "I think, therefore I am",
              "created_at": "2023-12-20T07:50:03Z",
              "custom_tweet": "string",
              "deliver_notifications": False,
              "display_at": "2023-12-20T07:50:03Z",
              "status": "investigating",
              "tweet_id": "string",
              "twitter_updated_at": "2023-12-20T07:50:03Z",
              "updated_at": "2023-12-20T07:50:03Z",
              "wants_twitter_update": False
            }
        ],
        "monitoring_at": "2023-12-20T07:50:03Z",
        "name": "Cogito, ergo sum",
        "page_id": "page0xc0ffee",
        "scheduled_auto_completed": False,
        "scheduled_auto_in_progress": False,
        "scheduled_for": "2013-05-07T03:00:00.007Z",
        "auto_transition_deliver_notifications_at_end": False,
        "auto_transition_deliver_notifications_at_start": False,
        "auto_transition_to_maintenance_state": False,
        "auto_transition_to_operational_state": False,
        "scheduled_remind_prior": False,
        "scheduled_reminded_at": "2023-12-20T07:50:03Z",
        "scheduled_until": "2013-05-07T06:00:00.007Z",
        "shortlink": "http://stspg.io/803310a12",
        "status": "identified",
        "updated_at": "2023-12-20T07:50:03Z",
        "reminder_intervals": "[3, 6, 12, 24]"
    }
    responses.add(responses.POST, 'https://api.statuspage.io/v1/pages/page0xc0ffee/incidents', json=json_response,
                  match=[matchers.json_params_matcher({
                      "incident": {
                          "body": "I think, therefore I am",
                          "component_ids": ["component0xs0da"],
                          "components": {"component0xs0da": "major_outage"},
                          "impact_override": "minor",
                          "name": "Cogito, ergo sum",
                          "status": "identified"
                      }
                  })])

    test_args = ["conan", "statuspage:create-incident", "-tk", "t0xfoobar", "-p", "page0xc0ffee", "-c", "component0xs0da", "-t", "Cogito, ergo sum", "-m", "I think, therefore I am", "-s", "identified", "-i", "minor", "-cs", "major_outage"]
    with patch.object(sys, 'argv', test_args):
        try:
            conan_run()
        except SystemExit as error:
            assert error.code == 0


@responses.activate
def test_update_incident():
    """
    Test if capable to update an existing incident in Status Page.
    """
    json_response = {
        "id": "inc0xid001",
        "components": [
            {
              "id": "component0xs0da",
              "page_id": "page0xc0ffee",
              "group_id": "group0xc0ffee",
              "created_at": "2023-12-20T07:50:03Z",
              "updated_at": "2023-12-20T07:50:03Z",
              "group": True,
              "name": "API Service",
              "description": "API Service Description",
              "position": 0,
              "status": "degraded_performance",
              "showcase": True,
              "only_show_if_degraded": True,
              "automation_email": "user@acme.com",
              "start_date": "2023-12-20"
            }
        ],
        "created_at": "2023-12-20T07:50:03Z",
        "impact": "minor",
        "impact_override": "minor",
        "incident_updates": [
            {
              "id": "incident0xid1",
              "incident_id": "incident0xid1",
              "affected_components": [
                {
                  "code": "component0xs0da",
                  "name": "API Service",
                  "old_status": "operational",
                  "new_status": "minor"
                }
              ],
              "body": "Working on it",
              "created_at": "2023-12-20T07:50:03Z",
              "custom_tweet": "string",
              "deliver_notifications": False,
              "display_at": "2023-12-20T07:50:03Z",
              "status": "degraded_performance",
              "tweet_id": "string",
              "twitter_updated_at": "2023-12-20T07:50:03Z",
              "updated_at": "2023-12-20T07:50:03Z",
              "wants_twitter_update": False
            }
        ],
        "monitoring_at": "2023-12-20T07:50:03Z",
        "name": "Cogito, ergo sum",
        "page_id": "page0xc0ffee",
        "scheduled_auto_completed": False,
        "scheduled_auto_in_progress": False,
        "scheduled_for": "2013-05-07T03:00:00.007Z",
        "auto_transition_deliver_notifications_at_end": False,
        "auto_transition_deliver_notifications_at_start": False,
        "auto_transition_to_maintenance_state": False,
        "auto_transition_to_operational_state": False,
        "scheduled_remind_prior": False,
        "scheduled_reminded_at": "2023-12-20T07:50:03Z",
        "scheduled_until": "2013-05-07T06:00:00.007Z",
        "shortlink": "http://stspg.io/803310a12",
        "status": "monitoring",
        "updated_at": "2023-12-20T07:50:03Z",
        "reminder_intervals": "[3, 6, 12, 24]"
    }
    responses.add(responses.PATCH, 'https://api.statuspage.io/v1/pages/page0xc0ffee/incidents/inc0xid001', json=json_response,
                  match=[matchers.json_params_matcher({
                      "incident": {
                          "body": "Working on it",
                          "component_ids": ["component0xs0da"],
                          "components": {"component0xs0da": "degraded_performance"},
                          "impact_override": "minor",
                          "status": "monitoring"
                      }
                  })])

    test_args = ["conan", "statuspage:update-incident", "-tk", "t0xfoobar", "-p", "page0xc0ffee", "-c", "component0xs0da", "-ic", "inc0xid001", "-m", "Working on it", "-s", "monitoring", "-i", "minor", "-cs", "degraded_performance"]
    with patch.object(sys, 'argv', test_args):
        try:
            conan_run()
        except SystemExit as error:
            assert error.code == 0


@responses.activate
def test_schedule_maintenance():
    """
    Test if capable to schedule a maintenance window in Status Page.
    """
    json_response = {
        "id": "p31zjtct2jer",
        "components": [
            {
              "id": "component0xs0da",
              "page_id": "page0xc0ffee",
              "group_id": "group0xc0ffee",
              "created_at": "2023-12-20T07:50:03Z",
              "updated_at": "2023-12-20T07:50:03Z",
              "group": True,
              "name": "API Service",
              "description": "API Service Description",
              "position": 0,
              "status": "minor_outage",
              "showcase": True,
              "only_show_if_degraded": True,
              "automation_email": "user@acme.com",
              "start_date": "2023-12-20"
            }
        ],
        "created_at": "2023-12-20T07:50:03Z",
        "impact": "minor",
        "impact_override": "minor",
        "incident_updates": [
            {
              "id": "incident0xid1",
              "incident_id": "incident0xid1",
              "affected_components": [
                {
                  "code": "component0xs0da",
                  "name": "API Service",
                  "old_status": "operational",
                  "new_status": "minor"
                }
              ],
              "body": "I think, therefore I am",
              "created_at": "2023-12-20T07:50:03Z",
              "custom_tweet": "string",
              "deliver_notifications": False,
              "display_at": "2023-12-20T07:50:03Z",
              "status": "investigating",
              "tweet_id": "string",
              "twitter_updated_at": "2023-12-20T07:50:03Z",
              "updated_at": "2023-12-20T07:50:03Z",
              "wants_twitter_update": False
            }
        ],
        "monitoring_at": "2023-12-20T07:50:03Z",
        "name": "Cogito, ergo sum",
        "page_id": "page0xc0ffee",
        "scheduled_auto_completed": False,
        "scheduled_auto_in_progress": False,
        "scheduled_for": "2013-05-07T03:00:00.007Z",
        "auto_transition_deliver_notifications_at_end": False,
        "auto_transition_deliver_notifications_at_start": False,
        "auto_transition_to_maintenance_state": False,
        "auto_transition_to_operational_state": False,
        "scheduled_remind_prior": False,
        "scheduled_reminded_at": "2023-12-20T07:50:03Z",
        "scheduled_until": "2013-05-07T06:00:00.007Z",
        "shortlink": "http://stspg.io/803310a12",
        "status": "identified",
        "updated_at": "2023-12-20T07:50:03Z",
        "reminder_intervals": "[3, 6, 12, 24]"
    }
    responses.add(responses.POST, 'https://api.statuspage.io/v1/pages/page0xc0ffee/incidents', json=json_response,
                  match=[matchers.json_params_matcher({
                      "incident": {
                          "auto_transition_deliver_notifications_at_end": True,
                          "auto_transition_deliver_notifications_at_start": False,
                          "auto_transition_to_maintenance_state": True,
                          "auto_transition_to_operational_state": True,
                          "body": "I think, therefore I am",
                          "component_ids": ["component0xs0da"],
                          "components": {"component0xs0da": "under_maintenance"},
                          "deliver_notifications": True,
                          "impact_override": "maintenance",
                          "name": "Cogito, ergo sum",
                          "scheduled_auto_completed": False,
                          "scheduled_auto_in_progress": True,
                          "scheduled_remind_prior": True,
                          "status": "scheduled"
                      }
                  }, strict_match=False)])


    test_args = ["conan", "statuspage:schedule-maintenance", "-tk", "t0xfoobar", "-p", "page0xc0ffee", "-c", "component0xs0da", "-t", "Cogito, ergo sum", "-m", "I think, therefore I am"]
    with patch.object(sys, 'argv', test_args):
        try:
            conan_run()
        except SystemExit as error:
            assert error.code == 0
    assert len(responses.calls) == 1
    assert "scheduled_for" in responses.calls[0].request.body.decode('utf-8')
    assert "scheduled_until" in responses.calls[0].request.body.decode('utf-8')


@responses.activate
def test_resolve_incident():
    """Test if capable to resolve an existing incident in Status Page."""
    json_response = {
            "id": "incident0xf00bar",
            "components": [
                {
                    "id": "component0xs0da",
                    "page_id": "page0xc0ffee",
                    "group_id": "group0x5ca1ab1e",
                    "created_at": "2023-12-19T08:44:40Z",
                    "updated_at": "2023-12-19T08:44:40Z",
                    "group": True,
                    "name": "API Service",
                    "description": "API Service",
                    "position": 0,
                    "status": "operational",
                    "showcase": True,
                    "only_show_if_degraded": False,
                    "automation_email": "email@acme.com",
                    "start_date": "2023-12-19"
                }
            ],
            "created_at": "2023-12-19T08:44:40Z",
            "impact": "none",
            "impact_override": "none",
            "monitoring_at": "2023-12-19T08:44:40Z",
            "name": "Cogito, ergo sum",
            "page_id": "page0xc0ffee",
            "scheduled_auto_completed": False,
            "scheduled_auto_in_progress": False,
            "scheduled_for": "2013-05-07T03:00:00.007Z",
            "auto_transition_deliver_notifications_at_end": False,
            "auto_transition_deliver_notifications_at_start": True,
            "auto_transition_to_maintenance_state": True,
            "auto_transition_to_operational_state": True,
            "scheduled_remind_prior": True,
            "scheduled_reminded_at": "2023-12-19T08:44:40Z",
            "status": "resolved",
            "updated_at": "2023-12-19T08:44:40Z",
            "shortlink": "http://stspg.io/803310a12",
            "reminder_intervals": "[3, 6, 12, 24]"
    }
    responses.add(responses.PATCH, 'https://api.statuspage.io/v1/pages/page0xc0ffee/incidents/incident0xf00bar',
                  json=json_response,
                  match=[matchers.json_params_matcher({
                      "incident": {
                          "component_ids": ["component0xs0da"],
                          "components": {"component0xs0da": "operational"},
                          "impact_override": "none",
                          "status": "resolved"
                      }
                  })])
    argv = [
        "conan",
        "statuspage:resolve-incident",
        "--token=0xdeadbeef",
        "--page=page0xc0ffee",
        "--components=component0xs0da",
        "--event=incident",
        "--incident=incident0xf00bar",
    ]
    with patch.object(sys, 'argv', argv):
        try:
            conan_run()
        except SystemExit as error:
            assert error.code == 0
