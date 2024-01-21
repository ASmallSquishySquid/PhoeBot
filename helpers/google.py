from dataclasses import dataclass
import datetime
import os.path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from helpers import constants

@dataclass
class Calendar():
    id: str
    summary: str

@dataclass
class Event():
    id: str
    start: str
    summary: str
    reminders: List[int] = None

@dataclass
class TaskList():
    id: str
    title: str

@dataclass
class Task():
    id: str
    title: str
    parent: str = None
    due: str = None

class Google():
    credentials = None
    SCOPES = ["https://www.googleapis.com/auth/tasks.readonly",
              "https://www.googleapis.com/auth/calendar.readonly"]

    @classmethod
    def startup(cls) -> None:
        """Sets up the OAuth 2 credentials."""        
        package_dir = os.path.abspath(os.path.dirname(__file__))
        credential_path = os.path.join(
            package_dir, "..", "..", constants.RESOURCE_FOLDER, "google_credentials.json")
        token_path = os.path.join(
            package_dir, "..", "..", constants.RESOURCE_FOLDER, "google_token.json")
        if os.path.exists(token_path):
            cls.credentials = Credentials.from_authorized_user_file(token_path, cls.SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not cls.credentials or not cls.credentials.valid:
            if cls.credentials and cls.credentials.expired and cls.credentials.refresh_token:
                cls.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credential_path, cls.SCOPES,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob')

                auth_uri, _ = flow.authorization_url()
                print(f'Please visit {auth_uri} on your local computer')

                # The user will get an authorization code. This code is used to get the
                # access token.
                code = input('Enter the authorization code: ')
                flow.fetch_token(code=code)

                cls.credentials = flow.credentials
            # Save the credentials for the next run
            with open(file=token_path, mode="w", encoding="utf-8") as token:
                token.write(cls.credentials.to_json())

    @classmethod
    def tasklists(cls) -> List[TaskList]:
        """Gets the available tasklists.

        Returns:
            List[TaskList]: The list of TaskLists
        """
        service = build("tasks", "v1", credentials=cls.credentials)
        results = service.tasklists().list().execute()
        items = results.get("items", [])

        return [TaskList(item["id"], item["title"]) for item in items]

    @classmethod
    def tasks(cls, list_id: str) -> List[Task]:
        """Gets the tasks in the provided list.

        Args:
            list_id (str): The list's id

        Returns:
            List[Task]: A List of Tasks
        """
        service = build("tasks", "v1", credentials=cls.credentials)
        results = service.tasks().list(tasklist=list_id, showCompleted=False).execute()
        items = results.get("items", [])

        return [Task(item["id"], item["title"], item.get("parent"), item.get("due"))
            for item in items]

    @classmethod
    def calendars(cls) -> List[Calendar]:
        """Gets the available calendars.

        Returns:
            List[Calendar]: A List of Calendars
        """
        service = build("calendar", "v3", credentials=cls.credentials)
        results = service.calendarList().list().execute()
        items = results.get("items", [])

        return [Calendar(item["id"], item["summary"]) for item in items]

    @classmethod
    def events(cls,
        start: datetime.datetime = None,
        end: datetime.datetime = None,
        calendar_id: str="primary") -> List[Event]:
        """Gets the events from the provided calendar from between the provided times.
        If no times are provided, returns the next 10 upcoming events.

        Args:
            start (datetime.datetime, optional): The UTC start time
            end (datetime.datetime, optional): The UTC end time
            calendar_id (str, optional): The calendar's ID. Defaults to the primary calendar.

        Returns:
            List[Event]: A List of Events
        """
        service = build("calendar", "v3", credentials=cls.credentials)

        start_time = datetime.datetime.utcnow().isoformat() + "Z"
        if start:
            start_time = start.isoformat() + "Z"  # 'Z' indicates UTC time

        end_time = None
        if end:
            end_time = end.isoformat() + "Z"  # 'Z' indicates UTC time

        events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=start_time,
                timeMax=end_time,
                maxResults=None if end_time else 10,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
        items = events_result.get("items", [])

        return [Event(item["id"], item["start"], item["summary"]) for item in items]
