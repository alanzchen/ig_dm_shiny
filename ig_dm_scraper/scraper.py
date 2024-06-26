from pathlib import Path
import time
import datetime
import zipfile
import os
import json
import re

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
    """Find participant name from the zip file or folder. Return empty string if not found"""
    print('Finding participant name ... ', end="")
    
    # Check if zipname is a folder
    if os.path.isdir(zipname):
        folder_path = Path(zipname)
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for filename in files:
                if filename.endswith('personal_information.json'):
                    print(root, dirs, files)
                if 'personal_information' in root and filename.endswith('personal_information.json'):
                    json_path = os.path.join(root, filename)
                    with open(json_path, 'r') as file:
                        data = json.load(file)
                        if data['profile_user'][0]['string_map_data']:
                            _ = data['profile_user'][0]['string_map_data']
                            if 'Name' in _: # check if the format is valid
                                name = _['Name']['value']
                                return name
                            elif 'Username' in _:
                                name = _['Username']['value']
                                return name
                            else:
                                raise Exception('There is a problem reading your file. Your file is likely corrupted, please contact umncarlsonstudy@gmail.com for assistance. We apology for the inconvenience.')
        else:
            raise Exception('personal_information.json not found in the zip file or folder. Did you choose the right file or folder? Its name should look like "instagram-(username)-XXXX".')
    # If zipname is a zip file
    elif zipfile.is_zipfile(zipname):
        with zipfile.ZipFile(zipname, mode='r') as z:
            for filename in z.namelist():
                if 'personal_information/personal_information.json' in filename:
                    data = json.loads(z.read(filename))
                    if data['profile_user'][0]['string_map_data']:
                        try:
                            _ = data['profile_user'][0]['string_map_data']
                            if 'Name' in _: # check if the format is valid
                                name = _['Name']['value']
                                return name
                            elif 'Username' in _:
                                name = _['Username']['value']
                                return name
                            else:
                                raise Exception('There is a problem reading your file. Your file is likely corrupted, please contact umncarlsonstudy@gmail.com for assistance. We apology for the inconvenience.')
                        except Exception as e:
                            return 'participant'
                    else:
                        raise Exception('personal_information.json is not valid. Did you choose the right file or folder?.')
            else:
                raise Exception('personal_information.json not found in the zip file or folder. Did you choose the right file or folder? Its name should look like "instagram-(username)-XXXX".')

def get_post_comments(filepath: str) -> list:
    """Get comments from the zip file or folder

    Args:
        filepath (str): path to the zip file or folder

    Return:
        A list containing comments

    """
    comment_list = []
    print('Getting post comments from the zip file or folder ... ', end="")
    if os.path.isdir(filepath): # if filepath is a folder
        for root, dirs, files in os.walk(filepath):
            for filename in files:
                if 'comments' in root and re.search(r'^post_comments_\d+.json', os.path.basename(filename)):
                    json_path = os.path.join(root, filename)
                    with open(json_path, 'r') as file:
                        comments = json.load(file)
                        comment_list += comments
    elif zipfile.is_zipfile(filepath): # if filepath is a zip file
        with zipfile.ZipFile(filepath, mode='r') as z:
            for filename in z.namelist():
                if 'comments' in filename and re.search(r'^post_comments_\d+.json', os.path.basename(filename)):
                    decoded_text = z.read(filename)
                    comments = json.loads(decoded_text)
                    comment_list += comments
    print(f'{len(comment_list)} comments collected')
    return comment_list

def get_reels_comments(filepath: str) -> list:
    """Get comments from the zip file or folder

    Args:
        filepath (str): path to the zip file or folder

    Return:
        A list containing comments

    """
    comment_list = []
    print('Getting reels comments from the zip file or folder ... ', end="")
    if os.path.isdir(filepath): # if filepath is a folder
        for root, dirs, files in os.walk(filepath):
            for filename in files:
                if 'comments' in root and 'reels_comments.json' == os.path.basename(filename):
                    json_path = os.path.join(root, filename)
                    with open(json_path, 'r') as file:
                        comments = json.load(file)['comments_reels_comments']
                        comment_list += comments
    elif zipfile.is_zipfile(filepath): # if filepath is a zip file
        with zipfile.ZipFile(filepath, mode='r') as z:
            for filename in z.namelist():
                if 'comments' in filename and 'reels_comments.json' == os.path.basename(filename):
                    decoded_text = z.read(filename)
                    comments = json.loads(decoded_text)['comments_reels_comments']
                    comment_list += comments
    print(f'{len(comment_list)} comments collected')
    return comment_list

def get_stories(filepath: str) -> list:
    """Get stories from the zip file or folder

    Args:
        filepath (str): path to the zip file or folder

    Return:
        A list containing stories

    """
    stories_list = []
    print('Getting stories from the zip file or folder ... ', end="")
    if os.path.isdir(filepath): # if filepath is a folder
        for root, dirs, files in os.walk(filepath):
            for filename in files:
                if 'content' in root and os.path.basename(filename) == 'stories.json':
                    json_path = os.path.join(root, filename)
                    with open(json_path, 'r') as file:
                        stories = json.load(file)
                        if 'ig_stories' in stories:
                            stories_list += stories['ig_stories']
                        else:
                            print(f'No stories found in {json_path}')
    elif zipfile.is_zipfile(filepath): # if filepath is a zip file
        with zipfile.ZipFile(filepath, mode='r') as z:
            for filename in z.namelist():
                if 'content' in filename and os.path.basename(filename) == 'stories.json':
                    decoded_text = z.read(filename)
                    stories = json.loads(decoded_text)
                    if 'ig_stories' in stories:
                        stories_list += stories['ig_stories']
                    else:
                        print(f'No stories found in {filename}')

    print(f'{len(stories_list)} stories collected')
    return stories_list

def get_posts(filepath: str) -> list:
    """Get posts from the zip file or folder

    Args:
        filepath (str): path to the zip file or folder

    Return:
        A list containing posts

    """
    posts_list = []
    def proc(loaded_json):
        nonlocal posts_list
        if isinstance(loaded_json, list):
            posts = [i['media'][0] if 'title' not in i else i for i in loaded_json]
        else:
            # there is only one post
            posts = loaded_json['media'] # note: media is a list, so no need to wrap it in a list 
        posts_list += posts

    print('Getting posts from the zip file or folder ... ', end="")
    if os.path.isdir(filepath): # if filepath is a folder
        for root, dirs, files in os.walk(filepath):
            for filename in files:
                if 'content' in root and re.search(r'^posts_\d+.json', os.path.basename(filename)):
                    json_path = os.path.join(root, filename)
                    with open(json_path, 'r') as file:
                        posts = json.load(file)
                        proc(posts)
    elif zipfile.is_zipfile(filepath): # if filepath is a zip file
        with zipfile.ZipFile(filepath, mode='r') as z:
            for filename in z.namelist():
                if 'content' in filename and re.search(r'^posts_\d+.json', os.path.basename(filename)):
                    decoded_text = z.read(filename)
                    posts = json.loads(decoded_text)
                    proc(posts)
    
    print(f'{len(posts_list)} posts collected')
    return posts_list

def get_dm_from_zip(filepath: str, oldest_date: str = None) -> list:
    """Get direct message from zip file or folder until oldest_date

        Args:
            filepath (str): path to the zip file or folder
            oldest_date (str): date used as a cutoff to get data newer than this date

        Return:
            A list containing messages from each thread (chat room)

    """
    print("get_dm_from_zip")
    participant_name = _find_participant_name_from_zip(filepath)
    oldest_date = datetime.date.fromisoformat(oldest_date if oldest_date else '2000-01-01')
    message_count = 0
    thread_list = []

    def proc(loaded_json):
        nonlocal message_count
        nonlocal thread_list

        messages = loaded_json['messages']
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

    print('Getting data from the zip file or folder ... ', end="")
    if os.path.isdir(filepath): # if filepath is a folder
        for root, dirs, files in os.walk(filepath):
            for filename in files:
                if 'inbox' in root and re.search(r'^message_\d+.json', os.path.basename(filename)):
                    json_path = os.path.join(root, filename)
                    with open(json_path, 'r') as file:
                        messages = json.load(file)
                        proc(messages)
    elif zipfile.is_zipfile(filepath): # if filepath is a zip file
        with zipfile.ZipFile(filepath, mode='r') as z:
            for filename in z.namelist():
                if 'inbox' in filename and re.search(r'^message_\d+.json', os.path.basename(filename)):
                    decoded_text = z.read(filename)
                    messages = json.loads(decoded_text)
                    proc(messages)

    print('done')
    print(f'{len(thread_list)} threads - {message_count} messages collected')

    return thread_list
