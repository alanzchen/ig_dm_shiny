from datetime import datetime
import pandas as pd

def _get_message_type(message: dict) -> str:
    """get message type from message dictionary"""
    if 'photos' in message:
        msg_type = 'image'
    elif 'videos' in message:
        msg_type = 'video'
    elif 'audio_files' in message:
        msg_type = 'audio'
    elif 'share' in message:
        msg_type = 'share content'
    elif 'call_duration' in message:
        msg_type = 'audio/video call'
    elif 'content' in message:
        if 'an audio call' in message['content']:
            msg_type = 'audio/video call'
        elif message['content'].endswith('shared a story.'):
            msg_type = 'story mentioned'
        elif message['content'].endswith('Liked a message'):
            msg_type = 'story liked'
        else:
            msg_type = 'text'
    else:
        msg_type = 'other'

    return msg_type


def _get_message_text(message: dict) -> str:
    """get text message if any from message dictionary"""
    if 'content' in message:  # find a better way to check this
        text = message['content'].encode('raw_unicode_escape').decode('utf-8')
    else:
        text = ""

    return text


def _get_reaction(message: dict) -> int:
    """get count of reactions of the message"""
    if 'reactions' in message:
        reaction_text = "".join([dct['reaction'] for dct in message['reactions']])
        reaction_text = reaction_text.encode('raw_unicode_escape').decode('utf-8')
    else:
        reaction_text = ""

    return reaction_text


def _get_reaction_count(message: dict) -> int:
    """get count of reactions of the message"""
    if 'reactions' in message:
        count = len(message['reactions'])
    else:
        count = 0

    return count
