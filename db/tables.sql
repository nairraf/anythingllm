CREATE TABLE sites (
	site_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	base_url TEXT,
	parent_element TEXT,
	child_element TEXT,
	name TEXT,
	UNIQUE (base_url)
);

CREATE TABLE pages (
	page_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	site_id INTEGER NOT NULL,
	normalized_url TEXT,
	original_url TEXT,
	title TEXT,
	content TEXT,
    content_hash TEXT,
	status TEXT,
	job TEXT,
	tags TEXT,
	workspaces TEXT, 
	last_update DATETIME,
	UNIQUE(normalized_url)
	CONSTRAINT pages_sites_FK FOREIGN KEY (site_id) REFERENCES sites(site_id)
);