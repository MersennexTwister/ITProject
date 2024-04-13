import sqlite3, os

conn = sqlite3.connect('instance/mars.db')
cur = conn.cursor()

cur.execute("DELETE FROM teacher")
cur.execute("DELETE FROM student")
cur.execute("DELETE FROM mark")

conn.commit()
conn.close()

os.system("rm -rf ./static/faces/* ./static/undefined_image_cache/* ./encs/* ./site_image_cache/*")
