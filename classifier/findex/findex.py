class Findex:
    def __init__(self, directory):
        self.directory = directory
        self.media_files = []

    def scan(self):
        import os
        
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if file.endswith(('.mp4', '.avi', '.mkv', '.mov')):
                    file_path = os.path.join(root, file)
                    self.media_files.append({
                        'path': file_path,
                        'name': file,
                        'size': os.path.getsize(file_path),
                        'type': file.split('.')[-1]
                    })

    def get_media_files(self):
        return self.media_files

    def save_to_database(self, db_connection):
        # Placeholder for database saving logic
        pass