import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
import Toybox.Application;

class mistyStateDetectionMenuDelegate extends WatchUi.MenuInputDelegate {

    function initialize() {
        MenuInputDelegate.initialize();
    }

    function onMenuItem(item as Symbol) as Void {
        var selectedChoice = "none";
        var updateText = "";

        // Determine which item was clicked and what text to show
        if (item == :item_breathe) {
            selectedChoice = "breathe";
            updateText = "[ANIM:BREATHE]";
        } else if (item == :item_walk) {
            selectedChoice = "walk";
            updateText = "Take a quick\nwalk or stretch.";
        } else if (item == :item_imagery) {
            selectedChoice = "imagery";
            updateText = "Close your eyes.\nVisualize a calm place.";
        } else if (item == :item_ignore) {
            selectedChoice = "ignore";
            updateText = "I'm here for you.";
        }

        var app = Application.getApp() as mistyStateDetectionApp;

        if (app != null) {
            // 🚨 CRITICAL FIX: Directly set the variable instead of calling a function.
            // This guarantees no "Symbol Not Found" crashes!
            app.queuedChoice = selectedChoice; 
            
            // Instantly update the UI so the user gets immediate feedback
            if (app.view != null) {
                app.view.updateState(null, updateText);
            }
        }
    }
}