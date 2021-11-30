# abbr_helper
Abbreviation helper web app - decipher and manage abbreviations easily.


The main goal of this project is simple - to find and decipher abbreviations in text documents.

Current workflow is:
  1. You launch abbr_helper.py and open web interface in browser
  1. You click [upload input file] link and upload DOCX or TXT file
  2. AbbrHelper will return page with all found abbreviations, known or unknown.
  
You can add new abbreviations to DB via [Create abbreviation] button.
Other supported actions for Abbreviations: edit, delete, disable.




INSTALL

  1. Firstly, install prerequesite packages via pip
    pip3 install flask
    pip3 install docx
  
  2. Copy project directory to desired destination
  
  3. Set up autostart, if it is required.
    For systemd-managed Linux distros, edit supplied .service file to reflect path to abbr_helper.py - please edit WorkingDirectory and ExecStart vars. Then copy .service file to systemd service dir. 
    
  4. Start web app
    if you use systemd: systemct start abbr_helper.service
    if you launch manully, run command abbr_helper.py

