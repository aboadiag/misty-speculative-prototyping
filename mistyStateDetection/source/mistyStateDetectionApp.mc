import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Communications;
import Toybox.Timer;


class mistyStateDetectionApp extends Application.AppBase {
    var view as mistyStateDetectionView?;

    hidden var NGROK_GARMIN = "https://3ac1-128-237-82-119.ngrok-free.app/get_situation";

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
        // NGROK_URL/get_situation";
        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_GET,
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        Communications.makeWebRequest(
            url, 
            {}, 
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