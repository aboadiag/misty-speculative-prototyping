import Toybox.Graphics;
import Toybox.WatchUi;
import Toybox.Activity; // Swapped ActivityMonitor for Activity
import Toybox.Communications;
import Toybox.Timer;
import Toybox.Lang;
import Toybox.System; // Added this for the System.print logs

class MistyActivityMonitorView extends WatchUi.View {

    // --- CONFIGURATION ---
    // Updated endpoint to /update_activity
    hidden var LAPTOP_URL = "https://6332-128-237-82-119.ngrok-free.app/update_activity"; 
    
    hidden var _timer;
    hidden var _currentActivity = "STILL";
    hidden var _statusMessage = "Ready";

    function initialize() {
        View.initialize();
        _timer = new Timer.Timer();
    }

    function onShow() {
        _timer.start(method(:onTimer), 3000, true);
    }

    function onHide() {
        _timer.stop();
    }

    // 3. Updated Logic Loop for Activity Recognition
    function onTimer() {
        var info = Activity.getActivityInfo();
        var newActivity = "STILL";

        // This 'has :currentSport' is what fixes your 'Undefined symbol' error
        if (info != null && info has :currentSport && info.currentSport != null) {
            var sport = info.currentSport;
            
            System.print("Checking Activity... Sport ID: " + sport);

            if (sport == Activity.SPORT_WALKING) {
                newActivity = "WALKING";
            } else if (sport == Activity.SPORT_RUNNING) {
                newActivity = "RUNNING";
            } else if (sport == Activity.SPORT_CYCLING) {
                newActivity = "CYCLING";
            } else {
                newActivity = "ACTIVE"; 
            }
        } else {
            System.print("Activity Info is NULL or hasn't started yet.");
        }
        
        _currentActivity = newActivity;
        
        // Only send if we are in a valid state
        sendToMisty(_currentActivity);
        
        WatchUi.requestUpdate(); 
    }
    // 4. Send Activity String to Python
    function sendToMisty(activity) {
        _statusMessage = "Sending " + activity + "...";
        
        var payload = {
            "activity_type" => activity,
            "confidence" => 100
        };

        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_POST,
            :headers => { "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        Communications.makeWebRequest(
            LAPTOP_URL,
            payload,
            options,
            method(:onReceive)
        );
    }

    function onReceive(responseCode as Lang.Number, data as Lang.Dictionary or String or Null) as Void {
        if (responseCode == 200) {
            _statusMessage = "Updated!";
        } else {
            _statusMessage = "Err: " + responseCode;
        }
        WatchUi.requestUpdate();
    }

    // 6. Update the Watch UI to show Activity
    function onUpdate(dc) {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        
        var w = dc.getWidth();
        var h = dc.getHeight();
        
        dc.drawText(w/2, h/2 - 40, Graphics.FONT_MEDIUM, "Activity State", Graphics.TEXT_JUSTIFY_CENTER);
        
        // Use a smaller font if the activity name is long
        dc.drawText(w/2, h/2, Graphics.FONT_LARGE, _currentActivity, Graphics.TEXT_JUSTIFY_CENTER);
        
        dc.drawText(w/2, h/2 + 50, Graphics.FONT_XTINY, _statusMessage, Graphics.TEXT_JUSTIFY_CENTER);
    }
}