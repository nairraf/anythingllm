from datetime import datetime
import hashlib
import json
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
        """
        Inserts a single site into the sites table
        """
        try:
            parameters = (
                base_url,
                parent_element,
                child_element,
                name
            )
            self.cursor.execute(
                """
                    INSERT INTO sites (base_url, parent_element, child_element, name)
                    VALUES (?, ?, ?, ?)
                """, parameters
            )
        except sqlite3.IntegrityError:
            self.conn.rollback()
            print(f"an entry for site: {name} already exists - skipping")

    def set_site_config(self, base_url):
        try:
            self.cursor.execute(
                """
                    SELECT site_id, base_url, parent_element, child_element, name 
                    FROM sites
                    WHERE base_url = ?;
                """, (base_url,)
            )
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
                raise ValueError(f"Invalid Site Configuration: base_url: {base_url} not found")
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

    def insert_new_page(self, normalized_url, original_url, title="", status="new", job="", tags=[], workspaces=""):
        """
        Inserts a page into the pages table
        """
        if self._site_config_set == False:
            print("You must set the site config before attempting to insert a page!")
            raise ValueError("Site Config Not Set")
        
        try:
            now = datetime.now()
            sqlite_datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')

            parameters = (
                self.site_id,
                normalized_url,
                original_url,
                title,
                status,
                job,
                json.dumps(tags),
                workspaces,
                sqlite_datetime_str
            )
            self.cursor.execute(
                """
                    INSERT INTO pages 
                    (site_id, normalized_url, original_url, title, status, job, tags, workspaces, last_update) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (normalized_url) DO UPDATE SET
                        title = excluded.title,
                        job = excluded.job,
                        tags = excluded.tags,
                        workspaces = excluded.workspaces,
                        last_update = excluded.last_update
                """, parameters
            )
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"database error: {e}")
    
    def update_page(self, page_id, content, status="complete"):
        """
        Updates a page into the pages table
        uses a seperate cursor to not interfere with any other DB operations
        """
        try:
            now = datetime.now()
            sqlite_datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')
            content_hash = self.content_hash(content)
            
            parameters = (
                content,
                content_hash,
                status,
                sqlite_datetime_str,
                page_id
            )
            cursor = self.conn.cursor()
            cursor.execute(
                """
                    UPDATE pages
                    SET content=?, content_hash=?, status=?, last_update=''
                    WHERE page_id=? and content_hash != excluded.content_hash;
                """, parameters
            )
            # we have to commit since it's a seperate cursor
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"database error: {e}")
            return None

    def get_pages(self, status="new"):
        """returns an iterable cursor object that can loop through all rows. this saves loading the whole dataset in memory"""
        try:
            parameters = (
                status,
            )
            self.cursor.execute(
                """
                    SELECT page_id, normalized_url, original_url, title, content, status, job, tags, workspaces, last_update
                    FROM pages
                    WHERE
                        status = ?
                    ORDER BY normalized_url
                """, parameters
            )
            return self.cursor
        except sqlite3.Error as e:
            print(f"database error: {e}")
            return None
        
    def update_page_status(self, page_id, status="complete"):
        """
        set the complete flag for a specific page_id
        uses a seperate cursor to not interfere with any other DB operations
        """
        try:
            cursor = self.conn.cursor()
            parameters = (
                status,
                page_id,
            )
            cursor.execute(
                """
                    UPDATE pages
                    SET status=?
                    WHERE page_id=?;
                """, parameters
            )
            # since this is a seperate operation, it will be lost when the cursor closes/method exists, so we force a commit
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"database error: {e}")
            self.conn.rollback()
            return None

    def commit(self) -> bool:
        try:
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"database error: {e}")
            return False
        
    def rollback(self) -> bool:
        try:
            self.conn.rollback()
            return True
        except sqlite3.Error as e:
            print(f"database error: {e}")
            return False

    def close(self):
        self.conn.close()