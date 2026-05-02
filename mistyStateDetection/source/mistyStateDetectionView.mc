import Toybox.WatchUi;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Attention;

class mistyStateDetectionView extends WatchUi.View {
    // 1. Declare variables one per line with explicit types
    var happyIcon as WatchUi.BitmapResource?;
    var concernedIcon as WatchUi.BitmapResource?;
    var defaultIcon as WatchUi.BitmapResource?;
    var currentMsg as Lang.String = "";
    var br as Lang.String = "--";
    var isAnxious as Lang.Boolean = false;

    // --- Flag to track the initial startup ---
    var isFirstUpdate as Lang.Boolean = true;

    var breath_rate = 15;
    var watch_message = "";
    var current_icon as WatchUi.BitmapResource?;

    function initialize() {
        View.initialize(); 
    }

    function onLayout(dc as Graphics.Dc) as Void {
        // 2. Explicitly cast the loaded resources as BitmapResources
        happyIcon = WatchUi.loadResource(Rez.Drawables.MistyHappy) as WatchUi.BitmapResource;
        concernedIcon = WatchUi.loadResource(Rez.Drawables.MistyConcerned) as WatchUi.BitmapResource;
        defaultIcon = WatchUi.loadResource(Rez.Drawables.MistyDefault) as WatchUi.BitmapResource;

        current_icon = defaultIcon;
    }


    // 3. Accept multiple types since JSON data can sometimes be a Number, String, or Null
    function updateState(newBr as Lang.Number or Lang.String or Null, newMsg as Lang.String or Null) as Void {
        
        // Convert the breath rate to a string for the UI
        if (newBr != null) {
            br = newBr.toString();
        }
        
        // Handle the message and vibration safely
        if (newMsg != null) {
            if (!newMsg.equals("") && !newMsg.equals(currentMsg)) {
                // Ensure the watch actually supports vibration before calling it
               // --- NEW LOGIC: Suppress vibration on app startup! ---
                // Similar to p05's calibration, we skip the beep on the very first update
                if (!isFirstUpdate && Attention has :vibrate) {
                    Attention.vibrate([new Attention.VibeProfile(100, 500)]);
                }
                // --- Check message content to decide the emotion! ---
                if (newMsg.find("Good") != null) {
                    // It's the reward message! Show Happy Misty.
                    isAnxious = false;
                    current_icon = happyIcon;
                } else {
                    // It's the anxiety message. Show Concerned Misty.
                    isAnxious = true;
                    current_icon = concernedIcon;
                }
                
            } else if (newMsg.equals("")) {
                isAnxious = false;
                // Swap back to happy image
                current_icon = WatchUi.loadResource(Rez.Drawables.MistyHappy);
            }
            currentMsg = newMsg;
        }

        // --- The initial load is over, allow vibrations for future updates ---
        isFirstUpdate = false;
        
        WatchUi.requestUpdate();
    }

     function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        // 2. Draw Misty on the RIGHT side
        // X = 230 pushes her to the right half of the 454px screen
        // Y = 80 drops her down slightly from the top edge
        if (current_icon != null) {
            dc.drawBitmap(230, 80, current_icon); 
        }

        // 3. Draw the Breath Rate on the LEFT side
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(50, 100, Graphics.FONT_MEDIUM, "BR: " + br, Graphics.TEXT_JUSTIFY_LEFT);

        // 4. Draw the Wrapped Text Box on the LEFT side
        if (currentMsg != null && !currentMsg.equals("")) {
            var textArea = new WatchUi.TextArea({
                :text => currentMsg,
                :color => Graphics.COLOR_WHITE,
                :font => Graphics.FONT_XTINY, 
                :locX => 50,          // Start near the left edge
                :locY => 150,         // Start right below the Breath Rate
                :width => 180,        // Restrict the width to the left half of the screen
                :height => 250,       // HUGE height limit so it never triggers the "..."
                :justification => Graphics.TEXT_JUSTIFY_LEFT // Left-align the text itself
            });
            
            textArea.draw(dc); 
        }
    }

}