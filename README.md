# DownloadCanvasFiles
Script to download all course files from canvas and store locally

main.py is current iteration, for stock classification and folder structre, run download_files.py

NOTE: You need to generate a new API key on Canvas prior to use.

Installation Steps:

  1. Ensure python and pip are installed on PATH
  2. Create config.py with API_KEY from Canvas User settings
  3. Set API_URL in config.py to https://canvas.instructure.com
  4. Configure _path variable in python file for custom save destination
  5. Run pip install -r requrements.txt in shell
  6. Run python3 main.py

TODO:
* Download media files
* Download assignment submissions