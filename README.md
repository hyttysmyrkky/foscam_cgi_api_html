# foscam_cgi_api_html
A simple browser-based way to communicate with Foscam CGI API compatible HD IP cameras (incl. for example the Opticam brand).

Features:
- Setup the camera, manage users, wifi settings, IP settings
- Supports multiple cameras
- Remembers the configuration and settings
- Settings can be exported as a json file, and imported
- Set motion detection area and schedule
- Get a still image from camera
- Turn infrared off/on
- ... and almost everything else that can be done with Foscam CGI API
- Monitor selected cameras with a fullscreen view displaying snapshots at a chosen interval
- Operate PTZ+focus in a pinch
- No ads, no installation, no dependencies or browser plugins. Only a single portable file. Greetings from Finland!

This tool does not
- show video from camera, but only parses the RTSP links to open in another program. Without the video stream, operating PTZ is possible but clumsy.
- support non-HD cameras (they use the older version of the API)

## How to use
Download the `index.html` and open it (with a browser). In practice that can be done at least by 'saving as' [the raw view of the index.html](https://raw.githubusercontent.com/hyttysmyrkky/foscam_cgi_api_html/main/index.html). Please read the "Security notes" below. Further instructions are in the tool itself.

Alternatively, you can [preview the page by using htmlpreview.github.io](https://htmlpreview.github.io/?https://github.com/hyttysmyrkky/foscam_cgi_api_html/blob/main/index.html), but saving the camera address etc. may not work, or if it does, note that any other \*.github.io page can probably read all saved data, including camera credentials as clear-text.

## Security notes
- Data is saved to localStorage only on the browser you are using.
- Requests to cameras use unencrypted HTTP and the credentials are clear-text and show up in the browser page history.
- Use this only on your personal machine, and so that the cameras are accessed via LAN (or VPN or similar). On the other hand, if you can access your cameras over the internet without VPN or similar, you should reconfigure your firewalls.
- This is a very simple tool to parse the Foscam API URLs, and therefore best practices in terms of information security, mitigation for XSS etc. are not implemented.
- If you're not sure whether the above isn't a problem in your case, do not input real address or credentials of your cameras. Review the contents of the index.html (which contains HTML, CSS and JavaScript).

## How this was developed
1. The contents (chapters 2 and 3) of the Foscam PDF were copy pasted into [a text file](https://github.com/hyttysmyrkky/foscam_cgi_api_html/blob/main/src/Foscam-IPCamera-CGI-User-Guide-AllPlatforms-2015.11.06.pdf.txt).
2. [A Python script](https://github.com/hyttysmyrkky/foscam_cgi_api_html/blob/main/src/parse_pdf_to_json.py) was created to parse the API into a [JSON](https://github.com/hyttysmyrkky/foscam_cgi_api_html/blob/a21d45395c0bf15a8c76047754126e1791b33f65/index.html#L1134).
3. Everything else was written into [the HTML template file](https://github.com/hyttysmyrkky/foscam_cgi_api_html/blob/main/src/index_template.html). The Python script reads the template file, inserts the parsed JSON into it, and writes the result as the [index.html](https://github.com/hyttysmyrkky/foscam_cgi_api_html/blob/main/index.html).

## Design choices & goals
- platform-agnostic
- no installation
- no backend (server, other than the browser)
- easy to review, audit and understand by non-web-developers
- no (unnecessary) dependencies
- must be able to setup and manage (while maybe not operate, e.g. PTZ) a camera without using the Windows or browser plugin based 'official' tools
- transparent in terms of the commands sent to camera
- single portable file

## How to contribute (and areas for improvement)
- importConfig, exportConfig and fwUpgrade commands (under the System view) are not tested.
- Pull requests or Issues about typos or commands that don't work, and all kinds of testing is welcome.
- The command tables of the PDF should be parsed by using some proper python library or other tool, instead of the ugly python script. However, the format of the produced JSON should be preserved, because the html/javascript depends on it. Also the python script currently includes manual fixes and additions to the PDF contents, which should also be preserved.
- Adding or fixing some commands or their parameters should be done at the end of the python script (instead of directly to the JSON in index.html); otherwise the changes will get overwritten when you run `python3 parse_pdf_to_json.py`
- Alternatively a complete JSON representation of the Foscam API could be created (even manually). Some other Github projects could benefit from that too.
- As a workaround to CORS, the commands are sent by opening a new tab with the correct URL. This makes it impossible to parse the response and also to real-time-operate the camera (e.g. PTZ). This could possibly be improved, even if some well-known dependency is needed.
- Ideas how to improve the listed Security notes, if they don't conflict with the design choices too much.

## License
Apache-2.0 (c) hyttysmyrkky

## Disclaimer
This project is not related to Foscam or any other manufacturer, but is fully 3rd-party-contributed. If this repository contains the original API PDF documentation, it shouldn't be considered as a part of this repository in terms of license etc. You should get the latest version of the PDF from the Foscam website. Use at your own risk. I take no responsibility if your IP camera explodes.

## Acknowledgements & related
* [The Foscam IPCamera CGI User Guide (PDF)](https://www.foscam.es/descarga/Foscam-IPCamera-CGI-User-Guide-AllPlatforms-2015.11.06.pdf)
