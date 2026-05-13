import Toybox.Graphics;
import Toybox.WatchUi;
import Toybox.Lang;
import Toybox.Attention; // Required for Vibration!

class mistyChecksInView extends WatchUi.View {
    
    var currentMsg as Lang.String = "Waiting for\nreminders...";
    var lastMsg as Lang.String = "";
    
    // Image references
    var iconDefault as WatchUi.BitmapResource?;
    var iconConcerned as WatchUi.BitmapResource?;
    var iconHappy as WatchUi.BitmapResource?;


    function initialize() {
        View.initialize();
    }

    function onLayout(dc as Dc) as Void {
        // Load your PNG files into memory
        iconDefault = WatchUi.loadResource(Rez.Drawables.misty_default);
        iconConcerned = WatchUi.loadResource(Rez.Drawables.misty_concerned);
        iconHappy = WatchUi.loadResource(Rez.Drawables.misty_happy);

    }

    function updateMessage(msg as Lang.String) as Void {
        // Only update (and vibrate) if the message has actually changed!
        if (!msg.equals(lastMsg) && !msg.equals("")) {
            currentMsg = msg;
            lastMsg = msg;
            
            System.println("New Reminder Received: " + currentMsg);

            // 🚨 TRIGGER VIBRATION
            if (Attention has :vibrate) {
                var vibeData = [new Attention.VibeProfile(100, 1500)]; // Vibrate at 100% for 1.5 seconds
                Attention.vibrate(vibeData);
            }
            
            WatchUi.requestUpdate(); 
        }
    }

    function onUpdate(dc as Dc) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var iconToDraw = iconDefault;
        var displayText = currentMsg;

        // --- CHECK TAGS AND SWAP ICON ---
        if (currentMsg.find("[CONCERNED]") != null) {
            iconToDraw = iconConcerned;
            // Remove the tag from the text before drawing
            displayText = currentMsg.substring(11, currentMsg.length());
        } else if (currentMsg.find("[DEFAULT]") != null) {
            iconToDraw = iconDefault;
            // Remove the tag from the text before drawing
            displayText = currentMsg.substring(9, currentMsg.length());
        }   else if (currentMsg.find("[HAPPY]") != null) {
            iconToDraw = iconHappy;
            // Remove the tag from the text before drawing
            displayText = currentMsg.substring(7, currentMsg.length());
        }

        // Draw the Misty Icon on the RIGHT side
        // x=200 pushes it to the right half of the 390px Venu 3 screen
        if (iconToDraw != null) {
            dc.drawBitmap(200, 100, iconToDraw); 
        }

        // Draw the Reminder Text on the TOP LEFT side
        // x=40, y=90 keeps it safely inside the curved bezel, aligned left
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(40, 90, Graphics.FONT_XTINY, displayText, Graphics.TEXT_JUSTIFY_LEFT);
    }
}