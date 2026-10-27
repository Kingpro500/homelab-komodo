import json, os, time, uuid, re, requests

BASE = 'https://matrix.lan.local'
API = 'http://127.0.0.1:8008'
USER = '@hermes-ai:matrix.lan.local'
ROOM = '!nXviuMwcYbixRsYB8uQcE7PlXGm7O04X5xjoCRbxTXY'
TOKEN_PATH = '/opt/synapse/.hermes_ai_token'
HA_TOKEN_PATH = '/opt/synapse/.hass_token'
OLLAMA_URL = 'http://10.0.0.133:11434/api/chat'

# Runtime secrets remain on CT180 and are never committed.
TOKEN = open(TOKEN_PATH).read().strip()
HA_TOKEN = open(HA_TOKEN_PATH).read().strip()
H = {'Authorization': f'Bearer {TOKEN}'}
HA_H = {'Authorization': f'Bearer {HA_TOKEN}', 'Content-Type': 'application/json'}

ARC = 'media_player.stue_arc_sonos'
LIGHT = 'light.stue'
SINCE_PATH = '/opt/synapse/.hermes_ai_since'


def ha_state(entity):
    r = requests.get(f'http://10.0.0.7:8123/api/states/{entity}', headers=HA_H, timeout=5)
    r.raise_for_status()
    return r.json()


def ha_call(domain, service, data):
    r = requests.post(f'http://10.0.0.7:8123/api/services/{domain}/{service}', headers=HA_H, json=data, timeout=10)
    r.raise_for_status()
    return r.json()


def sonos_status():
    s = ha_state(ARC)
    a = s.get('attributes', {})
    volume = round(float(a.get('volume_level', 0)) * 100)
    title = a.get('media_title') or a.get('source') or 'ukjent'
    return f'Sonos Arc: {s.get("state")}, volum {volume} prosent, kilde {title}.'


def light_state():
    return ha_state(LIGHT)


def light_answer(text):
    if not any(x in text for x in ('lys', 'lyset', 'lampe')):
        return None
    if 'stue' not in text and 'lys' not in text:
        return None
    if any(x in text for x in ('på', 'skru på', 'slå på')):
        ha_call('light', 'turn_on', {'entity_id': LIGHT})
        return 'Stuelampen er slått på.' if light_state().get('state') == 'on' else 'Jeg fikk ikke bekreftet at stuelampen ble slått på.'
    if any(x in text for x in ('av', 'skru av', 'slå av')):
        ha_call('light', 'turn_off', {'entity_id': LIGHT})
        return 'Stuelampen er slått av.' if light_state().get('state') == 'off' else 'Jeg fikk ikke bekreftet at stuelampen ble slått av.'
    match = re.search(r'(?:lys|lysstyrke|styrke).*?(\d{1,3})\s*(?:%|prosent)', text)
    if match:
        pct = max(1, min(100, int(match.group(1))))
        ha_call('light', 'turn_on', {'entity_id': LIGHT, 'brightness_pct': pct})
        state = light_state()
        brightness = state.get('attributes', {}).get('brightness')
        actual = round(float(brightness) / 255 * 100) if brightness is not None else pct
        return f'Stuelampen er satt til {actual} prosent lysstyrke.'
    if 'status' in text or 'lyset' in text:
        state = light_state()
        brightness = state.get('attributes', {}).get('brightness')
        pct = round(float(brightness) / 255 * 100) if brightness is not None else None
        suffix = f' med {pct} prosent lysstyrke.' if pct is not None else '.'
        return f'Stuelampen er {"på" if state.get("state") == "on" else "av"}{suffix}'
    return None


def answer(text):
    text = text.lower().strip()
    reply = light_answer(text)
    if reply is not None:
        return reply

    if 'arc' in text or 'sonos' in text or text.startswith('sett '):
        match = re.search(r'(?:volum|lyd|lydnivå|arc|sonos)(?:[^0-9]*?)(\d{1,3})\s*(?:%|prosent)?', text)
        if match and any(x in text for x in ('sett', 'volum', 'lyd', 'lydnivå')):
            value = max(0, min(100, int(match.group(1)))) / 100
            ha_call('media_player', 'volume_set', {'entity_id': ARC, 'volume_level': value})
            actual = ha_state(ARC).get('attributes', {}).get('volume_level')
            return f'Sonos Arc-volum satt til {round(float(actual) * 100) if actual is not None else int(value * 100)} prosent.'

    if 'arc' in text or 'sonos' in text:
        if any(x in text for x in ('pause', 'stopp', 'stoppe', 'lyd av', 'stopp lyden')):
            ha_call('media_player', 'media_pause', {'entity_id': ARC})
            return 'Sonos Arc er satt på pause.'
        if any(x in text for x in ('play', 'start', 'fortsett', 'spill', 'spille')):
            ha_call('media_player', 'media_play', {'entity_id': ARC})
            return 'Sonos Arc spiller videre.'
        if 'neste' in text or 'next' in text:
            ha_call('media_player', 'media_next_track', {'entity_id': ARC})
            return 'Sonos Arc hopper til neste spor.'
        if 'forrige' in text or 'previous' in text:
            ha_call('media_player', 'media_previous_track', {'entity_id': ARC})
            return 'Sonos Arc går til forrige spor.'
        if 'mute' in text or 'demp' in text:
            ha_call('media_player', 'volume_mute', {'entity_id': ARC, 'is_volume_muted': True})
            return 'Sonos Arc er dempet.'
        if any(x in text for x in ('lyd på', 'unmute', 'ikke demp', 'slå på lyden')):
            ha_call('media_player', 'volume_mute', {'entity_id': ARC, 'is_volume_muted': False})
            return 'Sonos Arc er ikke lenger dempet.'
        if any(x in text for x in ('radio', 'tv', 'kilde', 'source')):
            match = re.search(r'(?:til|kilde|source)\s+["“]?(.+?)["”]?\s*$', text)
            sources = ha_state(ARC).get('attributes', {}).get('source_list', [])
            if match:
                wanted = match.group(1).strip()
                source = next((x for x in sources if x.lower() == wanted.lower()), None)
                if source:
                    ha_call('media_player', 'select_source', {'entity_id': ARC, 'source': source})
                    actual = ha_state(ARC).get('attributes', {}).get('source', source)
                    return f'Sonos Arc-kilde satt til {actual}.'
                return 'Jeg finner ikke den kilden på Sonos Arc. Tilgjengelige kilder: ' + ', '.join(sources) + '.'
        if any(x in text for x in ('status', 'hva spilles', 'spiller')):
            return sonos_status()
        match = re.search(r'(?:volum|lyd|lydnivå)(?:[^0-9]*?)(\d{1,3})\s*(?:%|prosent)?', text)
        if match:
            value = max(0, min(100, int(match.group(1)))) / 100
            ha_call('media_player', 'volume_set', {'entity_id': ARC, 'volume_level': value})
            actual = ha_state(ARC).get('attributes', {}).get('volume_level')
            return f'Sonos Arc-volum satt til {round(float(actual) * 100) if actual is not None else int(value * 100)} prosent.'

    query = text
    if 'pc1' in query and any(x in query for x in ('strøm', 'watt', 'power', 'forbruk')):
        try:
            state = ha_state('sensor.pc1_ai_power')
            unit = state.get('attributes', {}).get('unit_of_measurement', 'W')
            return f'PC1 bruker akkurat nå {state.get("state")} {unit}.'
        except Exception:
            return 'Jeg fikk ikke lest PC1-strømmen fra Home Assistant.'
    if any(x in query for x in ('stue', 'stuen')) and any(x in query for x in ('varm', 'temperatur', 'grader')):
        try:
            state = ha_state('sensor.stue_2_temperatur')
            unit = state.get('attributes', {}).get('unit_of_measurement', '°C')
            return f'Det er {state.get("state")} {unit} i stuen.'
        except Exception:
            return 'Jeg fikk ikke lest stuetemperaturen fra Home Assistant.'
    if 'pc1' in query and any(x in query for x in ('temperatur', 'temp', 'gpu', 'varm')):
        return 'PC1-temperatur er ikke tilgjengelig akkurat nå. PC1 brukes til gaming, og temperaturmålingen er ikke eksponert i Home Assistant.'

    response = requests.post(OLLAMA_URL, json={
        'model': 'qwen3:8b',
        'messages': [
            {'role': 'system', 'content': 'Du er Hermes AI i Matrix-rommet Hermes AI. Svar kort og konkret på norsk. Du har ikke tilgang til Home Assistant eller systemverktøy.'},
            {'role': 'user', 'content': text},
        ],
        'stream': False,
        'think': False,
        'options': {'temperature': 0.2, 'num_predict': 500},
    }, timeout=3)
    response.raise_for_status()
    data = response.json()
    return (data.get('message', {}).get('content') or data.get('message', {}).get('thinking') or 'Jeg fikk ikke et svar fra modellen.').strip()


def send(body):
    txn = str(uuid.uuid4())
    url = f'{API}/_matrix/client/v3/rooms/{ROOM}/send/m.room.message/{txn}'
    response = requests.put(url, headers={**H, 'Content-Type': 'application/json'}, json={'msgtype': 'm.text', 'body': body}, timeout=20)
    response.raise_for_status()


def poll():
    since = None
    seen = set()
    while True:
        try:
            params = {'timeout': 30000}
            if since:
                params['since'] = since
            response = requests.get(f'{API}/_matrix/client/v3/sync', headers=H, params=params, timeout=40)
            response.raise_for_status()
            data = response.json()
            since = data['next_batch']
            with open(SINCE_PATH, 'w') as cursor:
                cursor.write(since)
            events = data.get('rooms', {}).get('join', {}).get(ROOM, {}).get('timeline', {}).get('events', [])
            for event in events:
                if event.get('type') != 'm.room.message':
                    continue
                event_id = event.get('event_id')
                if event_id and event_id in seen:
                    continue
                if event_id:
                    seen.add(event_id)
                if event.get('sender') == USER:
                    continue
                content = event.get('content', {})
                if content.get('msgtype') == 'm.audio':
                    send('Jeg mottok en talemelding, men talegjenkjenning er ikke aktivert ennå. Skriv kommandoen som tekst.')
                    continue
                text = content.get('body', '').strip()
                if not text or text.startswith('!'):
                    continue
                try:
                    reply = answer(text)
                except requests.exceptions.RequestException as error:
                    if '10.0.0.133' in str(error):
                        reply = 'Lokal AI på PC1 er avslått eller i gaming-modus. Home Assistant-styring fungerer fortsatt.'
                    else:
                        reply = 'Home Assistant svarte ikke på kommandoen. Ingen endring ble bekreftet.'
                except Exception:
                    reply = 'Jeg fikk ikke kontakt med lokal Ollama akkurat nå.'
                send(reply)
        except Exception:
            time.sleep(5)


if __name__ == '__main__':
    poll()
