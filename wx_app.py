from datetime import datetime
import hashlib
import wx
import wx.lib.newevent
import pandas as pd
import threading
from ig_dm_scraper.scraper import get_dm_from_zip, get_post_comments, get_posts, get_reels_comments, get_stories
from ig_dm_scraper.formatter import _get_message_text, _get_message_type, _get_reaction
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
import spacy
from pathlib import Path
import spacy_fastlang
import os
import shutil

bundle_dir = Path(__file__).parent.absolute()


nlp = spacy.load(bundle_dir / "en_core_web_sm")
nlp.add_pipe("language_detector")
model = SentenceTransformer("all-MiniLM-L6-v2")
print(nlp('hello')._.language)

def fix_encoding(s):
    if s:
        return s.encode("utf-8").decode("utf-8")
    else:
        return s
    
def namehash(name):
    return hashlib.md5(name.encode('raw_unicode_escape')).hexdigest()[:5]

class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        super(MainFrame, self).__init__(parent, title=title, size=(600, 600))

        self.panel = wx.Panel(self)
        self.CreateStatusBar()
        self.SetStatusText("Ready")
        self.layout_components()
        
        self.Bind(wx.EVT_BUTTON, self.on_open_file, self.open_file_button)
        self.Bind(wx.EVT_BUTTON, self.on_open_folder, self.open_folder_button)
        self.Bind(wx.EVT_BUTTON, self.on_save_file, self.save_file_button)

        self.Centre()
        self.Show()

    def layout_components(self):
        # Group 1: File Chooser
        file_chooser_heading = wx.StaticText(self.panel, label="1. Select Instagram Export File or Folder")
        file_chooser_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.open_file_button = wx.Button(self.panel, label="Select File")
        self.open_folder_button = wx.Button(self.panel, label="Select Folder")
        file_chooser_sizer.Add(self.open_file_button, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        file_chooser_sizer.Add(self.open_folder_button, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        file_chooser_divider = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL)

        # Group 2: Progress Bar
        progress_bar_heading = wx.StaticText(self.panel, label="2. Process data")
        progress_bar_sizer = wx.BoxSizer(wx.VERTICAL)
        self.progress_bar = wx.Gauge(self.panel, range=100, style=wx.GA_HORIZONTAL)
        progress_bar_sizer.Add(self.progress_bar, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        progress_bar_divider = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL)

        # Group 3: Save File
        save_file_heading = wx.StaticText(self.panel, label="3. Save Processed File")
        save_file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_file_button = wx.Button(self.panel, label="Save File")
        self.save_file_button.Disable()
        save_file_sizer.Add(self.save_file_button, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        # Main Sizer (Vertical)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(file_chooser_heading, proportion=0, flag=wx.ALL, border=5)
        main_sizer.Add(file_chooser_sizer, proportion=0, flag=wx.EXPAND)
        main_sizer.Add(file_chooser_divider, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(progress_bar_heading, proportion=0, flag=wx.ALL, border=5)
        main_sizer.Add(progress_bar_sizer, proportion=0, flag=wx.EXPAND)
        main_sizer.Add(progress_bar_divider, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(save_file_heading, proportion=0, flag=wx.ALL, border=5)
        main_sizer.Add(save_file_sizer, proportion=0, flag=wx.EXPAND)

        self.panel.SetSizerAndFit(main_sizer)
        self.Fit()

        self.SetMinSize(self.GetSize())


    def on_open_file(self, event):
        with wx.FileDialog(self, "Select your Instagram data file", wildcard="ZIP files (*.zip)|*.zip",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return  # User changed their mind
            # Disable UI components during processing
            self.open_folder_button.Disable()
            self.open_file_button.Disable()
            self.SetStatusText("Processing... Please wait.")
            # Async processing
            ReformatThread(self, file_dialog.GetPath())

    def on_open_folder(self, event):
        with wx.DirDialog(self, "Select your Instagram data folder",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return  # User changed their mind
            # Disable UI components during processing
            self.open_folder_button.Disable()
            self.open_file_button.Disable()
            self.SetStatusText("Processing... Please wait.")
            # Async processing
            ReformatThread(self, file_dialog.GetPath())

    def on_save_file(self, event):
        with wx.DirDialog(self, "Save file to this folder",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return  # User changed their mind
            # Attempt to save the data
            try:
                target_folder_path = file_dialog.GetPath()
                save_file_path = Path(target_folder_path) / f"{os.path.basename(self.final_file_path)}"
                shutil.copy(self.final_file_path, save_file_path)
                wx.MessageBox(f"Data saved to {save_file_path} successfully! Please do not rename the file. Now you may upload it on our survey webpage. Feel free to quit this app now.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.SetStatusText("Step 3 compeleted.")
            except Exception as e:
                wx.MessageBox(f"Error saving the file: {e}", "Error", wx.OK | wx.ICON_ERROR)
                self.SetStatusText(f"Error saving the file: {e}")

    def on_reformat_done(self, result):
        self.final_file_path = result  # Store the DataFrame in the instance
    
    def update_progress_bar(self, progress):
        self.progress_bar.SetValue(progress)


class ReformatThread(threading.Thread):
    def __init__(self, parent, path):
        threading.Thread.__init__(self)
        self.parent = parent
        self.path = path
        self.start()  # start the thread

    def run(self):
        # Execute the reformat function in the thread
        output = self.reformat(self.path)
        wx.CallAfter(self.parent.on_reformat_done, output)

    def reformat(self, path):
        try:
            # get the date one month before now
            cutoff_date = datetime.now() - timedelta(days=90)
            threads = get_dm_from_zip(filepath=path, oldest_date=cutoff_date.strftime('%Y-%m-%d'))
            post_comments = get_post_comments(filepath=path)
            reels_comments = get_reels_comments(filepath=path)
            posts = get_posts(filepath=path)
            stories = get_stories(filepath=path)

            output = []
            total_messages = sum(len(thread['message']) for thread in threads) + len(post_comments) + len(reels_comments) + len(posts) + len(stories)
            messages_processed = 0

            # process DM
            print("Processing DMs")
            for thread_idx, thread in enumerate(threads):
                for message in thread['message']:
                    text = fix_encoding(_get_message_text(message))
                    type = _get_message_type(message)
                    if type == 'text':
                        doc = nlp(text)
                        language = doc._.language
                        length = doc.__len__()
                    output.append(
                        {
                        'receiver': thread_idx, # here is thread
                        'sender': namehash(message['sender_name']) if message['sender_name'] != 'participant' else 'participant',
                        'timestamp': datetime.fromtimestamp(message['timestamp_ms']/ 1000),
                        'type': "message_" + type.replace(' ', '_'),
                        'language': language if type == 'text' else None,
                        # 'text': text if type == 'text' else None,
                        'len': length if type == 'text' else None,
                        'embedding': model.encode(text) if type == 'text' else None,
                        'reaction': _get_reaction(message)
                        }
                    )
                    messages_processed += 1
                    progress = int((messages_processed / total_messages) * 100)
                    wx.CallAfter(self.parent.update_progress_bar, progress)
            
            # process post comments
            print("Processing post comments")
            for post in post_comments:
                try:
                    _ = post['string_map_data']
                    text = fix_encoding(_['Comment']['value'])
                    time = datetime.fromtimestamp(_['Time']['timestamp'])
                    if time < cutoff_date:
                        messages_processed += 1
                        progress = int((messages_processed / total_messages) * 100)
                        wx.CallAfter(self.parent.update_progress_bar, progress)
                        continue
                    if text:
                        doc = nlp(text)
                        language = doc._.language
                        length = doc.__len__()
                    output.append({
                        'receiver': 'id_' + namehash(_['Media Owner']['value']),
                        'sender': 'participant',
                        'timestamp': time,
                        'type': 'post_comments',
                        'language': language if text else None,
                        'len': length if text else None,
                        'embedding': model.encode(text) if text else None,
                    })
                except Exception as e:
                    print(_)
                    print(e)
                    pass
                messages_processed += 1
                progress = int((messages_processed / total_messages) * 100)
                wx.CallAfter(self.parent.update_progress_bar, progress)

            # process reels comments
            print("Processing reels comments")
            for reel in reels_comments:
                try:
                    _ = reel['string_map_data']
                    text = fix_encoding(_['Comment']['value'])
                    time = datetime.fromtimestamp(_['Time']['timestamp'])
                    if time < cutoff_date:
                        messages_processed += 1
                        progress = int((messages_processed / total_messages) * 100)
                        wx.CallAfter(self.parent.update_progress_bar, progress)
                        continue
                    if text:
                        doc = nlp(text)
                        language = doc._.language
                        length = doc.__len__()
                    output.append({
                        'receiver': 'id_' + namehash(_['Media Owner']['value']),
                        'sender': 'participant',
                        'timestamp': time,
                        'type': 'reel_comments',
                        'language': language if text else None,
                        'len': length if text else None,
                        'embedding': model.encode(text) if text else None,
                    })
                except Exception as e:
                    print(_)
                    print(e)
                    pass
                messages_processed += 1
                progress = int((messages_processed / total_messages) * 100)
                wx.CallAfter(self.parent.update_progress_bar, progress)

            # process posts
            print("Processing posts")
            for post in posts:
                try:
                    _ = post
                    text = fix_encoding(_['title'])
                    time = datetime.fromtimestamp(_['creation_timestamp'])
                    if time < cutoff_date:
                        messages_processed += 1
                        progress = int((messages_processed / total_messages) * 100)
                        wx.CallAfter(self.parent.update_progress_bar, progress)
                        continue
                    if text:
                        doc = nlp(text)
                        language = doc._.language
                        length = doc.__len__()
                    output.append({
                        'sender': 'participant',
                        'timestamp': time,
                        'type': 'posts',
                        'language': language if text else None,
                        'len': length if text else None,
                        'embedding': model.encode(text) if text else None,
                    })
                except Exception as e:
                    print(_)
                    print(e)
                    pass
                messages_processed += 1
                progress = int((messages_processed / total_messages) * 100)
                wx.CallAfter(self.parent.update_progress_bar, progress)

            # process posts
            print("Processing stories")
            for post in stories:
                try:
                    _ = post
                    text = fix_encoding(_['title'])
                    time = datetime.fromtimestamp(_['creation_timestamp'])
                    if time < cutoff_date:
                        messages_processed += 1
                        progress = int((messages_processed / total_messages) * 100)
                        wx.CallAfter(self.parent.update_progress_bar, progress)
                        continue
                    if text:
                        doc = nlp(text)
                        language = doc._.language
                        length = doc.__len__()
                    output.append({
                        'sender': 'participant',
                        'timestamp': time,
                        'type': 'story',
                        'language': language if text else None,
                        'len': length if text else None,
                        'embedding': model.encode(text) if text else None,
                    })
                except Exception as e:
                    print(_)
                    print(e)
                    pass
                messages_processed += 1
                progress = int((messages_processed / total_messages) * 100)
                wx.CallAfter(self.parent.update_progress_bar, progress)

            output = pd.DataFrame(output)
            output.to_csv(bundle_dir / "data.csv", index=False)
            # calculate hash of the file
            hash = hashlib.md5()
            with open(bundle_dir / "data.csv", "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash.update(chunk)
            # rename the data.csv based on the hash
            final_file_path = bundle_dir / f"{hash.hexdigest()}.csv"
            Path(bundle_dir / "data.csv").rename(final_file_path)

            if output is not None and not output.empty:
                wx.CallAfter(self.parent.save_file_button.Enable)  # Enable the save button on the main thread
                wx.CallAfter(self.parent.SetStatusText, "Step 2 compeleted.")
            else:
                wx.MessageBox("We could not process your file. The file is in correct format but an unknown error has occurred. A possible reason is that the export data does not contain any message data in the past month. Please contact the study administrator umncarlsonstudy@gmail.com for next steps.", "Error", wx.OK | wx.ICON_ERROR)
                wx.CallAfter(self.parent.SetStatusText, "Failed to process the file or no data returned.")
                self.parent.open_file_button.Enable()
                self.parent.open_folder_button.Enable()
            return final_file_path
        
        except Exception as e:
            wx.CallAfter(self.parent.SetStatusText, f"Error processing the file: {e}")
            wx.MessageBox(f"Error processing the file: {e}", "Error", wx.OK | wx.ICON_ERROR)
            self.parent.open_file_button.Enable()
            self.parent.open_folder_button.Enable()
            return None

def main():
    app = wx.App(False)
    frame = MainFrame(None, "Data Processor")
    app.MainLoop()

if __name__ == '__main__':
    main()
