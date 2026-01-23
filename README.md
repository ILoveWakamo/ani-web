# AniWeb

This project is a simple Flask-based web application that allows users to search for anime, browse episodes, and stream them directly in the browser by fetching available MP4/HLS sources from Allanime.

It is designed primarily as a personal experimental project.



## Features

- Search anime titles using Allanime search  
- AniList-powered autocomplete for anime titles  
- Episode listing and playback  
- Automatic fetching of available MP4/HLS stream links  
- Simple web-based video player  
- No account or login required  



## Inspiration and Credits

This project is **heavily inspired by [ani-cli](https://github.com/pystardust/ani-cli)**.

Much of the logic and overall approach for fetching episodes and stream URLs is based on how `ani-cli` works. Full credit goes to the `ani-cli` contributors for their excellent project and research.

This project is **not affiliated with ani-cli** and does not aim to be a replacement for it.

## Requirements

- Python 3.9+ (recommended)  
- pip  
## Installation

Clone the repository:

```bash
git clone https://github.com/ILoveWakamo/ani-web.git
cd ani-web
```

(Optional but recommended) Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```
    
## Run Locally

Start the Flask server:

```bash
python app.py
```

By default, the app will run on:

```
http://0.0.0.0:5000
```

Open your browser and navigate to:

```
http://localhost:5000
```

For production-level deployment, it is recommended to use a WSGI server. 


## Notes

- This project scrapes and consumes third-party APIs and websites that may change at any time.  
- Stream availability and quality depend entirely on external providers.  

I am a **casual Python developer**, and this project was built primarily for experimentation.  
As a result:

- The code may be messy or inconsistent in places  
- Error handling is not perfect  
- Some parts may be inefficient or hacky  

Contributions, refactors, and suggestions are welcome.
## License

This project is provided as-is for educational and personal use.  
Refer to the `ani-cli` repository for its respective license.


