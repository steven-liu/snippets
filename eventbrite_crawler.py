"""Quick script to gather events from Eventbrite's Events API.

Please set the LOCALE_DB_URL and EVENTBRITE_OAUTH_KEY in your environment."""

import logging
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

import requests

# setup some basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# verify environment is set up properly
DB_URL = os.getenv('LOCALE_DB_URL')
OAUTH_KEY = os.getenv('EVENTBRITE_OAUTH_KEY')
if not DB_URL or not OAUTH_KEY:
    logging.warning('LOCALE_DB_URL or EVENTBRITE_OAUTH_KEY not set. '
        'Please set those variables in your environment.')
    sys.exit(1)

API_URL = 'https://www.eventbriteapi.com/v3/'

# some static variables
MINIMUM_EVENT_ID = 18397574641 # created 2015-08-31T16:38:39Z
EVENTBRITE_SOURCE_ID = 1


def get_latest_event_id():
    """Get the latest event ID from the database."""
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute("""
                SELECT MAX(source_event_id) AS max_id
                FROM locale.events;
            """)
            max_id = curs.fetchone()['max_id']
    return max_id


def _get_events_paginated(since_event_id, page):
    """TODO: use batching API perhaps? or maybe gevent.

    https://www.eventbrite.com/developer/v3/reference/batching/"""

    # grab events via /events/search/ API endpoint
    resp = requests.get(API_URL + '/events/search/', params=dict(
            token=OAUTH_KEY,
            since_id=since_event_id,
            page=page,
            ))

    # handle errors coming from the API
    if resp.status_code != 200:
        logging.warning(resp.content)
        return [], False
    else:
        data = resp.json()
        has_more_pages = True if page < data['pagination']['page_count'] else False
        return data['events'], has_more_pages


def get_events(since_event_id):
    """Grab events via Eventbrite API."""

    current_page = 1
    has_more_pages = True
    while has_more_pages:
        events, has_more_pages = _get_events_paginated(since_event_id, current_page)
        for event in events:
            yield event
        current_page += 1


def write_events(events):
    """Persist events to the database."""

    for event in events:
        if not event_exists(event['id']):
            logging.debug('event %s does not exist in db.', event['id'])
            event_id = insert_event(event)
            logging.debug('event %s created! internal id %s', event['id'], event_id)


def insert_event(event):
    """Insert an Eventbrite event into the database."""

    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute("""
                INSERT INTO locale.events (
                    name, dt_start, dt_end, url, source_id, source_event_id
                ) VALUES (
                    %(name)s, %(dt_start)s, %(dt_end)s, %(url)s, %(source_id)s,
                    %(source_event_id)s
                ) RETURNING id
            """, dict(
                name=event['name']['text'],
                dt_start=event['start']['utc'],
                dt_end=event['end']['utc'],
                url=event['url'],
                source_id=EVENTBRITE_SOURCE_ID,
                source_event_id=event['id']
            ))
            event_id = curs.fetchone()
            conn.commit()
    return event_id


def event_exists(eventbrite_id):
    """Check whether a given Eventbrite event exists in the database."""

    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute("""
                SELECT 1
                FROM locale.events
                WHERE source_event_id = %s
            """, (eventbrite_id,))
            exists = curs.fetchone()
    return exists


if __name__ == '__main__':

    # get latest event that we have scraped
    since_event_id = get_latest_event_id() or MINIMUM_EVENT_ID
    logging.info('since_event_id: %s', since_event_id)

    # get more events
    events = get_events(since_event_id)

    # persist events
    write_events(events)

    # use this to debug
    #from pprint import pprint
    #pprint(events)
