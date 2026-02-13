import filecmp
import shutil
import uuid
from Commit import Commit
import click
import os


@click.group()
def cli():
    pass


#שימוש ביחודיות של פייתון אתחול מבנה נתונים בשורה אחת!!!!!😁😁😁😁😁
def get_ignored_files(wit_dir):
    p = os.path.join(wit_dir, '.witignore')
    return {'.wit'} | ({line.strip() for line in open(p) if line.strip() and not line.strip().startswith('#')} if os.path.exists(p) else set())


@cli.command()
def init():
    path = os.getcwd()
    wit_dir = os.path.join(path, '.wit')

    if os.path.exists(wit_dir):
        click.secho(f"Here is .wit: {wit_dir}", fg='yellow')
        return

    head_file = os.path.join(wit_dir, 'HEAD')
    staging_area = os.path.join(wit_dir, 'staging_area')
    images_dir = os.path.join(wit_dir, 'images')
    witignore_file = os.path.join(wit_dir, '.witignore')

    try:
        os.makedirs(staging_area, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)

        # יצירת HEAD
        with open(head_file, 'w') as f:
            f.write("None")

        # יצירת .witignore
        with open(witignore_file, 'w') as f:
            pass

        click.secho(f"Successfully initialized .wit in: {path}", fg='green')

    except OSError as e:
        click.echo(f"An error occurred: {e}")

@cli.command()
@click.argument('path')
def add(path):
    """Adds a file or all files (.) to the staging area."""

    current_dir = os.getcwd()
    wit_dir = os.path.join(current_dir, '.wit')
    staging_area = os.path.join(wit_dir, 'staging_area')

    if not os.path.exists(wit_dir):
        click.secho("Error: Not a wit repository (run 'wit init' first)", fg='red')
        return

    # --- תוספת: טעינת רשימת ההתעלמות ---
    ignored_files = get_ignored_files(wit_dir)

    # מקרה 1: הוספת כל הקבצים (.)
    if path == ".":
        # (הערה: את בדיקת compare_directories השארתי לך כאן, אבל שים לב
        # שהיא משווה את כל התיקייה, זה עלול להיות בעייתי אם יש קבצים להתעלמות שכבר ב-staging)

        files_to_add = os.listdir(current_dir)
        count = 0
        for file_name in files_to_add:

            # --- השינוי המרכזי: בדיקה מול ה-witignore ---
            if file_name in ignored_files:
                continue
            # ---------------------------------------------

            full_path = os.path.join(current_dir, file_name)

            # תיקון קטן ללוגיקה שלך: כשמעתיקים ב-add . צריך לשמור על השם בתוך ה-staging
            # אחרת copytree ישפוך את התוכן, ו-copy2 עלול לדרוס
            dest_path = os.path.join(staging_area, file_name)

            copy_to_staging(full_path, dest_path)
            count += 1

        click.secho(f"Added {count} files to staging area.", fg='green')
    # מקרה 2: הוספת קובץ ספציפי
    else:
        # --- השינוי המרכזי: אם הקובץ ברשימת ההתעלמות - כאילו לא קיים ---
        if path in ignored_files:
            click.secho(f"Error: File '{path}' not found (ignored by .witignore).", fg='red')
            return
        # ---------------------------------------------------------------

        full_path = os.path.abspath(path)

        if not os.path.exists(full_path):
            click.secho(f"Error: File '{path}' not found.", fg='red')
            return

        staging_area_path = os.path.join(staging_area, path)

        # בדיקה אם הקובץ זהה למה שיש כבר ב-staging
        if os.path.exists(staging_area_path):
            # אם זה קובץ נשווה תוכן, אם זו תיקייה נשווה רקורסיבית
            is_same = False
            if os.path.isfile(full_path):
                is_same = filecmp.cmp(full_path, staging_area_path, shallow=False)
            elif os.path.isdir(full_path):
                is_same = compare_directories(full_path, staging_area_path)

            if is_same:
                click.secho("Error: nothing has changed", fg='yellow')
                return

        if os.path.isdir(full_path):
            # כאן אפשר להוסיף לוגיקה שאם זו תיקייה, לא להעתיק ממנה קבצים מוחרגים
            # כרגע זה מעתיק את כל התיקייה כמו שהיא
            pass

            # שים לב: בשימוש בקובץ בודד, צריך לוודא שנתיב היעד כולל את שם הקובץ
        # תיקנתי את הקריאה ל-copy_to_staging כדי שתתאים ללוגיקה
        dest_path = os.path.join(staging_area, os.path.basename(full_path))
        copy_to_staging(full_path, dest_path)

        click.secho(f"Added '{path}' to staging area.", fg='green')


def copy_to_staging(source_path, dest_path):
    """פונקציית עזר להעתקת קובץ בודד ל-staging"""
    try:
        if os.path.isdir(source_path):
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, dest_path)
    except Exception as e:
        click.secho(f"Failed to add {source_path}: {e}", fg='red')


def compare_directories(dir1, dir2, ignored_files=None):
    """
    משווה שתי תיקיות באופן רקורסיבי.
    מחזירה True רק אם המבנה, השמות, הסוגים (קובץ/תיקייה) והתוכן זהים לחלוטין.
    מתעלמת מקבצים שנמצאים ב-ignored_files.
    """
    if ignored_files is None:
        ignored_files = []

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
            if not compare_directories(path1, path2, ignored_files):
                return False

        # מקרה ב': שניהם קבצים -> השוואת תוכן (בייטים)
        else:  # אנחנו יודעים ששניהם קבצים בגלל הבדיקה למעלה
            if not filecmp.cmp(path1, path2, shallow=False):
                return False

    # אם שרדנו את כל הבדיקות - הכל זהה
    return True


@cli.command()
@click.option('-m', '--message', required=True, help='Commit message')
def commit(message):
    """Creates a new commit with a running ID."""

    path = os.getcwd()
    wit_dir = os.path.join(path, '.wit')
    head_path = os.path.join(wit_dir, 'HEAD')
    staging_area = os.path.join(wit_dir, "staging_area")

    # 1. בדיקה שה-init בוצע
    if not os.path.exists(wit_dir):
        click.secho("Error: .wit directory not found. Please run 'wit init' first.", fg='red')
        return

    with open(head_path, 'r') as f:
        current = f.readline()
    current_path = os.path.join(wit_dir, "commits", current, "state")

    if compare_directories(current_path, staging_area):
        click.secho("Error: nothing to commit", fg='red')
        return

    new_id = uuid.uuid1()

    # 3. יצירת האובייקט (בהנחה שהמחלקה Commit מיובאת או מוגדרת למעלה)
    # אנו מעבירים לו את ה-ID שחישבנו ואת ההודעה מהדגל -m
    commit_obj = Commit(commit_id=new_id, message=message)

    try:
        # 4. שמירה (יצירת התיקיות והעתקת ה-staging)
        commit_obj.save(wit_dir)

        # 5. עדכון ה-HEAD למספר החדש!
        with open(head_path, 'w') as f:
            f.write(new_id.__str__())

        click.secho(f"Commit created successfully! ID: {new_id}, Message: {message}", fg='green')

    except Exception as e:
        click.secho(f"Error creating commit: {e}", fg='red')


@cli.command()
@click.argument('commit_id')
def checkout(commit_id):
    """Restores the state of a specific commit ID."""

    path = os.getcwd()
    wit_dir = os.path.join(path, '.wit')
    staging_area = os.path.join(wit_dir, 'staging_area')

    commited_status_file = os.path.join(staging_area, '.committed')

    # ---------------------------------------------------------
    # בדיקה האם יש שינויים שלא נשמרו (false בקובץ commited)
    # ---------------------------------------------------------
    if os.path.exists(commited_status_file):
        try:
            with open(commited_status_file, 'r') as f:
                status = f.read().strip()

            # אם כתוב false - עוצרים ומתריעים
            if status == 'false':
                click.secho("Error: You have uncommitted changes in the staging area.", fg='red')
                click.secho("These files will be lost if you checkout now. Please commit first.", fg='yellow')
                return
            if compare_directories(staging_area, path):
                click.secho("Error: You have uncommitted changes ", fg='red')
                click.secho("These files will be lost if you checkout now. Please add and commit first.", fg='yellow')
                return

        except Exception as e:
            # אם לא הצלחנו לקרוא את הקובץ, אפשר להחליט אם לעצור או להמשיך.
            # כאן בחרתי להזהיר אך לא לעצור, אבל לשיקולך.
            click.secho(f"Warning: Could not read commit status: {e}", fg='yellow')


    # בדיקה שה-ID תקין
    commit_path = os.path.join(wit_dir, 'commits', commit_id)
    # נניח ששמרנו את הקבצים בתוך תיקיית state בתוך הקומיט (לפי ה-save שבנינו קודם)
    commit_state_path = os.path.join(commit_path, 'state')

    if not os.path.exists(commit_state_path):
        click.secho(f"Error: Commit ID '{commit_id}' not found.", fg='red')
        return

    # 1. טעינת רשימת ההתעלמות (כדי לדעת על מה להגן)
    ignored_files = get_ignored_files(wit_dir)

    try:
        # ---------------------------------------------------------
        # שלב א': ניקוי התיקייה הנוכחית (מחיקת קבצים שלא ב-ignore)
        # ---------------------------------------------------------
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

        click.secho(f"HEAD is now at {commit_id}", fg='green')

    except Exception as e:
        click.secho(f"Fatal error during checkout: {e}", fg='red')


if __name__ == '__main__':
    cli()


