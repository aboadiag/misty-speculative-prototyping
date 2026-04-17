import Toybox.Lang;
import Toybox.WatchUi;

class MistyHeartMonitorDelegate extends WatchUi.BehaviorDelegate {

    function initialize() {
        BehaviorDelegate.initialize();
    }

    function onMenu() as Boolean {
        WatchUi.pushView(new Rez.Menus.MainMenu(), new MistyHeartMonitorMenuDelegate(), WatchUi.SLIDE_UP);
        return true;
    }

}