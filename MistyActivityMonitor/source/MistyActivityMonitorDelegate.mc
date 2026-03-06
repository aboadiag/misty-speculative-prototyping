import Toybox.Lang;
import Toybox.WatchUi;

class MistyActivityMonitorDelegate extends WatchUi.BehaviorDelegate {

    function initialize() {
        BehaviorDelegate.initialize();
    }

    function onMenu() as Boolean {
        WatchUi.pushView(new Rez.Menus.MainMenu(), new MistyActivityMonitorMenuDelegate(), WatchUi.SLIDE_UP);
        return true;
    }

}