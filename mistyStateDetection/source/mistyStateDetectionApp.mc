import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Communications;
import Toybox.Timer;
import Toybox.Activity;

class mistyStateDetectionApp extends Application.AppBase {
    var view as mistyStateDetectionView?;
    var pollTimer as Timer.Timer?;

    // 🚨 THE QUEUE: Safely holds the menu choice until the network sends it
    var queuedChoice as Lang.String = "none";

    // 🚦 THE TRAFFIC LIGHT: Prevents overlapping HTTP requests
    var isNetworkBusy as Lang.Boolean = false;

    // UPDATE THESE WITH YOUR CURRENT NGROK URL
    hidden var NGROK_GARMIN = "https://3793-128-237-82-122.ngrok-free.app/get_situation";
    hidden var NGROK_CHOICE_URL = "https://3793-128-237-82-122.ngrok-free.app/user_choice";

    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() {
        view = new mistyStateDetectionView();
        
        pollTimer = new Timer.Timer();
        // Fire one tick every 3 seconds
        pollTimer.start(method(:onNetworkTick) as Method() as Void, 3000, true);
        
        return [ view, new mistyStateDetectionDelegate() ];
    }

    function queueChoice(choice as Lang.String) as Void {
        queuedChoice = choice;
    }

    function onNetworkTick() as Void {
        if (isNetworkBusy) { return; }

        if (!queuedChoice.equals("none")) {
            executeSendChoice(queuedChoice);
            queuedChoice = "none"; 
        } else {
            executeFetchData();
        }
    }

    function executeFetchData() as Void {
        var info = Activity.getActivityInfo();
        var currentBr = 15;
        if (info != null && info.currentHeartRate != null) {
            currentBr = info.currentHeartRate;
        }

        isNetworkBusy = true;

        var params = { "breath_rate" => currentBr };
        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_POST,
            :headers => { "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON, "ngrok-skip-browser-warning" => "true" },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        try {
            Communications.makeWebRequest(NGROK_GARMIN, params, options, method(:onReceiveData) as Method(code as Lang.Number, data as Lang.Dictionary or Null) as Void);
        } catch(e) {
            System.println("Fetch failed");
            isNetworkBusy = false;
        }
    }

    function onReceiveData(code as Lang.Number, data as Lang.Dictionary or Null) as Void {
        isNetworkBusy = false; 
        
        if (code == 200 && data != null) {
            var br = data.get("breath_rate");
            var msg = data.get("watch_message");
            
            // The watch ONLY updates its UI based on what Python tells it!
            if (view != null) {
                view.updateState(br, msg);
            }
        }
    }

    function executeSendChoice(choice as String) as Void {
        isNetworkBusy = true;
        
        var params = { "choice" => choice };
        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_POST,
            :headers => {
                "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON,
                "ngrok-skip-browser-warning" => "true"
            },
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        try {
            Communications.makeWebRequest(
                NGROK_CHOICE_URL, params, options, 
                method(:onChoiceResponse) as Method(code as Lang.Number, data as Lang.Dictionary or Null) as Void
            );
        } catch (ex) {
            System.println("[ERROR] Choice send failed");
            isNetworkBusy = false; 
        }
    }

    function onChoiceResponse(code as Lang.Number, data as Lang.Dictionary or Null) as Void {
        isNetworkBusy = false; 

        if (code == 200) {
            System.println("[SUCCESS] Server received choice.");
        } else {
            System.println("[ERROR] Server rejected choice.");
        }
    }
}