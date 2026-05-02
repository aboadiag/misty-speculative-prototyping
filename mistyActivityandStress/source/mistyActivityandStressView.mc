import Toybox.Graphics;
import Toybox.WatchUi;
import Toybox.Sensor; // Added for live HR display

class mistyActivityandStressView extends WatchUi.View {

    function initialize() {
        View.initialize();
    }

    // FIX: Change 'Dc' to 'Graphics.Dc'
    function onLayout(dc as Graphics.Dc) as Void {
        // We aren't using a layout file, so we can leave this empty
    }

    // FIX: Change 'Dc' to 'Graphics.Dc'
    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);

        var info = Sensor.getInfo();
        var hrValue = (info != null && info.heartRate != null) ? info.heartRate.toString() : "--";

        var centerX = dc.getWidth() / 2;
        var centerY = dc.getHeight() / 2;

        dc.drawText(centerX, centerY - 40, Graphics.FONT_SMALL, "Misty Link P01", Graphics.TEXT_JUSTIFY_CENTER);
        
        // Use a slightly safer font if THAI_HOT is causing the crash
        dc.drawText(centerX, centerY, Graphics.FONT_NUMBER_MEDIUM, hrValue, Graphics.TEXT_JUSTIFY_CENTER);
        
        dc.drawText(centerX, centerY + 50, Graphics.FONT_TINY, "Sending to Misty...", Graphics.TEXT_JUSTIFY_CENTER);
    }

    function onShow() as Void { }
    function onHide() as Void { }
}