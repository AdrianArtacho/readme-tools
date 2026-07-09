Instrumentation.py

the idea is that this script will be called:

./tools/readme/instrumentation.py piano+electronik

then, the script will:

- clone locally the git repository 'Coursework' 
- latexpand it into one tex file
- select only the content within the environments 'piano' and 'elektronik'
- create (if not existing yet) a folder 'refs'
- create (if not existing yet) a subfolder 'refs/inst'
- render that latex content selected onto md files inside refs/inst (one file per instrument, include images in a subfolder 'img'), namely:
    refs/inst/piano.md
    refs/inst/electronik.md
