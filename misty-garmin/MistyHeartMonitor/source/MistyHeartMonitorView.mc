import Toybox.Graphics;
import Toybox.WatchUi;
import Toybox.ActivityMonitor;
import Toybox.Communications;
import Toybox.Timer;
import Toybox.Lang;

class MistyHeartMonitorView extends WatchUi.View {

    // --- CONFIGURATION ---
    // TODO: REPLACE THIS IP with your Laptop's real IP Address (e.g., 192.168.1.50)
    // Keep the :5000/update_breath part at the end.
    hidden var LAPTOP_URL = "https://d240-128-237-82-210.ngrok-free.app/update_breath"; // connect to ngrok then to my laptop
    
    hidden var _timer;
    hidden var _currentRate = 0;
    hidden var _statusMessage = "Ready";

    function initialize() {
        View.initialize();
        _timer = new Timer.Timer();
    }

    // 1. Start the timer when the app opens
    function onShow() {
        // Run 'onTimer' every 3000ms (3 seconds)
        _timer.start(method(:onTimer), 3000, true);
    }

    // 2. Stop the timer when app closes
    function onHide() {
        _timer.stop();
    }

    // 3. The Logic Loop (Runs every 3 seconds)
    function onTimer() {
        var info = ActivityMonitor.getInfo();

        // Check for Breath Rate
        if (info has :respirationRate && info.respirationRate != null) {
            _currentRate = info.respirationRate;
            sendToMisty(_currentRate);
        } else {
            // If watch is loose or not reading, just send 0 or keep last known
            _statusMessage = "Reading...";
             // optional: still send 0 to let Python know we lost signal
        }
        
        WatchUi.requestUpdate(); // Refresh screen
    }

    // 4. Send Data to Python
    function sendToMisty(rate) {
        _statusMessage = "Sending " + rate + "...";
        
        var payload = {
            "breath_rate" => rate
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

// 5. Handle Response from Laptop
    // We added specific types (Lang.Number, etc.) to satisfy the strict compiler
    function onReceive(responseCode as Lang.Number, data as Lang.Dictionary or String or Null) as Void {
        if (responseCode == 200) {
            _statusMessage = "Sent!";
        } else {
            _statusMessage = "Err: " + responseCode;
        }
        WatchUi.requestUpdate();
    }

    // 6. Draw the Watch Screen
    function onUpdate(dc) {
        // Clear screen to black
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        // Text Color White
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        
        var w = dc.getWidth();
        var h = dc.getHeight();
        
        // Draw the stats
        dc.drawText(w/2, h/2 - 40, Graphics.FONT_MEDIUM, "Breath Rate", Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(w/2, h/2, Graphics.FONT_NUMBER_HOT, _currentRate.toString(), Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(w/2, h/2 + 50, Graphics.FONT_XTINY, _statusMessage, Graphics.TEXT_JUSTIFY_CENTER);
    }
}