from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
from flask import Flask, request, make_response, Response
import os
import json
import pprint

app = Flask(__name__)

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_workspace_token = os.environ["SLACK_WORKSPACE_TOKEN"]
slack_client = SlackClient(slack_bot_token)
    #refresh_token=slack_refresh_token,
    #client_id=slack_client_id,
    #client_secret=slack_client_secret,
    #token_update_callback=token_update_callback)


def token_update_callback(update_data):
    print("Enterprise ID: {}".format(update_data["enterprise_id"]))
    print("Workspace ID: {}".format(update_data["team_id"]))
    print("Access Token: {}".format(update_data["access_token"]))
    print("Access Token expires in (ms): {}".format(update_data["expires_in"]))

# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "hi" in message.get('text'):
        channel = message["channel"]
        message = "Hello <@%s>! :tada:" % message["user"]
        slack_client.api_call("chat.postMessage", channel=channel, text=message)

@slack_events_adapter.on("team_join")
def team_join(data):
    mention_bot(data)

@slack_events_adapter.on("app_mention")
def mention_bot(data):
    event = data["event"]
    user= event["user"]
    channel = event["channel"]
    print("User/Channel: " + user + "/"+channel)
    dm_data = slack_client.api_call(
        "conversations.open",
        users="{}".format(user))

    if dm_data["ok"] == True:
        channel = dm_data["channel"]["id"]
        welcome_message(channel)
    else:
        print(dm_data["error"])

def welcome_message(chan = "CEJFLVBKJ"):
    #CEJFLVBKJ is test channel
    slack_client.api_call(
        "chat.postMessage",
        channel=chan,
        text="Hi! Welcome to OT Robotics! What team are you on/do you plan on joining?",
        attachments=[
        {
            "text": "Which team?",
            "fallback": "You are unable to choose a team",
            "callback_id": "team_choice",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "actions": [
                {
                    "name": "team",
                    "text": "1334 (Red Devils)",
                    "type": "button",
                    "value": "1334"
                },
                {
                    "name": "team",
                    "text": "1374 (Amped Up)",
                    "type": "button",
                    "value": "1374"
                },
                {
                    "name": "team",
                    "text": "Neither, ask me later",
                    "style": "danger",
                    "type": "button",
                    "value": "neither",
                    "confirm": {
                        "title": "Are you sure?",
                        "text": "You can set your team later by sending me a DM!",
                        "ok_text": "Yes",
                        "dismiss_text": "No"
                    }
                }
            ]
        }]
    )

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))


@app.route("/message_options", methods=["POST"])
def message_options():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Dictionary of menu options which will be sent as JSON
    menu_options = {
        "options": [
            {
                "text": "Cappuccino",
                "value": "cappuccino"
            },
            {
                "text": "Latte",
                "value": "latte"
            }
        ]
    }

    # Load options dict as JSON and respond to Slack
    return Response(json.dumps(menu_options), mimetype='application/json')

@app.route("/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Check to see what the user's selection was and update the message accordingly
    selection_name = form_json["actions"][0]["name"]
    selection = form_json["actions"][0]["value"]

    team_selection_flow(form_json, selection_name, selection)
    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


def join_subteam(subteam, user, chan):

    subteams = {
    "build":"",
    "design":"",
    "programming":"",
    "electrical":"",
    "media":"",
    "awards":"",
    "scouting":"",
    "business":"",
    }

    users = slack_client.api_call(
        "usergroups.users.list",
        usergroup=subteams[subteam],
        include_disabled=False)["users"]

    if user in users:
        slack_client.api_call(
        "chat.postMessage",
        channel = chan,
        text = "You're already in the {0} subteam!".format(subteam),
        attachments = [])
        return

    users.append(user)

    slack_client.api_call(
        "usergroups.users.update",
        token=slack_workspace_token,
        usergroup=subteams[subteam],
        users=','.join(users))

    slack_client.api_call(
        "chat.postMessage",
        channel = chan,
        text = "Awesome! Welcome to the {0} subteam!".format(subteam),
        attachments = [])

def team_selection_flow(form_json, selection_name, selection):
    user = form_json["user"]["id"]
    chan = form_json["channel"]["id"]

    print(user)
    if selection_name == "team":
        team_choice = selection
        if team_choice == "neither":
            response = slack_client.api_call(
                  "chat.update",
                  channel=form_json["channel"]["id"],
                  ts=form_json["message_ts"],
                  text="Indecision is okay!",
                  attachments=[]
                )
            return make_response("", 200)
        elif team_choice == "1334":
            print("1334 chosen")
            # Set user group
        elif team_choice == "1374":
            print("1374 chosen")
            # Set user group
        response = slack_client.api_call(
              "chat.update",
              channel=form_json["channel"]["id"],
              ts=form_json["message_ts"],
              text="You can choose any subteams you'd like to join below.",
              attachments=[
                {
                    "text": "Choose a subteam",
                    "fallback": "You are unable to choose a subteam",
                    "callback_id": "subteam_choice",
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "subteam",
                            "text": "Programming",
                            "type": "button",
                            "value": "programming"
                        },
                        {
                            "name": "subteam",
                            "text": "Design",
                            "type": "button",
                            "value": "design"
                        },
                        {
                            "name": "subteam",
                            "text": "Electrical",
                            "type": "button",
                            "value": "electrical"
                        },
                        {
                            "name": "subteam",
                            "text": "Other...",
                            "type": "button",
                            "value": "other"
                        },
                        {
                            "name": "subteam",
                            "text": "No Thanks",
                            "style": "danger",
                            "type": "button",
                            "value": "none"
                        }
                    ]
                }
            ] # empty `attachments` to clear the existing massage attachments
        )
    elif selection_name == "subteam":
        subteam_choice = selection
        if subteam_choice == "other":
            response = slack_client.api_call(
                  "chat.update",
                  channel=form_json["channel"]["id"],
                  ts=form_json["message_ts"],
                  text="You can choose any subteams you'd like to join below.",
                  attachments=[
                    {
                        "text": "Choose a subteam",
                        "fallback": "You are unable to choose a subteam",
                        "callback_id": "subteam_choice",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            {
                                    "name": "subteam",
                                    "text": "Awards",
                                    "type": "button",
                                    "value": "awards"
                                },
                                {
                                    "name": "subteam",
                                    "text": "Business",
                                    "type": "button",
                                    "value": "business"
                                },
                                {
                                    "name": "subteam",
                                    "text": "Scouting",
                                    "type": "button",
                                    "value": "scouting"
                                },
                                {
                                    "name": "subteam",
                                    "text": "Media",
                                    "type": "button",
                                    "value": "media"
                                },
                                {
                                    "name": "subteam",
                                    "text": "No Thanks",
                                    "style": "danger",
                                    "type": "button",
                                    "value": "none"
                                }    
                        ]
                    }
                ] # empty `attachments` to clear the existing massage attachments
            )
        elif subteam_choice == "none":
            response = slack_client.api_call(
                  "chat.update",
                  channel=form_json["channel"]["id"],
                  ts=form_json["message_ts"],
                  text="Send me a DM if you'd like to join a subteam in the future!",
                  attachments=[] # empty `attachments` to clear the existing massage attachments
            )
        else:
            subteam_choice = selection
            print("Subteam: " + subteam_choice)
            join_subteam(subteam_choice, user, chan)
            response = slack_client.api_call(
                  "chat.update",
                  channel=form_json["channel"]["id"],
                  ts=form_json["message_ts"],
                  text="You can choose any subteams you'd like to join below.",
                  attachments=[
                    {
                        "text": "Choose a subteam",
                        "fallback": "You are unable to choose a subteam",
                        "callback_id": "subteam_choice",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            {
                                "name": "subteam",
                                "text": "Programming",
                                "type": "button",
                                "value": "programming"
                            },
                            {
                                "name": "subteam",
                                "text": "Design",
                                "type": "button",
                                "value": "design"
                            },
                            {
                                "name": "subteam",
                                "text": "Electrical",
                                "type": "button",
                                "value": "electrical"
                            },
                            {
                                "name": "subteam",
                                "text": "Other...",
                                "type": "button",
                                "value": "other"
                            },
                            {
                                "name": "subteam",
                                "text": "No Thanks",
                                "style": "danger",
                                "type": "button",
                                "value": "none"
                            }
                        ]
                    }
                ] # empty `attachments` to clear the existing massage attachments
            )


# Flask server on port 3000
if __name__ == "__main__":
    app.run(port=3000)

