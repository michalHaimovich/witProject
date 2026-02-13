from setuptools import setup

setup(
    name='wit',
    version='1.0',
    # כאן אנחנו רושמים את כל קבצי הפייתון שצריכים להיות מותקנים.
    # זה כולל את הקובץ הראשי (cliWit), ואת המודולים שהוא מייבא (wit, Exeptions)
    py_modules=['cliWit', 'wit', 'Exeptions'],
    install_requires=[
        'click',
        'colorama', # מומלץ להוסיף בשביל צבעים בווינדוס
    ],
    entry_points='''
        [console_scripts]
        wit=cliWit:cli
    ''',
)