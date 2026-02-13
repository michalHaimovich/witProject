from setuptools import setup

setup(
    name='wit',
    version='1.0',
    py_modules=['wit'],  # השם של קובץ הפייתון שלך (בלי .py)
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        wit=wit:cli
    ''',
)