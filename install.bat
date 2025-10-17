@echo You need the following installed:
@echo opencv, python 3.12, the camera as generic USB cam (if it shows up with picture in discord/zoom/etc, you are set)
@echo Also if you are on the windows media player-less N Windows, install the Media Feature Pack
python -m venv ./
./Scripts/activate.bat
pip install numpy
pip install opencv_contrib_python