class WitError(Exception):
    """Base class for exceptions in this module."""
    pass


# --- שגיאה 1: אין תיקיית wit ---
class WitRepoNotFoundError(WitError):
    def __init__(self):

        super().__init__("Error: Not a wit repository (run 'wit init' first)")


# --- שגיאה 2: שינויים לא שמורים ב-staging ---
class WitUncommittedChangesError(WitError):
    def __init__(self):
        super().__init__("Error: You have uncommitted changes in the staging area. Please commit or stash them.")


# --- שגיאה 3: הפניה לא נמצאה (Commit ID שגוי) ---
class WitReferenceNotFoundError(WitError):
    def __init__(self):
        super().__init__("Error: The specified commit ID or branch does not exist.")


class WitAlreadyExistsError(WitError):
    def __init__(self):
        super().__init__("Error: repo already exist in this directory.")


class WitNoChangesError(WitError):
    def __init__(self):
        super().__init__("Error: there are no changes from the last commit.")
