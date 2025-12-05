#!/usr/bin/osascript

-- Get screen dimensions
tell application "Finder"
	set screenBounds to bounds of window of desktop
	set screenWidth to item 3 of screenBounds
	set screenHeight to item 4 of screenBounds
end tell

-- Calculate window dimensions
set leftThirdWidth to screenWidth / 3
set twoThirdsWidth to screenWidth * 2 / 3

-- Position terminal windows (iTerm2 or Ghostty) on left third
tell application "System Events"
	set runningApps to name of every process
end tell

-- Handle iTerm/iTerm2
if "iTerm2" is in runningApps or "iTerm" is in runningApps then
	try
		tell application "iTerm"
			set bounds of front window to {0, 0, leftThirdWidth, screenHeight}
		end tell
	end try
end if

-- Handle Ghostty (uses System Events for window manipulation)
if "Ghostty" is in runningApps then
	try
		tell application "System Events"
			tell process "Ghostty"
				if exists window 1 then
					set position of window 1 to {0, 0}
					set size of window 1 to {leftThirdWidth, screenHeight}
				end if
			end tell
		end tell
	end try
end if

-- Position ALL visible IDE windows on right two thirds
set intellijApps to {"IntelliJ IDEA", "PyCharm", "WebStorm", "GoLand", "RubyMine", "PhpStorm", "DataGrip", "CLion", "Rider"}
set ideCount to 0

repeat with appName in intellijApps
	if appName is in runningApps then
		tell application "System Events"
			tell process appName
				try
					repeat with w in (every window)
						set position of w to {leftThirdWidth, 0}
						set size of w to {twoThirdsWidth, screenHeight}
						set ideCount to ideCount + 1
					end repeat
				end try
			end tell
		end tell
	end if
end repeat

display notification "Terminal left, " & ideCount & " IDE windows resized right" with title "Dev Layout"
