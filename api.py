from typing import Literal, List, Dict, Any

def START_NAVIGATE(DESTINATION: str) -> None:
    """
    Initialise navigation.
    
    This function uses the START_NAVIGATE intent to open the map app, search about the input location, and start the navigation ability.

    Args:
        DESTINATION (str): The destination of the route.
            - Provide a place name or address string, e.g. "Changi Airport", "Marina Bay Sands".
    """
    pass


def VIEW_ROUTES(
    ORIGIN: str,
    DESTINATION: str,
    MODE: Literal["DRIVING", "WALKING", "TRANSIT", "CYCLING"] = "DRIVING"
) -> None:
    """
    View available routes from ORIGIN to DESTINATION in the default map application.

    Args:
        ORIGIN (str): The starting point of the route.
            - Use "CURRENT" to represent the user's current location.
            - Or provide a place name or address string, e.g. "Orchard MRT", "NUS".

        DESTINATION (str): The destination of the route.
            - Provide a place name or address string, e.g. "Changi Airport", "Marina Bay Sands".

        MODE ({"driving","walking","transit","cycling"}): 
            Optional. The travel mode to use for route calculation. Default is "driving".
    """
    pass


def CREATE_CALENDER_EVENT(TITLE: str, DESCRIPTION: str, EVENT_LOCATION: str=None, 
                        EXTRA_EVENT_ALL_DAY: bool=False, 
                        EXTRA_EVENT_BEGIN_TIME: str=None, 
                        EXTRA_EVENT_END_TIME: str=None) -> None:
    """
    Add a new event to the user's calendar.
    
    Args:
        TITLE (str): The event title.
        
        DESCRIPTION (str): The event description.
        
        EVENT_LOCATION (str): The event location. Default is None.
        
        EXTRA_EVENT_ALL_DAY (bool): A boolean specifying whether this is an all-day event. Default is False.
        
        EXTRA_EVENT_BEGIN_TIME (str): The start time of the event in ISO 8601 format. Default is None.
        
        EXTRA_EVENT_END_TIME (str): The end time of the event in ISO 8601 format. Default is None.
    """
    pass

def SET_PLAYBACK_STATE(
    STATE: Literal["PLAY", "PAUSE", "PLAYPREVIOUS", "PLAYNEXT", "TOGGLEFAVORITE"]
) -> None:
    """
    Control the playback state of the media player. Users can perform music playback, pause, previous track, next track, and favorite operations.

    Args:
        STATE ({"PLAY", "PAUSE", "PLAYPREVIOUS", "PLAYNEXT", "TOGGLEFAVORITE"}):
            The desired playback action to perform.
            
            - "PLAY": Start or resume playback of the current media.
            - "PAUSE": Pause the current playback.
            - "PLAYPREVIOUS": Play the previous track in the playlist.
            - "PLAYNEXT": Play the next track in the playlist.
            - "TOGGLEFAVORITE": Add or remove the current track from favorites.
    """
    pass

def OPEN_CAMERA(
    MODE: Literal["PHOTO", "VIDEO"] = "PHOTO",
    CAMERA_POSITION: Literal["FRONT", "BACK"] = "BACK"
) -> None:
    """
    Open the camera in the specified mode and position.

    Args:
        MODE ({"PHOTO", "VIDEO"}): 
            The mode in which to open the camera.
            - "PHOTO": Open the camera for taking photos. (default)
            - "VIDEO": Open the camera for recording videos.

        CAMERA_POSITION ({"FRONT", "BACK"}): 
            The position of the camera to use.
            - "FRONT": Use the front camera.
            - "BACK": Use the rear camera. (default)
    """
    pass

def TAKE_PHOTO(
    MODE: Literal["PHOTO", "VIDEO"] = "PHOTO",
    CAMERA_POSITION: Literal["FRONT", "BACK"] = "BACK"
) -> None:
    """
    Capture a picture or video using the camera app in specified camera position.
    
    Args:
        MODE ({"PHOTO", "VIDEO"}): 
            The mode in which to open the camera.
            - "PHOTO": Open the camera for taking photos. (default)
            - "VIDEO": Open the camera for recording videos.

        CAMERA_POSITION ({"FRONT", "BACK"}): 
            The position of the camera to use.
            - "FRONT": Use the front camera.
            - "BACK": Use the rear camera. (default)
    """
    pass

def CALL_MEETIME(
    PHONE_NUMBER: str,
    MEDIA_TYPE: Literal["AUDIO", "VIDEO"] = "AUDIO"
) -> None:
    """
    Initiates a MeeTime call to the specified phone number.

    This function allows the user to start a Huawei MeeTime call. It can be used
    to make either an audio or video call depending on the specified media type.

    Args:
        PHONE_NUMBER (str): The phone number to call.
            - This should be a valid telephone number (e.g., "13800138000").
            - The number must be registered with Huawei MeeTime service.

        MEDIA_TYPE ({"AUDIO", "VIDEO"}):
            The type of call to initiate.
            - "AUDIO": Start an audio call. (default)
            - "VIDEO": Start a video call.
    """
    pass

def GET_CURRENT_LOCATION() -> str:
    """
    Get the user's current geographic location.

    This function retrieves the user's current location information from the device.
    The location is returned as a standardized string (e.g., a human-readable address
    or a coordinate pair).

    Returns:
        str: The user's current location, which may include:
            - A human-readable address, e.g. "21 Lower Kent Ridge Rd, Singapore"
            - Or a coordinate string, e.g. "1.2966,103.7764"
    """
    pass

def START_CALL(
    PHONE_NUMBER: str,
    SLOT_ID: int = 0
) -> None:
    """
    Directly place a phone call to the specified number.

    This function allows the user to directly make a phone call without
    opening the dialer interface. It can optionally specify which SIM slot
    to use when the device supports dual SIM cards.

    Args:
        PHONE_NUMBER (str): The phone number to call.
            - This should be a valid telephone number, such as "13800138000".
            - The function will directly initiate the call.

        SLOT_ID (int): The SIM slot ID to use for the call. Default is 0.
            - 0: Primary SIM card (default)
            - 1: Secondary SIM card
    """
    pass

def SEARCH_CALL_RECORD(
    CALL_RECORD_TYPE: Literal[0, 1, 2, 3] = 0
) -> List[Dict[str, Any]]:
    """
    Retrieve recent call records from the device.

    This function queries the device's call history and returns
    a list of call records sorted by time (most recent first).
    Up to 20 records will be returned.

    Args:
        CALL_RECORD_TYPE ({0, 1, 2, 3}):
            The type of call records to retrieve. Default is 0 (all).
            - 0: All calls
            - 1: Missed calls
            - 2: Received calls
            - 3: Outgoing calls

    Returns:
        List[Dict[str, Any]]: A list of call record dictionaries, each containing
            relevant details such as:
            {
                "phone_number": "13800138000",
                "call_type": "outgoing",
                "call_duration": 120,  # seconds
                "call_time": "2025-10-07T09:15:00+08:00"
            }
    """
    pass

def VIEW_CALL_RECORD(
    CALL_RECORD_TYPE: Literal[0, 1] = 0
) -> None:
    """
    Open the call record page in the phone app.

    This function navigates to the system's call record interface,
    allowing the user to view call history. It supports filtering
    by call type (all or missed).

    Args:
        CALL_RECORD_TYPE ({0, 1}):
            The type of call records to display. Default is 0 (all).
            - 0: All calls
            - 1: Missed calls
    """
    pass

def MAKE_CALL(
    PHONE_NUMBER: str
) -> None:
    """
    Open the phone dialer with a specified number pre-filled.

    This function opens the system's phone dialer interface and
    fills in the given phone number. The user can then manually
    confirm and start the call.

    Args:
        PHONE_NUMBER (str): The phone number to display in the dialer.
            - Must be a valid telephone number, e.g. "13800138000" or "+6598765432".
            - This function does not automatically place the call.
    """
    pass

def READ_EMAIL(
    MESSAGE_ID: str = None,
    QUERY: str = None,
    LABELS: List[str] = None,
    MAX_RESULTS: int = 50,
    INCLUDE_BODY: bool = True,
) -> None:
    """
    Read emails from the user's mailbox.

    Use either a specific MESSAGE_ID or search filters to retrieve one or more emails.

    Args:
        MESSAGE_ID:
            Unique ID of the email to read. If provided, other filters are ignored.
        QUERY:
            Free-text search using standard email operators, e.g., from:, subject:, before:, after:, label:.
        LABELS:
            Filter by labels/folders, e.g., ["INBOX", "STARRED"].
        MAX_RESULTS:
            Maximum number of emails to return. Default: 50.
        INCLUDE_BODY:
            Whether to include the full HTML/text body for each email. Default: True.
    """
    pass


def SEND_EMAIL(
    TO: List[str],
    SUBJECT: str,
    BODY_TEXT: str = None,
    BODY_HTML: str = None,
    CC: List[str] = None,
    BCC: List[str] = None,
    ATTACHMENTS: List[Dict[str, Any]] = None,
    IN_REPLY_TO: str = None,
    THREAD_ID: str = None,
    HEADERS: Dict[str, str] = None,
    PRIORITY: Literal["NORMAL", "HIGH", "LOW"] = "NORMAL",
    SCHEDULE_TIME: str = None,
) -> None:
    """
    Send an email from the user's mailbox.

    Creates and sends a new message. Can reply in an existing thread and/or attach files.

    Args:
        TO:
            Primary recipients.
        SUBJECT:
            Email subject line.
        BODY_TEXT:
            Plain-text body. Provide at least one of BODY_TEXT or BODY_HTML.
        BODY_HTML:
            HTML body. Provide at least one of BODY_TEXT or BODY_HTML.
        CC:
            Carbon-copy recipients.
        BCC:
            Blind-carbon-copy recipients.
        ATTACHMENTS:
            A list of attachments with {filename, mime_type, content_base64} or {file_id}.
        IN_REPLY_TO:
            Message ID this email replies to.
        THREAD_ID:
            Existing thread ID.
        HEADERS:
            Additional RFC-822 headers (key/value).
        PRIORITY:
            Email priority. Default: "NORMAL".
        SCHEDULE_TIME:
            Future send time in ISO 8601 UTC. If omitted, sends immediately.
    """
    pass


def WRITE_EMAIL(
    DRAFT_ID: str = None,
    TO: List[str] = None,
    SUBJECT: str = None,
    BODY_TEXT: str = None,
    BODY_HTML: str = None,
    CC: List[str] = None,
    BCC: List[str] = None,
    ATTACHMENTS: List[Dict[str, Any]] = None,
    IN_REPLY_TO: str = None,
    HEADERS: Dict[str, str] = None,
) -> None:
    """
    Create or update an email draft without sending.

    Args:
        DRAFT_ID:
            Existing draft ID. If omitted, a new draft is created.
        TO:
            Primary recipients.
        SUBJECT:
            Email subject line.
        BODY_TEXT:
            Plain-text body.
        BODY_HTML:
            HTML body.
        CC:
            Carbon-copy recipients.
        BCC:
            Blind-carbon-copy recipients.
        ATTACHMENTS:
            Attachments with content or file ID.
        IN_REPLY_TO:
            Message ID this draft would reply to.
        HEADERS:
            Additional RFC-822 headers (key/value).
    """
    pass


def PAY_REPAYMENT(
    ENTITY_NAME: str,
    ENTITY_ID: str,
    ENTITY_GROUP_ID: str = None,
    DISPLAY_NAME: str = "",
    DESCRIPTION: str = "",
    LOGO_URL: str = "",
    KEYWORDS: List[str] = None,
    RANKING_HINT: float = None,
    EXPIRATION_TIME: float = None,
    METADATA_MODIFICATION_TIME: float = None,
    ACTIVITY_TYPE: List[str] = None,
    IS_PUBLIC_DATA: bool = None,
    EXTRAS: Dict[str, Any] = None,
) -> None:
    """
    Trigger a repayment payment and write or update related metadata.

    Args:
        ENTITY_NAME:
            Entity name.
        ENTITY_ID:
            Unique identifier, max length 64.
        ENTITY_GROUP_ID:
            Grouping identifier for admin use.
        DISPLAY_NAME:
            Display name, max length 50.
        DESCRIPTION:
            User-facing description, max length 2000.
        LOGO_URL:
            Thumbnail URL for UI.
        KEYWORDS:
            Search keywords array.
        RANKING_HINT:
            Sorting weight, 0 to 100.
        EXPIRATION_TIME:
            Expiration timestamp (s or ms).
        METADATA_MODIFICATION_TIME:
            Last metadata update timestamp.
        ACTIVITY_TYPE:
            Behavior types.
        IS_PUBLIC_DATA:
            Whether public-domain data.
        EXTRAS:
            Additional extension metadata.
    """
    pass






