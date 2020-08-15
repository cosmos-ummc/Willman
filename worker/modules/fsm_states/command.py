class Command:
    def __init__(self, command):
        self.command = command[1:]  # remove the '/'
