import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;

class mistyStateDetectionDelegate extends WatchUi.BehaviorDelegate {

    function initialize() {
        BehaviorDelegate.initialize();
    }

    function onSelect() as Lang.Boolean {
        // 1. Get the app and the view to check the current watch state
        var app = Application.getApp() as mistyStateDetectionApp;
        var view = app.view as mistyStateDetectionView;

        // 2. THE LOCK: Only trigger the menu if the anxiety alert is active!
        if (view != null && view.currentMsg != null) {
            if (view.currentMsg.equals("Anxious? Press Start for options.")) {
                System.println("[STATE] Anxiety detected. Opening Menu!");
                WatchUi.pushView(new Rez.Menus.MainMenu(), new mistyStateDetectionMenuDelegate(), WatchUi.SLIDE_UP);
                return true;
            }
        }

        // 3. DO NOTHING: User tapped screen but isn't anxious
        System.println("[STATE] Screen tapped, but menu is locked (No Anxiety).");
        return true; 
    }

}