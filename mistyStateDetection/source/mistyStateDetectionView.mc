import Toybox.WatchUi;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Timer;
import Toybox.System;

class mistyStateDetectionView extends WatchUi.View {
    
    var current_icon as WatchUi.BitmapResource?;
    var currentMsg as Lang.String = "";
    var br as Lang.String = "--";

    // Animation Variables
    var isAnimating as Lang.Boolean = false;
    var animTimer as Timer.Timer?;
    var animTick as Lang.Number = 0;
    var breathingText as Lang.String = "";
    var cycleCount as Lang.Number = 0;
    var animStartTime as Lang.Number = 0; // Tracks when animation started for the shield

    // We store RESOURCE IDs, not the actual images, to save memory!
    var animFrameIds as Lang.Array<Lang.ResourceId> = new [10] as Lang.Array<Lang.ResourceId>;

    function initialize() {
        View.initialize(); 

        animFrameIds[0] = Rez.Drawables.frame_1;
        animFrameIds[1] = Rez.Drawables.frame_2;
        animFrameIds[2] = Rez.Drawables.frame_3;
        animFrameIds[3] = Rez.Drawables.frame_4;
        animFrameIds[4] = Rez.Drawables.frame_5;
        animFrameIds[5] = Rez.Drawables.frame_6;
        animFrameIds[6] = Rez.Drawables.frame_7;
        animFrameIds[7] = Rez.Drawables.frame_8;
        animFrameIds[8] = Rez.Drawables.frame_9;
        animFrameIds[9] = Rez.Drawables.frame_10;
        
        loadDefaultFace();
    }

    function loadDefaultFace() as Void {
        try {
            current_icon = WatchUi.loadResource(Rez.Drawables.MistyDefault);
        } catch(e) {
            System.println("Default icon load failed.");
        }
    }

    // --- THE TRIGGER ---
    function startBreathingAnimation() as Void {
        if (isAnimating) { return; } 
        
        System.println(">>> STARTING BREATHING ANIMATION <<<");
        isAnimating = true;
        animTick = 0;
        cycleCount = 0; 
        breathingText = "Inhale..."; 
        animStartTime = System.getTimer(); // ✅ Uses correct Garmin timer function

        // Safely load just the first frame
        try { current_icon = WatchUi.loadResource(animFrameIds[0]); } catch(e) {}

        // ✅ Memory-Safe Timer Initialization
        if (animTimer != null) { 
            animTimer.stop(); 
        } else {
            animTimer = new Timer.Timer();
        }
        
        animTimer.start(method(:onAnimTick), 1000, true); 

        WatchUi.requestUpdate(); 
    }

    // --- THE STOP ---
    function stopBreathingAnimation() as Void {
        if (!isAnimating) { return; }
        
        System.println(">>> STOPPING ANIMATION <<<");
        isAnimating = false;
        
        if (animTimer != null) { 
            animTimer.stop();
        }
        
        loadDefaultFace();
        WatchUi.requestUpdate();
    }

    // --- NETWORK STATE HANDLER ---
    function updateState(newBr as Lang.Object or Null, newMsg as Lang.String or Null) as Void {
        if (newBr != null) { br = newBr.toString(); }

        if (newMsg != null) {
            if (newMsg.find("[ANIM:BREATHE]") != null) {
                startBreathingAnimation();
            } 
            else if (isAnimating) {
                // ✅ CLAUDE'S SHIELD FIX: Ignore messages for the first 3 seconds
                if (System.getTimer() - animStartTime < 3000) {
                    return; 
                }
                
                // Keep ignoring standard anxious/reset messages while breathing
                if (newMsg.equals("Anxious? Press Start for options.") || newMsg.equals("reset")) {
                    return;
                }
                
                // If it's a completely new, valid message, stop animation and show it
                stopBreathingAnimation();
                currentMsg = newMsg;
            }
            else if (!newMsg.equals("")) {
                stopBreathingAnimation();
                currentMsg = newMsg;
            }
            else if (newMsg.equals("") && !isAnimating) {
                currentMsg = "";
            }
        }
        WatchUi.requestUpdate();
    }
    
    // --- THE ANIMATION LOOP ---
    function onAnimTick() as Void {
        if (!isAnimating) { return; } // Safety check
        
        animTick++;
        if (animTick >= 10) { 
            animTick = 0; 
            cycleCount++;
            
            // AUTO-STOP: Stop after 3 full breaths (30 seconds)
            if (cycleCount >= 3) {
                System.println("[ANIMATION] 3 breaths completed. Stopping.");
                stopBreathingAnimation();
                currentMsg = "Great job.";
                WatchUi.requestUpdate();
                return;
            }
        }

        if (animTick < 4) { breathingText = "Inhale..."; }
        else if (animTick < 6) { breathingText = "Hold..."; }
        else { breathingText = "Exhale..."; }

        // ✅ Memory-safe load per tick
        try { 
            current_icon = WatchUi.loadResource(animFrameIds[animTick]); 
        } catch(e) {
            System.println("Frame load failed at: " + animTick);
        }
        
        WatchUi.requestUpdate(); 
    }

    // ✅ CLEANUP WHEN VIEW IS HIDDEN (Great Catch by Claude)
    function onHide() as Void {
        System.println("[VIEW] onHide called - cleaning up animation");
        if (animTimer != null) {
            animTimer.stop();
        }
        isAnimating = false;
    }

    // --- THE DRAW FUNCTION ---
    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        if (current_icon != null) {
            // Centered draw (adjust 120, 80 based on your screen size)
            dc.drawBitmap(200, 100, current_icon); 
        }

        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(45, 90, Graphics.FONT_XTINY, "BR: " + br, Graphics.TEXT_JUSTIFY_LEFT);

        if (isAnimating) {
            // x, y
            dc.drawText(45, 240, Graphics.FONT_SMALL, breathingText, Graphics.TEXT_JUSTIFY_CENTER);
        } else if (currentMsg != null && !currentMsg.equals("")) {
            dc.drawText(45, 240, Graphics.FONT_XTINY, currentMsg, Graphics.TEXT_JUSTIFY_CENTER);
        }
    }
}