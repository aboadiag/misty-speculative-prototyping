import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Sensor;
import Toybox.Activity;
import Toybox.Timer;
import Toybox.Communications;
import Toybox.ActivityRecording;

class mistyActivityandStressApp extends Application.AppBase {
    var dataTimer as Timer.Timer?;
    var session as ActivityRecording.Session?;
    var serverUrl = "https://58e3-128-237-82-212.ngrok-free.app/update_garmin";

    function initialize() {
        AppBase.initialize();
    }

    // FIX: Added Lang. prefix to Dictionary
    function onStart(state as Lang.Dictionary?) as Void {
        if (Toybox has :ActivityRecording) {
            session = ActivityRecording.createSession({
                :name=>"MistyStudy", 
                :sport=>Activity.SPORT_GENERIC
            });
            session.start();
        }

        dataTimer = new Timer.Timer();
        // FIX: Explicitly cast method to (Method() as Void)
        dataTimer.start(method(:onTimerUpdate) as Method() as Void, 2000, true);
    }

    function onTimerUpdate() as Void {
        var sInfo = Sensor.getInfo();
        var aInfo = Activity.getActivityInfo();

        if (sInfo != null && sInfo.heartRate != null) {
            var payload = {
                "heart_rate" => sInfo.heartRate,
                "activity_score" => (aInfo != null && aInfo.currentSpeed != null) ? aInfo.currentSpeed : 0.0
            };

            var options = {
                :method => Communications.HTTP_REQUEST_METHOD_POST,
                :headers => {"Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON}
            };

            Communications.makeWebRequest(
                serverUrl,
                payload,
                options,
                // FIX: Cast method to match the specific signature required by makeWebRequest
                method(:onWebResponse) as Method(responseCode as Lang.Number, data as Lang.Dictionary or Lang.String or Null) as Void
            );
        }
    }

    function onWebResponse(code as Lang.Number, data as Lang.Dictionary or Lang.String or Null) as Void {
        System.println("Misty Server Response: " + code);
    }

    // FIX: Added Lang. prefix to Dictionary
    function onStop(state as Lang.Dictionary?) as Void {
        if (dataTimer != null) {
            dataTimer.stop();
        }
        if (session != null) {
            session.stop();
            session.save();
            session = null;
        }
    }

   function getInitialView() {
        return [ new mistyActivityandStressView() ];
    }
}