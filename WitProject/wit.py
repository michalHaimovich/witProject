import filecmp
import shutil
import uuid
from Commit import Commit
import ctypes
import os
import Exeptions


def _get_repo_context():
    """
    פונקציה פנימית שמכינה את כל הנתיבים ובודקת תקינות.
    מחזירה מילון עם כל הנתיבים הרלוונטיים.
    """
    base_path = os.getcwd()
    wit_dir = os.path.join(base_path, '.wit')

    # בדיקת תקינות - האם זו בכלל תיקיית wit?
    if not os.path.exists(wit_dir):
        raise Exeptions.WitRepoNotFoundError()

    # הגדרת נתיבים
    staging_area = os.path.join(wit_dir, 'staging_area')
    commits_dir = os.path.join(wit_dir, 'commits')
    head_file = os.path.join(wit_dir, 'HEAD')

    # טעינת התעלמות (התיקון מהשאלה הקודמת: הקובץ בחוץ)
    ignored_files = get_ignored_files(wit_dir)

    return base_path, wit_dir, staging_area, commits_dir, head_file, ignored_files


#שימוש ביחודיות של פייתון אתחול מבנה נתונים בשורה אחת!!!!!😁😁😁😁😁
def get_ignored_files(path):
    p = os.path.join(path, '.witignore')
    return {'.wit'} | ({line.strip() for line in open(p) if line.strip() and not line.strip().startswith('#')} if os.path.exists(p) else set())


def init(path):

    wit_dir = os.path.join(path, '.wit')

    if os.path.exists(wit_dir):
        raise Exeptions.WitAlreadyExistsError()

    head_file = os.path.join(wit_dir, 'HEAD')
    staging_area = os.path.join(wit_dir, 'staging_area')
    images_dir = os.path.join(wit_dir, 'commits')
    witignore_file = os.path.join(path, '.witignore')

    os.makedirs(staging_area, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    if os.name == 'nt':  # בדיקה אם רצים על Windows
        file_attribute_hidden = 0x02
        try:
            # שימוש ב-Windows API כדי להפוך את התיקייה למוסתרת
            ret = ctypes.windll.kernel32.SetFileAttributesW(wit_dir, file_attribute_hidden)
            if not ret:
                print("Warning: Could not set hidden attribute on .wit directory.")
        except Exception:
            print("Warning: Could not access Windows API to hide directory.")

    # יצירת HEAD
    with open(head_file, 'w') as f:
        f.write("None")

     # יצירת .witignore
    with open(witignore_file, 'w') as f:
        pass


def add(path):
    """Adds a file or all files (.) to the staging area."""
    current_dir, wit_dir, staging_area, _, _, ignored_files = _get_repo_context

    # מקרה 1: הוספת כל הקבצים (.)
    if path == ".":
        # (הערה: את בדיקת compare_directories השארתי לך כאן, אבל שים לב
        # שהיא משווה את כל התיקייה, זה עלול להיות בעייתי אם יש קבצים להתעלמות שכבר ב-staging)

        files_to_add = os.listdir(current_dir)

        for file_name in files_to_add:

            # --- השינוי המרכזי: בדיקה מול ה-witignore ---
            if file_name in ignored_files:
                continue

            full_path = os.path.join(current_dir, file_name)

            # תיקון קטן ללוגיקה שלך: כשמעתיקים ב-add . צריך לשמור על השם בתוך ה-staging
            # אחרת copytree ישפוך את התוכן, ו-copy2 עלול לדרוס
            dest_path = os.path.join(staging_area, file_name)

            copy_to_staging(full_path, dest_path)

    # מקרה 2: הוספת קובץ ספציפי
    else:
        # --- השינוי המרכזי: אם הקובץ ברשימת ההתעלמות - כאילו לא קיים ---
        if path in ignored_files:
            raise FileNotFoundError()
        # ---------------------------------------------------------------

        full_path = os.path.abspath(path)

        if not os.path.exists(full_path):
            raise FileNotFoundError()

        staging_area_path = os.path.join(staging_area, path)

        # בדיקה אם הקובץ זהה למה שיש כבר ב-staging
        if os.path.exists(staging_area_path):
            # אם זה קובץ נשווה תוכן, אם זו תיקייה נשווה רקורסיבית
            is_same = False
            if os.path.isfile(full_path):
                is_same = filecmp.cmp(full_path, staging_area_path, shallow=False)
            elif os.path.isdir(full_path):
                is_same = compare_directories(full_path, staging_area_path, wit_dir)

            if is_same:
                raise Exeptions.WitNoChangesError()

        if os.path.isdir(full_path):
            # כאן אפשר להוסיף לוגיקה שאם זו תיקייה, לא להעתיק ממנה קבצים מוחרגים
            # כרגע זה מעתיק את כל התיקייה כמו שהיא
            pass

            # שים לב: בשימוש בקובץ בודד, צריך לוודא שנתיב היעד כולל את שם הקובץ
        # תיקנתי את הקריאה ל-copy_to_staging כדי שתתאים ללוגיקה
        dest_path = os.path.join(staging_area, os.path.basename(full_path))
        copy_to_staging(full_path, dest_path)


def copy_to_staging(source_path, dest_path):
    """פונקציית עזר להעתקת קובץ בודד ל-staging"""

    if os.path.isdir(source_path):
        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
    else:
        shutil.copy2(source_path, dest_path)


def compare_directories(dir1, dir2, path):
    """
    משווה שתי תיקיות באופן רקורסיבי.
    מחזירה True רק אם המבנה, השמות, הסוגים (קובץ/תיקייה) והתוכן זהים לחלוטין.
    מתעלמת מקבצים שנמצאים ב-ignored_files.
    """
    ignored_files = get_ignored_files(path)

    # 1. בדיקת קיום בסיסית
    if not os.path.exists(dir1) or not os.path.exists(dir2):
        return False

    try:
        # קבלת רשימת הפריטים הגולמית
        raw_dir1 = os.listdir(dir1)
        raw_dir2 = os.listdir(dir2)

        # סינון: מסננים החוצה קבצים שברשימת ההתעלמות וגם את תיקיית .wit
        # הערה: ההנחה היא ש-ignored_files מכיל שמות קבצים או נתיבים יחסיים
        items1 = sorted([f for f in raw_dir1 if f not in ignored_files and f != '.wit'])
        items2 = sorted([f for f in raw_dir2 if f not in ignored_files and f != '.wit'])

    except OSError:
        return False

    # 2. בדיקת מבנה: אם רשימת השמות שונה (אורך שונה או שמות שונים) -> לא זהה
    # זה מטפל במקרה של קובץ שנמצא במיקום אחד ובמיקום אחר לא
    if items1 != items2:
        return False

    # 3. לולאה על הפריטים (כעת אנו יודעים שהשמות זהים בשני הצדדים)
    for item in items1:
        path1 = os.path.join(dir1, item)
        path2 = os.path.join(dir2, item)

        # --- הבדיקה שהוספנו לבקשתך ---
        # בדיקת סוג: האם אחד הוא קובץ והשני תיקייה?
        # אם יש אי-התאמה בסוג הפריט -> התיקיות שונות
        if os.path.isdir(path1) != os.path.isdir(path2):
            return False
        # -----------------------------

        # מקרה א': שניהם תיקיות -> קריאה רקורסיבית
        if os.path.isdir(path1):
            if not compare_directories(path1, path2, path):
                return False

        # מקרה ב': שניהם קבצים -> השוואת תוכן (בייטים)
        else:  # אנחנו יודעים ששניהם קבצים בגלל הבדיקה למעלה
            if not filecmp.cmp(path1, path2, shallow=False):
                return False

    # אם שרדנו את כל הבדיקות - הכל זהה
    return True



def commit(message):
    """Creates a new commit with a running ID."""
    path, wit_dir, staging_area,  _, head_path, ignored_files = _get_repo_context

    with open(head_path, 'r') as f:
        current = f.readline()
    if current != "None":
        current_path = os.path.join(wit_dir, "commits", current, "state")

        if compare_directories(current_path, staging_area, wit_dir):
            raise Exeptions.WitNoChangesError()

    else:
        if not os.listdir(staging_area):
            raise Exeptions.WitNoChangesError()

    new_id = uuid.uuid1()

    # 3. יצירת האובייקט (בהנחה שהמחלקה Commit מיובאת או מוגדרת למעלה)
    # אנו מעבירים לו את ה-ID שחישבנו ואת ההודעה מהדגל -m
    commit_obj = Commit(commit_id=new_id, message=message)

    commit_obj.save(wit_dir)

    with open(head_path, 'w') as f:
        f.write(new_id.__str__())

    return new_id


def checkout(commit_id):
    """Restores the state of a specific commit ID."""
    path, wit_dir, staging_area, _, head_path, ignored_files = _get_repo_context

    commit_path = os.path.join(wit_dir, 'commits', commit_id)
    commit_state_path = os.path.join(commit_path, 'state')

    if not os.path.exists(commit_state_path):
       raise Exeptions.WitReferenceNotFoundError()

    with open(head_path, 'r') as f:
        current = f.readline()
    current_path = os.path.join(wit_dir, "commits", current, "state")

    if not compare_directories(current_path, path, wit_dir):
        raise Exeptions.WitUncommittedChangesError()

    for item in os.listdir(path):
        # הגנה על קבצים מוחרגים ועל תיקיית .wit עצמה
        if item in ignored_files:
            continue

        full_path = os.path.join(path, item)

        # מחיקה בטוחה (בין אם זה קובץ או תיקייה)
        if os.path.isfile(full_path) or os.path.islink(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)

    # ---------------------------------------------------------
    # שלב ב': העתקת הקבצים מה-Commit לתיקייה הנוכחית
    # ---------------------------------------------------------
    # הפונקציה copytree עם dirs_exist_ok=True מעתיקה ודורסת אם צריך
    shutil.copytree(commit_state_path, path, dirs_exist_ok=True)

    # ---------------------------------------------------------
    # שלב ג': עדכון ה-Staging Area וה-HEAD
    # ---------------------------------------------------------
    # ה-staging צריך להיות עכשיו זהה בדיוק למה שעשינו לו checkout
    if os.path.exists(staging_area):
        shutil.rmtree(staging_area)
    shutil.copytree(commit_state_path, staging_area)

    # עדכון ה-HEAD שיצביע על הקומיט הנוכחי
    head_file = os.path.join(wit_dir, 'HEAD')
    with open(head_file, 'w') as f:
        f.write(commit_id)


def status():
    """
    מדפיסה את הסטטוס הנוכחי של המערכת:
    1. קבצים ב-Staging ששונים מה-HEAD (ירוק).
    2. קבצים לא מעוקבים (Untracked) (אדום).
    3. קבצים ששונו בתיקייה אבל לא ב-Staging (אדום).
    """
    base_path, wit_dir, staging_area, _, head_file, ignored_files = _get_repo_context

    # מציאת התיקייה של הקומיט האחרון (HEAD)

    with open(head_file, 'r') as f:
        commit_id = f.read().strip()
        last_commit_dir = os.path.join(wit_dir, 'commits', commit_id, "state")

    # -----------------------------------------------------------
    # חלק 1: השוואה בין Staging Area לבין HEAD (קבצים שמוכנים לקומיט)
    # -----------------------------------------------------------
    changes_to_be_committed = []

    # עוברים על כל הקבצים ב-staging area
    for root, dirs, files in os.walk(staging_area):
        for file in files:
            full_path = os.path.join(root, file)
            # מציאת הנתיב היחסי (כדי לדעת איפה לחפש ב-HEAD)
            rel_path = os.path.relpath(full_path, staging_area)

            # אם אין עדיין HEAD (קומיט ראשון) - הכל נחשב חדש
            if not os.path.exists(last_commit_dir):
                changes_to_be_committed.append(rel_path)
            else:
                path_in_head = os.path.join(last_commit_dir, rel_path)

                # אם הקובץ לא קיים ב-HEAD או שהתוכן שלו שונה
                if not os.path.exists(path_in_head):
                    changes_to_be_committed.append(rel_path)
                else:
                    # שימוש באותה לוגיקה של compare_directories
                    if not filecmp.cmp(full_path, path_in_head, shallow=False):
                        changes_to_be_committed.append(rel_path)

    # -----------------------------------------------------------
    # חלק 2 + 3: השוואה בין התיקייה הנוכחית לבין Staging Area
    # -----------------------------------------------------------
    untracked_files = []  # קבצים שלא קיימים ב-staging
    modified_not_staged = []  # קבצים שקיימים ב-staging אך שונים בתוכן

    for root, dirs, files in os.walk(base_path):
        # התעלמות מתיקיית .wit עצמה
        if '.wit' in dirs:
            dirs.remove('.wit')

        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_path)

            # בדיקה אם הקובץ ברשימת ההתעלמות
            if rel_path in ignored_files or file in ignored_files:
                continue

            path_in_staging = os.path.join(staging_area, rel_path)

            # מקרה 2: Untracked files
            # הקובץ קיים בתיקייה אך לא ב-staging
            if not os.path.exists(path_in_staging):
                untracked_files.append(rel_path)

            # מקרה 3: Modified files
            # הקובץ קיים ב-staging, בודקים אם התוכן זהה
            else:
                # שימוש ב-filecmp (כמו בפונקציה הקודמת)
                if not filecmp.cmp(full_path, path_in_staging, shallow=False):
                    modified_not_staged.append(rel_path)

    # -----------------------------------------------------------
    # הדפסה (תצוגה)
    # -----------------------------------------------------------

    return commit_id, changes_to_be_committed, untracked_files, modified_not_staged






