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

## Building x86 binary on Apple Silicon Mac

1. Install a `universal2` version of Python on python.org
2. Launch Terminal.app in Roestta mode. Run `arch` to confirm you are using the right arch.
3. Activate the new Python env and use the corresponding pip to install all dependencies. Use `which pip` to confirm you are using the right one.
4. Build as usual. Confirm the arch in your final build. 

## Notes

- `ig_dm_scraper` by @NaphatPi