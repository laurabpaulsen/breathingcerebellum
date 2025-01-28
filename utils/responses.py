from pynput import keyboard

class KeyboardListener:
    """A class to listen for keyboard inputs."""
    
    def __init__(self, valid_keys = ["b", "y", "1", "2"], active=False):
        self.active = active
        self.key_pressed = None
        self.listener = None
        self.valid_keys = valid_keys

    def on_press(self, key):
            key_name = getattr(key, 'char', str(key))  # safer retrieval
            if self.active and key_name in self.valid_keys:
                self.key_pressed = key_name
        
    def start_listener(self):
        """Start the keyboard listener."""
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def stop_listener(self):
        """Stop the keyboard listener."""
        if self.listener:
            self.listener.stop()

    def get_response(self):
        """Retrieve the last key pressed and reset the key state."""
        response = self.key_pressed
        self.key_pressed = None  # Reset after capturing
        
        return response