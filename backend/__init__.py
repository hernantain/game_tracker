"""SQL-backed rewrite of the Racing Club stats API.

Reads everything from Postgres through SQLAlchemy. The legacy app in
`backend/` still reads the JSON files in data/ and is left untouched.
"""
