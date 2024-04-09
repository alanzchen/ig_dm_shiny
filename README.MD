# IG Data Anonymizer

## Requirements

First, make sure you will have all the dependencies to run:

```
pip install -r requirements.txt
python wx_app.py
```

Mostly you will need to install other packages that I have not included in the requirements.txt. Just make sure it runs.

## Build

```
mkdir payload
```

Download `en_core_web_sm` from https://github.com/explosion/spacy-models/releases. Extract the folder containing `config.cfg` to the payload folder.

Then run:

```
./build.sh
```

## Notes

- `ig_dm_scraper` by @NaphatPi