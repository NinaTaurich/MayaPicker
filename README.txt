Created By: Nina Taurich

Setup:
download picker and place folder in maya/scripts folder

2.In Maya run code:
from picker import pickerUI
pickerUI.pickerBaseUI()


Dependencies:
Maya and PySide2


Features:
- Add buttons with varying size, color, and text
- A list of check-boxes shows the current world selection allowing the user to easily deselect objects by unchecking them
- Ability to delete buttons
- Add tabs to hold different groups of buttons
- Add pictures so buttons can be displayed over the image
- Save current template in a json format
- Load previous templates
- Hold shift to select multiple buttons
- The UI is dockable in Maya