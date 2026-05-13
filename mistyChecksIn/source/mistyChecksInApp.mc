import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Communications;
import Toybox.Timer;

class mistyChecksInApp extends Application.AppBase {
    var view as mistyChecksInView?;
    var pollTimer as Timer.Timer?;

    // REPLACE WITH YOUR CURRENT NGROK URL:
    hidden var NGROK_URL = "https://ceb3-128-237-82-150.ngrok-free.app/get_situation";

    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() {
        view = new mistyChecksInView();
        
        // Check the server every 5 seconds for new reminders
        pollTimer = new Timer.Timer();
        pollTimer.start(method(:fetchReminders) as Method() as Void, 5000, true);
        
        return [ view, new mistyChecksInDelegate() ];
    }

    function onStop(state as Lang.Dictionary?) as Void {
        if (pollTimer != null) {
            pollTimer.stop();
        }
    }

    function fetchReminders() as Void {
        var params = { "dummy" => "data" }; // P04 doesn't need to send HR right now
        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_POST,
            :headers => { "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON, "ngrok-skip-browser-warning" => "true" },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        try {
            Communications.makeWebRequest(NGROK_URL, params, options, method(:onReceiveData));
        } catch(e) {
            System.println("Fetch failed");
        }
    }

    function onReceiveData(code as Lang.Number, data as Lang.Dictionary or Null) as Void {
        if (code == 200 && data != null) {
            var msg = data.get("watch_message") as Lang.String;
            if (view != null && msg != null) {
                view.updateMessage(msg);
            }
        }
    }
}