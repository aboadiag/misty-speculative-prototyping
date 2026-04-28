import Toybox.WatchUi;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Attention;

class mistyStateDetectionView extends WatchUi.View {
    // 1. Declare variables one per line with explicit types
    var happyIcon as WatchUi.BitmapResource?;
    var concernedIcon as WatchUi.BitmapResource?;
    var currentMsg as Lang.String = "";
    var br as Lang.String = "--";
    var isAnxious as Lang.Boolean = false;

    function initialize() {
        View.initialize();
    }

    function onLayout(dc as Graphics.Dc) as Void {
        // 2. Explicitly cast the loaded resources as BitmapResources
        happyIcon = WatchUi.loadResource(Rez.Drawables.MistyHappy) as WatchUi.BitmapResource;
        concernedIcon = WatchUi.loadResource(Rez.Drawables.MistyConcerned) as WatchUi.BitmapResource;
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var icon = isAnxious ? concernedIcon : happyIcon;
        
        // Safety check before drawing
        if (icon != null) {
            dc.drawBitmap((dc.getWidth() / 2) - (icon.getWidth() / 2), 30, icon);
        }

        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(dc.getWidth() / 2, 130, Graphics.FONT_MEDIUM, "BR: " + br, Graphics.TEXT_JUSTIFY_CENTER);
        
        if (!currentMsg.equals("")) {
            dc.setColor(Graphics.COLOR_RED, Graphics.COLOR_TRANSPARENT);
            dc.drawText(dc.getWidth() / 2, 170, Graphics.FONT_SMALL, currentMsg, Graphics.TEXT_JUSTIFY_CENTER);
        }
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
                if (Attention has :vibrate) {
                    Attention.vibrate([new Attention.VibeProfile(100, 500)]);
                }
                isAnxious = true;
            } else if (newMsg.equals("")) {
                isAnxious = false;
            }
            currentMsg = newMsg;
        }
        
        WatchUi.requestUpdate();
    }
}