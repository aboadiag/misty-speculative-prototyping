import Toybox.Lang;
import Toybox.WatchUi;

class mistyStateDetectionDelegate extends WatchUi.BehaviorDelegate {

    function initialize() {
        BehaviorDelegate.initialize();
    }

    function onMenu() as Boolean {
        WatchUi.pushView(new Rez.Menus.MainMenu(), new mistyStateDetectionMenuDelegate(), WatchUi.SLIDE_UP);
        return true;
    }

}