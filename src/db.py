import sqlite3
from datetime import datetime, timezone
from .config import config

def connect():
    config.logger.info('connecting to sqlite db: %s' % config.DB_SQLITE_PATH)
    connection = sqlite3.connect(config.DB_SQLITE_PATH)
    migrate_schema(connection)

    return connection

def migrate_schema(connection):
    config.logger.info('migrating sqlite schema')
    connection.execute('''
        CREATE TABLE IF NOT EXISTS pet_door_events (
           timestamp, pets, event, video_file_name, frame_file_name
        )
    ''')


def insert_event(connection, event):
    config.logger.info('inserting event into db')

    connection.execute('''INSERT INTO pet_door_events VALUES (?, ?, ?, ?, ?)''', (
        event['timestamp'].astimezone(tz=timezone.utc).isoformat(),
        ','.join([str(x) for x in event['pets']]),
        event['event'],
        event['video_file_name'],
        event['frame_file_name']
    ))
    connection.commit()

def select_recent_events(connection, since):
    config.logger.info('fetching events since %s from db' % since.isoformat())

    cursor = connection.cursor()
    cursor.execute('''
        SELECT * FROM pet_door_events 
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
    ''', (since.astimezone(tz=timezone.utc).isoformat(), ))

    rows = cursor.fetchall()

    return [
        {
            'timestamp': datetime.strptime(r[0], "%Y-%m-%dT%H:%M:%S.%f"),
            'pets': [int(x) for x in r[1].split(',')],
            'event': int(r[2]),
            'video_file_name': r[3],
            'frame_file_name': r[4]
        } for r in rows
    ]