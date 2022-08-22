h. Prerequisite
hh. A bot token
(telegram bot)[https://core.telegram.org/bots]

hh. chrome driver
Download the compatible chrome driver from (chromium)[https://chromedriver.chromium.org/downloads]

hh. python environment
Conda environment is strongly encouraged. Config the virtual env with pip is plausible 

h. Setup
complete sample_config.ini
There are two mandatory fields **token** and **chrome_driver**. **heartbeat_recipient_id** is optional    


h. Bot Usage

/start to start searching
/pause to pause, bring the bot to **PAUSE** mode
/update to update restaurant. /update will only be executed when the bot is in **PAUSE** mode
/resume to resume searching


