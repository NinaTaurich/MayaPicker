Created By: Nina Taurich


Setup:
1.download picker and place anim_picker folder in maya scripts folder

2.In Maya script editor run python code:
import anim_picker
anim_picker.load()

Demo Video: https://www.youtube.com/watch?v=0LSDkv1S84g&feature=emb_logo


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
