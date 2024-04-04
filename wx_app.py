from datetime import datetime
import hashlib
import wx
import wx.lib.newevent
import pandas as pd
import threading
import concurrent.futures
from ig_dm_scraper.scraper import get_dm_from_zip
from ig_dm_scraper.formatter import _get_message_text, _get_message_type, _get_reaction
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta

class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        super(MainFrame, self).__init__(parent, title=title, size=(600, 600))

        self.panel = wx.Panel(self)
        self.CreateStatusBar()
        self.SetStatusText("Ready")
        self.layout_components()
        
        self.Bind(wx.EVT_BUTTON, self.on_open_file, self.open_file_button)
        self.Bind(wx.EVT_BUTTON, self.on_save_file, self.save_file_button)

        self.Centre()
        self.Show()

    def layout_components(self):
        # Group 1: File Chooser
        file_chooser_heading = wx.StaticText(self.panel, label="1. Select Instagram Export File")
        file_chooser_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.open_file_button = wx.Button(self.panel, label="Select File")
        file_chooser_sizer.Add(self.open_file_button, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
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
            self.open_file_button.Disable()
            self.SetStatusText("Processing... Please wait.")
            # Async processing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.load_data, file_dialog.GetPath())
                future.add_done_callback(self.on_data_loaded)
    
    def load_data(self, path):
        self.open_file_button.Disable()
        try:
            # get the date one month before now
            one_month_ago = datetime.now() - timedelta(days=30)
            raw = get_dm_from_zip(filepath=path, oldest_date=one_month_ago.strftime('%Y-%m-%d'))
            print("reformat")
            # Use ReformatThread to run reformat in a separate thread
            ReformatThread(self, raw, as_dataframe=True)
        except Exception as e:
            wx.MessageBox(f"{e}", "Error", wx.OK | wx.ICON_ERROR)
            wx.CallAfter(self.SetStatusText, f"Error")
            self.open_file_button.Enable()
            return None

    def on_data_loaded(self, future):
        try:
            self.raw_df = future.result()
            if self.raw_df is not None:
                self.SetStatusText("Processing...")
                self.save_file_button.Enable()
            else:
                self.SetStatusText("")
        except Exception as e:
            self.SetStatusText(f"Error processing file: {e}")

    def on_save_file(self, event):
        with wx.FileDialog(self, "Save file", defaultFile="please_upload_me_to_webpage", wildcard="Parquet files (*.parquet)|*.parquet",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return  # User changed their mind
            # Attempt to save the data
            try:
                file_path = f"{file_dialog.GetPath()[:-4]}"
                self.raw_df.to_parquet(file_path)
                wx.MessageBox("Data saved successfully! Please upload it on our survey webpage. Feel free to quit this app now.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.SetStatusText("Step 3 compeleted.")
            except Exception as e:
                wx.MessageBox(f"Error saving the file: {e}", "Error", wx.OK | wx.ICON_ERROR)
                self.SetStatusText(f"Error saving the file: {e}")

    def on_reformat_done(self, result):
        # Assuming 'result' is a DataFrame or None
        if result is not None and not result.empty:
            self.raw_df = result  # Store the DataFrame in the instance
            wx.CallAfter(self.save_file_button.Enable)  # Enable the save button on the main thread
            wx.CallAfter(self.SetStatusText, "Step 2 compeleted.")
        else:
            wx.MessageBox("We could not process your file. The file is in correct format but an unknown error has occurred. A possible reason is that the export data does not contain any message data in the past month. Please contact the study administrator chen6029@umn.edu for next steps.", "Error", wx.OK | wx.ICON_ERROR)
            wx.CallAfter(self.SetStatusText, "Failed to process the file or no data returned.")
    
    def update_progress_bar(self, progress):
        self.progress_bar.SetValue(progress)


class ReformatThread(threading.Thread):
    def __init__(self, parent, threads, as_dataframe=False):
        threading.Thread.__init__(self)
        self.parent = parent
        self.threads = threads
        self.as_dataframe = as_dataframe
        self.start()  # start the thread

    def run(self):
        # Execute the reformat function in the thread
        output = self.reformat(self.threads, self.as_dataframe)
        wx.CallAfter(self.parent.on_reformat_done, output)

    def reformat(self, threads: list[dict], as_dataframe=False):
        model = SentenceTransformer("all-MiniLM-L6-v2")
        output = []
        total_messages = sum(len(thread['message']) for thread in threads)
        messages_processed = 0
        for thread_idx, thread in enumerate(threads):
            for message in thread['message']:
                text = _get_message_text(message)
                type = _get_message_type(message)
                output.append(
                    {
                    'thread_id': thread_idx,
                    'sender_name': hashlib.md5(message['sender_name'].encode('raw_unicode_escape')).hexdigest(),
                    'timestamp': datetime.fromtimestamp(message['timestamp_ms']/ 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'message_type': type,
                    # 'text': text if type == 'text' else None,
                    'len': len(text) if type == 'text' else None,
                    'words': len(text.split()) if type == 'text' else None,
                    'embedding': model.encode(text) if type == 'text' else None,
                    'reaction': _get_reaction(message)
                    }
                )
                messages_processed += 1
                progress = int((messages_processed / total_messages) * 100)
                wx.CallAfter(self.parent.update_progress_bar, progress)
        
        if as_dataframe:
            output = pd.DataFrame(output)

        return output

def main():
    app = wx.App(False)
    frame = MainFrame(None, "Data Processor")
    app.MainLoop()

if __name__ == '__main__':
    main()
