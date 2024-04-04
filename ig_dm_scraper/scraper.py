import time
import datetime
import zipfile
import os
import json

def _get_dict_from_message(message) -> dict:
    """ This function get instagrapi's DirectMessage object and
        convert to a dictionary with the same format as JSON file
        when getting data from IG's dump function

    Args:
        message: instagrapi DirectMessage object
    
    Return:
        dictionary containing message detail
        
    """
    msg_dict = {}
    msg_dict['sender_name'] = message.user_id
    msg_dict['timestamp_ms'] = time.mktime(message.timestamp.timetuple()) * 1000
    if message.item_type == 'text':
        msg_dict['content'] = message.text
    elif message.item_type == 'animated_media':
        msg_dict['share'] = {
            'link': message.animated_media['images']['fixed_height']['url'],
        }
    elif message.item_type == 'xma_media_share':
        msg_dict['share'] = {
            'link': str(message.xma_share.video_url)
        }
    elif message.item_type == 'media':
        if message.media.video_url: # video
            msg_dict['videos'] = [] # omit video detail
        else: # image
            msg_dict['photos'] = [] # omit image detail
    elif message.item_type == 'clip': # another kind of video
        msg_dict['videos'] = [] # omit video detail
    elif message.item_type == 'generic_xma':
        msg_dict['photos'] = []
    elif message.item_type == 'voice_media':
        msg_dict['audio_files'] = []
    elif message.item_type == 'video_call_event':
        msg_dict['call_duration'] = None

    if message.reactions:
        reac_list = []
        for reaction in message.reactions['emojis']:
            reac_list.append(
                {
                    "reaction": reaction['emoji'],
                    "actor": reaction['sender_id']
                }
            )
        msg_dict['reactions'] = reac_list

    return msg_dict

def _find_participant_name_from_zip(zipname):
    """Find participant name from the zip file. Return empty string if not found"""
    print('Finding participant name ... ', end="")
    name_flag = False
    with zipfile.ZipFile(zipname, mode='r') as z:
        for filename in z.namelist():
            if 'personal_information/personal_information.json' in filename:
                data = json.loads(z.read(filename))
                try:
                    name = data['profile_user'][0]['string_map_data']['Name']['value']
                    print('done')
                    print('Participant name:', name)
                    name_flag = True
                except:
                    raise Exception('Failed to extract name from personal_information.json')

        if not name_flag:
            raise Exception('Participant name not found in the zip file. Please make sure that the zip file is correct.')
        
        return name


def get_dm_from_zip(filepath: str, oldest_date: str = None) -> list:
    """Get direct message from zip file until oldest_date

        Args:
            oldest_date (str): date used as a cutoff to get data newer than this date

        Return:
            A list containing messages from each thread (chat room)

    """
    print("get_dm_from_zip")
    zipname = filepath
    participant_name = _find_participant_name_from_zip(zipname)
    oldest_date = datetime.date.fromisoformat(oldest_date if oldest_date else '2000-01-01')
    message_count = 0
    thread_list = []
    print('Getting data from the zip file ... ', end="")
    with zipfile.ZipFile(zipname, mode='r') as z:
        for filename in z.namelist():
            if 'inbox' in filename and filename.endswith('message_1.json'):
                decoded_text = z.read(filename)
                messages = json.loads(decoded_text)['messages']
                message_list = []
                for message in messages:
                    unix_timestamp = message['timestamp_ms'] / 1000
                    if datetime.date.fromtimestamp(unix_timestamp) >= oldest_date:
                        # mark participant name if found
                        if message['sender_name'] == participant_name:
                            message['sender_name'] = 'participant'
                        message_list.append(message)
                    else:
                        break
                
                if message_list: # if some messages are there
                    message_count += len(message_list)
                    thread_list.append({
                        'message': message_list
                    })
                    
        print('done')
        print(f'{len(thread_list)} threads - {message_count} messages collected')

    return thread_list
