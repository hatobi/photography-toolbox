# Simulate selecting all (Command + A)
osascript -e 'tell application "System Events" to keystroke "a" using {command down}'
sleep 0.2  # small delay to ensure copy completes

# Simulate copying (Command + C)
osascript -e 'tell application "System Events" to keystroke "c" using {command down}'
sleep 0.2  # small delay to ensure copy completes

# Process clipboard: replace dashes with spaces and remove digits
pbpaste | tr '-' ' ' | sed 's/[0-9]//g' | pbcopy

# Simulate pasting (Command + V)
osascript -e 'tell application "System Events" to keystroke "v" using {command down}'
sleep 0.2  # small delay to ensure copy completes

#Simulate Enter
osascript -e 'tell application "System Events" to key code 36'