from datetime import datetime
import hashlib
import sqlite3
import textwrap

class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.site_id = None
        self.site_base_url = None
        self.site_parent_element = None
        self.site_child_element = None
        self.site_name = None
        self._site_config_set = False
        try:
            self.conn = sqlite3.connect(db_file)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"database error: {e}")
    
    @property
    def site_config_set(self):
        return self._site_config_set
    
    def insert_site(self, base_url, parent_element, child_element, name):
        """Inserts a single site into the sites table"""
        try:
            
            self.cursor.execute("INSERT INTO sites (base_url, parent_element, child_element, name) VALUES (?, ?, ?, ?)", (base_url, parent_element, child_element, name))
        except sqlite3.IntegrityError:
            print(f"an entry for site: {name} already exists - skipping")

    def set_site_config(self, base_url):
        try:
            self.cursor.execute("SELECT site_id, base_url, parent_element, child_element, name FROM sites;")
            results = self.cursor.fetchall()
            if results and len(results) == 1:
                self.site_id = results[0]["site_id"]
                self.site_base_url = results[0]['base_url']
                self.site_parent_element = results[0]['parent_element']
                self.site_child_element = results[0]['child_element']
                self.site_name = results[0]['name']
                self._site_config_set = True
                return True
            else:
                return False 
        except sqlite3.Error as e:
            print(f"database error: {e}")

    def set_foreign_keys(self, state):
        state = state.lower()
        if state == "on":
            self.cursor.execute("PRAGMA foreign_keys = ON;")
        elif state == "off":
            self.cursor.execute("PRAGMA foreign_keys = OFF;")
    
    
    def print_site_config(self):
        site_config = f"""
            Here is the currently selected site:
                        
            name: {self.site_name}
            base_url: {self.site_base_url}
            parent_element: {self.site_parent_element}
            parent_element: {self.site_child_element}
            ID: {self.site_id}
        """
        print(textwrap.dedent(site_config))

    def content_hash(self, content):
        encoded = content.encode('utf-8')
        return (hashlib.sha256(encoded)).hexdigest()

    def insert_page(self, url, content="", status="new", category="mslearn", workspaces="selos-main, selos-development, selos-experiments"):
        """Inserts a page into the pages table"""
        if self._site_config_set == False:
            return print("You must set the site config before attempting to insert a page!")
        
        try:
            now = datetime.now()
            sqlite_datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')
            content_hash = self.content_hash(content)
            parameters = (
                self.site_id,
                url,
                content,
                content_hash,
                status,
                category,
                workspaces,
                sqlite_datetime_str
            )
            self.cursor.execute(
                """
                    INSERT INTO pages 
                    (site_id, url, content, content_hash, status, category, workspaces, last_update) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (url) DO UPDATE SET
                        content = excluded.content,
                        content_hash = excluded.content_hash,
                        status = excluded.status,
                        category = excluded.category,
                        workspaces = excluded.workspaces,
                        last_update = excluded.last_update
                    WHERE content_hash != excluded.content_hash
                """, parameters
            )
        except sqlite3.Error as e:
            print(f"database error: {e}")
    
    def get_pages(self, status="new"):
        """returns an iterable cursor object that can loop through all rows. this saves loading the whole dataset in memory"""
        try:
            self.cursor.execute(
                """
                    SELECT page_id, url, content, status, category, workspaces, last_update
                    FROM pages
                    WHERE
                        status = ?
                """, (status)
            )
            return self.cursor
        except sqlite3.Error as e:
            print(f"database error: {e}")

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
        print("Database connection closed.")