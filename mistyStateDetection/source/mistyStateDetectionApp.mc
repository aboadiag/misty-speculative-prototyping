import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Communications;
import Toybox.Timer;
import Toybox.Activity; // NEW: Allows us to read the watch's sensors


class mistyStateDetectionApp extends Application.AppBase {
    var view as mistyStateDetectionView?;

    hidden var NGROK_GARMIN = "https://975e-128-237-82-210.ngrok-free.app/get_situation";

    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() {
        view = new mistyStateDetectionView();
        
        var pollTimer = new Timer.Timer();
        // The ':fetchData' method needs to be cast as a Method() as Void
        pollTimer.start(method(:fetchData) as Method() as Void, 3000, true);
        
        return [ view ];
    }

    function fetchData() as Void {
        var url = NGROK_GARMIN;
        var currentBr = 15; // Default safe value

        // --- NEW: READ SIMULATED/REAL SENSOR DATA ---
        var info = Activity.getActivityInfo();
        
        if (info != null) {
            // Try to read the Respiration slider first
            if (info has :respirationRate && info.respirationRate != null) {
                currentBr = info.respirationRate.toNumber(); // Convert to integer
            } 
            // Fallback: If your specific watch simulator doesn't support the 
            // respiration slider, we can fake breath rate using the Heart Rate slider!
            else if (info.currentHeartRate != null) {
                currentBr = (info.currentHeartRate / 4).toNumber(); 
            }
        }

        // --- NEW: PACKAGE DATA TO SEND TO SERVER ---
        var params = {
            "breath_rate" => currentBr
        };

        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_POST, // Changed to POST
            :headers => {
                "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON // Tell server we are sending JSON
            },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        Communications.makeWebRequest(
            url, 
            params, 
            options, 
            method(:onResponse) as Method(code as Lang.Number, data as Lang.Dictionary or Null) as Void
        );
    }

    function onResponse(code as Lang.Number, data as Lang.Dictionary or Null) as Void {
        if (code == 200 && data != null && view != null) {
            // We tell the compiler to 'trust' that view is not null here
            (view as mistyStateDetectionView).updateState(
                data.get("breath_rate"), 
                data.get("watch_message")
            );
        }
    }
}