from shiny import App, render, ui, reactive
from ig_dm_scraper.scraper import get_dm_from_zip
from ig_dm_scraper.formatter import reformat
from ig_dm_scraper.anonymizer import anonymize
import io
from pathlib import Path

from js import fetch
from pathlib import Path
import zipfile

ready = False
success = False
status = "Initializing... Please stay connected to the internet. Please wait."

SUCCESS_MSG = 'Successfully anonymized your data. Enter your participant ID below to download the anonymized data.'
STANDYBY_MSG = 'You may optionally turn off your internet connection from now on. Please select the Instagram data file (a zip file) you downloaded. Once you select a file, it will automatically start processing, which may take a few minutes. This is normal.'

app_ui = ui.page_fluid(
    ui.panel_title("IG Data Anonymizer"),
    ui.panel_conditional(
        f"output.info_text == '{STANDYBY_MSG}'",
        ui.input_file("file_picker", "Select your instagram data file:", accept=".zip"),
    ),
    ui.output_text("info_text", "Initializing... Please stay connected to the internet. Please wait."),
    ui.panel_conditional(
        f"output.info_text === '{SUCCESS_MSG}'",
        ui.input_text("pid", "Your Participant ID:", placeholder="Enter text")
    ),
    ui.panel_conditional(
        f"output.info_text === '{SUCCESS_MSG}' && input.pid != ''",
        ui.download_button("download_data_btn", "Download Anonymized File"),
    )
)

def server(input, output, session):
    result_list = [None]

    async def download_and_extract_nltk_data(package_name):
        base_url = 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/'
        package_path = {
            'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger.zip',
            'maxent_ne_chunker': 'chunkers/maxent_ne_chunker.zip',
            'words': 'corpora/words.zip',
            'punkt': 'tokenizers/punkt.zip'
        }

        print(f"Downloading {package_name}... ")

        if package_name not in package_path:
            print(f"Package {package_name} not found.")
            return

        url = base_url + package_path[package_name]
        response = await fetch(url)
        js_buffer = await response.arrayBuffer()
        py_buffer = js_buffer.to_py()  # this is a memoryview
        stream = py_buffer.tobytes()  # now we have a bytes object

        directory = package_path[package_name].split('/')[0]
        d = Path(f"/nltk_data/{directory}")
        d.mkdir(parents=True, exist_ok=True)

        zip_path = f"/nltk_data/{package_path[package_name]}"
        Path(zip_path).write_bytes(stream)

        # extract the zip file
        zipfile.ZipFile(zip_path).extractall(path=d)

    async def init_nltk_data():
        global ready, status
        # Download the packages
        await download_and_extract_nltk_data('averaged_perceptron_tagger')
        status = "Initializing... 1/4"
        await download_and_extract_nltk_data('maxent_ne_chunker')
        status = "Initializing... 2/4"
        await download_and_extract_nltk_data('words')
        status = "Initializing... 3/4"
        await download_and_extract_nltk_data('punkt')
        status = "Initializing... 4/4"
        ready = True

    @reactive.Effect
    async def _():
        await init_nltk_data()

    @output
    @render.text
    def info_text():
        global ready, success, status
        if not ready:
            return status

        file_infos = input.file_picker()
        if not file_infos:
            success = False
            return STANDYBY_MSG

        file_info = file_infos[0]
        try:
            raw = get_dm_from_zip(filepath=file_info["datapath"], oldest_date='2023-05-01')
            df = reformat(raw, as_dataframe=True)
            anom_df = anonymize(df)

            result_list[0] = anom_df
            success = True
            return SUCCESS_MSG
        except Exception as e:
            return f"Error processing file '{file_info['name']}': {e}"

    @session.download(filename=lambda: f"data-{input.pid()}.csv")
    def download_data_btn():
        if success:
            with io.BytesIO() as buf:
                result_list[0].to_csv(buf)
                yield buf.getvalue()
        else:
            file_infos = input.file_picker()
            if not file_infos:
                msg = "Please select the Instagram data file (a zip file) you downloaded."
            else:
                msg = f"Error processing file '{file_infos[0]['name']}'. Please try again."
            m = ui.modal(
                msg,
                title="Error",
                easy_close=True
            )
            ui.modal_show(m)
            raise Exception(msg)

app = App(app_ui, server)