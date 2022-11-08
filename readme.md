## 1. Prerequisite
### 1.1 Obtain a [telegram bot token](https://core.telegram.org/bots)

### 1.2 Download [compatible chrome driver](https://chromedriver.chromium.org/downloads)

### 1.3 python environment
See environment.yaml. A minimum set should have python-telegram-bot>=20.0, pandas, selenium  

## 2. Configure [``sample_config.ini``](src/reservation_bot/sample_config.ini)
There are two mandatory fields **token** and **chrome_driver**.

**heartbeat_recipient_id** is optional.    


## 3. Run!
### launch [``bot_main.py``](src/reservation_bot/bot_main.py)

Bot supports four commands. While ___/change___ requires 2 arguments and other commands don't have any argument.

* ___/start___ - start searching. 
* ___/pause___ - pause searching. This brings the bot to **PAUSE** mode
* ___/resume___ - resume searching
* ___/change \[platform\] \[restaurant\]___ - change search target to \[restaurant\]. 
___/change___ will only take effect executed when the bot is in **PAUSE** mode. 
Example command: ___/change resy don-angies___ or ___/change tock yoshinonewyork___



