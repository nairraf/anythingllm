from datetime import datetime
import hashlib
import json
import re
import sqlite3
import textwrap
from urllib.parse import urlparse

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
    
    def insert_site(self, base_url: str, parent_element: str, child_element: str, name: str) -> None:
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

    def set_site_config(self, url: str) -> None:
        """
        retrieves the site configuration for the requested URL
        will only re-query SQL if the base_url is different than the current self:site_base_url
        """
        api_url = urlparse(url)
        base_url = api_url.netloc
        #print(f"setting base_url to: {base_url}")
        if self.site_base_url is not None or self.site_base_url != base_url:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                        SELECT site_id, base_url, parent_element, child_element, name 
                        FROM sites
                        WHERE base_url = ?;
                    """, (base_url,)
                )
                results = cursor.fetchone()
                #print(f"retrieved base_url for site: {results['name']}")
                if results:
                    self.site_id = results["site_id"]
                    self.site_base_url = base_url
                    self.site_parent_element = results['parent_element']
                    self.site_child_element = results['child_element']
                    self.site_name = results['name']
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

    def content_hash(self, content: str) -> str:
        encoded = content.encode('utf-8')
        return (hashlib.sha256(encoded)).hexdigest()
    
    def generate_title(self, raw_title, suffix=None):
        # Remove special characters, replace spaces/dashes with underscores
        title = re.sub(r'[^A-Za-z0-9 ]+', '', raw_title)
        title = re.sub(r'\s+', '_', title.strip())
        if suffix:
            title = f"{title}_{suffix}"
        return title


    def insert_new_page(
            self, 
            normalized_url: str, 
            original_url: str, 
            title: str = "",
            status: str = "new",
            job: str = "", 
            tags: list = [],
            workspaces: str = "",
            image_urls: list = []) -> None:
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
                self.generate_title(title),
                status,
                job,
                json.dumps(tags),
                workspaces,
                sqlite_datetime_str,
                json.dumps(image_urls)
            )
            self.cursor.execute(
                """
                    INSERT INTO pages 
                    (site_id, normalized_url, original_url, title, status, job, tags, workspaces, last_update, image_urls) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (normalized_url) DO UPDATE SET
                        title = excluded.title,
                        job = excluded.job,
                        tags = excluded.tags,
                        workspaces = excluded.workspaces,
                        last_update = excluded.last_update,
                        image_urls = excluded.image_urls
                """, parameters
            )
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"database error: {e}")
    
    def update_page(self, page_id: int, content: str, status: str = "complete") -> None:
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
                    SET content=?, content_hash=?, status=?, last_update=?
                    WHERE page_id=?;
                """, parameters
            )
            # we have to commit since it's a seperate cursor
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"database error: {e}")
            return None
    
    def get_pages_count(self, status: str = None, job: str = None) -> int:
        """
        returns the count for all pages mathing job (or all jobs).
        """
        where_clauses = []
        parameters = []

        try:
            if status is not None and len(status) > 0:
                where_clauses.append("status = ?")
                parameters.append(status)

            if job is not None and len(job) > 0:
                where_clauses.append("job = ?")
                parameters.append(job)
            
            sql_where = ""
            if where_clauses:
                sql_where = "WHERE " + " AND ".join(where_clauses)

            self.cursor.execute(
                f"""
                    SELECT count(*) as 'count'
                    FROM pages
                    {sql_where}
                """, parameters
            )
            results = self.cursor.fetchone()
            if results:
                return results['count']
            return 0
        except sqlite3.Error as e:
            print(f"database error: {e}")
            return None

    def get_pages(self, status: str = None, job: str = None) -> sqlite3.Cursor:
        """
        returns an iterable cursor object that can loop through all rows. this saves loading the whole dataset in memory
        """

        where_clauses = []
        parameters = []

        try:
            if status is not None and len(status) > 0:
                where_clauses.append("status = ?")
                parameters.append(status)

            if job is not None and len(job) > 0:
                where_clauses.append("job = ?")
                parameters.append(job)
            
            sql_where = ""
            if where_clauses:
                sql_where = "WHERE " + " AND ".join(where_clauses)

            self.cursor.execute(
                f"""
                    SELECT page_id, normalized_url, original_url, title, content, content_hash, uploaded_hash, status, job, tags, workspaces, last_update
                    FROM pages
                    {sql_where}
                    ORDER BY normalized_url
                """, parameters
            )
            return self.cursor
        except sqlite3.Error as e:
            print(f"database error: {e}")
            return None
   
    def get_jobs(self) -> list[str]:
        """
        returns a basic python list for all unique jobs names present in the database
        """

        parameters = []

        try:
            self.cursor.execute(
                f"""
                   select DISTINCT(job) from pages;
                """, parameters
            )
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"database error: {e}")
            return None
        
    def get_jobs_runtime(self):
        """
        returns a basic python list for all jobs and their last runtime
        """

        parameters = []

        try:
            self.cursor.execute(
                f"""
                   SELECT job, MAX(last_update) as last_update 
                   FROM pages 
                   GROUP BY job;
                """, parameters
            )
            return [
                {"job": row["job"], "last_update": row["last_update"]}
                for row in self.cursor.fetchall()
            ]
        except sqlite3.Error as e:
            print(f"database error: {e}")
            return None
        
    def update_uploaded_page(self, page_id: int, status: str, uploaded_hash: str) -> None:
        """
        set the complete flag for a specific page_id
        uses a seperate cursor to not interfere with any other DB operations
        """
        try:
            cursor = self.conn.cursor()
            parameters = (
                status,
                uploaded_hash,
                page_id,
            )
            cursor.execute(
                """
                    UPDATE pages
                    SET status=?, uploaded_hash=?
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
        
    def insert_file(self, uploaded_hash, anythingllm_folder, anythingllm_file_name, original_file_name, status):
        """
        updates the file table with the purpose of tracking anythingllm uploads
        right now this requires git repositories to ensure file unique naming
        uses a seperate cursor to ensure it doesn't break any other cursor
        """
        try:
            cursor = self.conn.cursor()

            now = datetime.now()
            sqlite_datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')

            parameters = (
                uploaded_hash,
                anythingllm_folder,
                anythingllm_file_name,
                original_file_name,
                status,
                sqlite_datetime_str,
            )
            cursor.execute(
                """
                    INSERT INTO files 
                    (uploaded_hash, anythingllm_folder, anythingllm_file_name, original_file_name, status, last_update) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (anythingllm_folder, anythingllm_file_name) DO UPDATE SET
                        uploaded_hash = excluded.uploaded_hash,
                        original_file_name = excluded.original_file_name,
                        status = excluded.status,
                        last_update = excluded.last_update
                """, parameters
            )
            # since this is a seperate operation, it will be lost when the cursor closes/method exists, so we force a commit
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"database error: {e}")
            self.conn.rollback()
            return None
        
    def get_file(self, anythingllm_folder, anythingllm_file_name):
        """
        returns the columns for an anythingllm file to detect file content changes
        uses a seperate cursor to ensure it doesn't break any other cursor
        """
        
        parameters = [
            anythingllm_folder,
            anythingllm_file_name
        ]

        try:
            self.cursor.execute(
                f"""
                   SELECT uploaded_hash, original_file_name, status, last_update 
                   FROM files
                   WHERE anythingllm_folder = ? AND anythingllm_file_name = ?
                """, parameters
            )
            
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"database error: {e}")
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