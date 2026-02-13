import os
import shutil
import datetime
import uuid


class Commit:
    def __init__(self, message, commit_id):
        self.message = message
        self.id = str(commit_id)
        self.time = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")

    def save(self, wit_dir):
        """
        1. יוצרת תיקייה בשם ה-ID בתוך commits.
        2. יוצרת קובץ info עם פרטי הקומיט.
        3. מעתיקה את כל ה-staging area לתיקיית state.
        """
        commits_dir = os.path.join(wit_dir, 'commits')
        commit_path = os.path.join(commits_dir, self.id)
        state_path = os.path.join(commit_path, 'state')
        info_file = os.path.join(commit_path, 'info.txt')

        staging_area_src = os.path.join(wit_dir, 'staging_area')
        os.makedirs(commit_path, exist_ok=True)

        with open(info_file, 'w') as f:
            f.write(f"id={self.id}\n")
            f.write(f"message={self.message}\n")
            f.write(f"time={self.time}\n")

        if os.path.exists(state_path):
            shutil.rmtree(state_path)

        shutil.copytree(staging_area_src, state_path)

    @staticmethod
    def load(commit_id, wit_dir):
        """
        מקבלת ID, בודקת אם קיים בתיקיית commits.
        אם כן - קוראת את קובץ ה-info ומחזירה אובייקט Commit.
        """
        commit_path = os.path.join(wit_dir, 'commits', commit_id)
        info_file = os.path.join(commit_path, 'info.txt')

        if not os.path.exists(info_file):
            return None

        data = {}
        with open(info_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    data[key] = value

        return Commit(
            message=data.get('message'),
            commit_id=data.get('id'),
            time=data.get('time')
        )

    def __str__(self):
        return f"Commit(id={self.id}, message='{self.message}', time={self.time})"