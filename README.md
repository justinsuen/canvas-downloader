# DownloadCanvasFiles
Script to download all course files from canvas and store locally

Install python;
* Windows - install from Microsoft Store 'Python 3.12'
* Mac - install brew;
  * run `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)` in Terminal
  * run `brew install python3` in Terminal after HomeBrew installs

Download repository zip file, unzip to location (ex; Documents)
* Open terminal, navigate to directory by typing ex; `cd /users/user/Documents/DownloadCanvasFiles/`
* Follow installation steps below 

Recommend using `download_files.py`

NOTE: You need to generate a new API key on Canvas prior to use.

Installation Steps:

  1. Ensure python and pip are installed on PATH
  2. Create config.py with two variables, ensure they are in quotes (ex; '');
      * API_KEY = 'key' -> generated from Canvas User settings
      * API_URL = 'https://canvas.instructure.com'
  3. Configure _path variable in python file for custom save destination
  4. Run `pip install -r requrements.txt` in shell
  5. Run `python3 download_files.py``:`

TODO:
* Download media files
* Download assignment submissions
