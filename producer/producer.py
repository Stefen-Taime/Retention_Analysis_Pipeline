import json
import uuid
import datetime
import time
import random
from kafka import KafkaProducer
from faker import Faker

fake = Faker()

REDPANDA_BROKER = 'redpanda:9092'
TOPIC_NAME = 'viewer_events'

producer = KafkaProducer(
    bootstrap_servers=REDPANDA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None,
    acks='all',
    retries=5,
    retry_backoff_ms=1000
)

VIDEO_IDS = [fake.uuid4() for _ in range(10)]  
USER_IDS = [fake.uuid4() for _ in range(100)]  

VIDEO_METADATA = {
    str(vid): {
        'duration': random.randint(30, 1800),  
        'popularity': random.uniform(0.1, 1.0)  
    } for vid in VIDEO_IDS
}

def generate_event(video_id, user_id, session_id, current_video_time_sec, event_type_choice):
    event_type = event_type_choice
    delta = 0
    if event_type == "VIEW_SEGMENT_START":
        delta = 1
    elif event_type == "VIEW_SEGMENT_END":
        delta = -1
    
    event = {
        "event_id": str(uuid.uuid4()),
        "video_id": str(video_id),
        "user_id": str(user_id),
        "session_id": str(session_id),
        "event_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "video_time_sec": current_video_time_sec,
        "delta_viewers": delta
    }
    return event

def calculate_dropout_probability(video_time_sec, video_duration):
    """Probabilité de quitter en fonction du temps - courbe réaliste"""
    progress = video_time_sec / video_duration
    if progress < 0.1:  # 10% du début
        return 0.15  # 15% de chance de quitter
    elif progress < 0.5:  # Milieu de vidéo
        return 0.05  # 5% de chance
    elif progress > 0.8:  # 80% vers la fin
        return 0.12  # 12% de chance
    else:
        return 0.08  # 8% chance normale

def simulate_realistic_viewing_session():
    """Simule une session de visionnage réaliste"""
    video_weights = [VIDEO_METADATA[str(vid)]['popularity'] for vid in VIDEO_IDS]
    video_id = random.choices(VIDEO_IDS, weights=video_weights)[0]
    video_duration = VIDEO_METADATA[str(video_id)]['duration']
    
    user_id = random.choice(USER_IDS)
    session_id = str(uuid.uuid4())
    
    viewing_patterns = [
        'binge_watcher',    # Regarde longtemps
        'casual_viewer',    # Regarde un peu puis quitte
        'skipper',          # Saute beaucoup
        'completer'         # Termine la vidéo
    ]
    
    pattern = random.choices(viewing_patterns, weights=[0.15, 0.5, 0.25, 0.1])[0]
    
    print(f"🎬 User {user_id[:8]} starts watching video {str(video_id)[:8]} ({video_duration}s) - Pattern: {pattern}")
    
    if pattern == 'casual_viewer':
        watch_duration = random.randint(5, int(video_duration * 0.3))
        start_time = random.randint(0, max(1, video_duration - watch_duration))
    elif pattern == 'binge_watcher':
        watch_duration = random.randint(int(video_duration * 0.6), video_duration)
        start_time = 0
    elif pattern == 'skipper':
        return simulate_skipping_session(video_id, user_id, session_id, video_duration)
    else:  # completer
        watch_duration = random.randint(int(video_duration * 0.8), video_duration)
        start_time = 0
    
    return simulate_continuous_viewing(video_id, user_id, session_id, start_time, watch_duration, video_duration)

def simulate_continuous_viewing(video_id, user_id, session_id, start_time, watch_duration, video_duration):
    """Simule un visionnage continu avec des abandons probabilistes"""
    events_sent = 0
    current_time = start_time
    
    for sec_offset in range(watch_duration):
        current_video_time = start_time + sec_offset
        if current_video_time >= video_duration:
            break
            
        dropout_prob = calculate_dropout_probability(current_video_time, video_duration)
        if random.random() < dropout_prob:
            print(f"   👋 User drops out at {current_video_time}s")
            break
        
        start_event = generate_event(video_id, user_id, session_id, current_video_time, "VIEW_SEGMENT_START")
        producer.send(TOPIC_NAME, key=str(video_id), value=start_event)
        events_sent += 1
        
        if random.random() < 0.03:  # 3% de chance
            pause_event = generate_event(video_id, user_id, session_id, current_video_time, "PAUSE")
            producer.send(TOPIC_NAME, key=str(video_id), value=pause_event)
            time.sleep(random.uniform(1, 8))  # Pause réaliste
            play_event = generate_event(video_id, user_id, session_id, current_video_time, "PLAY")
            producer.send(TOPIC_NAME, key=str(video_id), value=play_event)
            events_sent += 2
        
        time.sleep(random.uniform(0.8, 1.2))  # ~1 seconde réelle
        
        end_event = generate_event(video_id, user_id, session_id, current_video_time, "VIEW_SEGMENT_END")
        producer.send(TOPIC_NAME, key=str(video_id), value=end_event)
        events_sent += 1
    
    return events_sent

def simulate_skipping_session(video_id, user_id, session_id, video_duration):
    """Simule un utilisateur qui saute beaucoup dans la vidéo"""
    events_sent = 0
    positions = sorted(random.sample(range(0, video_duration), min(5, video_duration//10)))
    
    for pos in positions:
        seek_event = generate_event(video_id, user_id, session_id, pos, "SEEK")
        producer.send(TOPIC_NAME, key=str(video_id), value=seek_event)
        events_sent += 1
        
        watch_time = random.randint(3, 15)
        for i in range(watch_time):
            if pos + i >= video_duration:
                break
                
            start_event = generate_event(video_id, user_id, session_id, pos + i, "VIEW_SEGMENT_START")
            producer.send(TOPIC_NAME, key=str(video_id), value=start_event)
            time.sleep(0.1)
            end_event = generate_event(video_id, user_id, session_id, pos + i, "VIEW_SEGMENT_END")
            producer.send(TOPIC_NAME, key=str(video_id), value=end_event)
            events_sent += 2
            
            if random.random() < 0.2:  
                break
    
    return events_sent

def simulate_multiple_concurrent_users():
    """Simule plusieurs utilisateurs regardant en même temps"""
    concurrent_sessions = random.randint(1, 8)  
    total_events = 0
    
    print(f"🚀 Starting {concurrent_sessions} concurrent viewing sessions")
    
    for _ in range(concurrent_sessions):
        events = simulate_realistic_viewing_session()
        total_events += events
        
        time.sleep(random.uniform(0.5, 3))
    
    producer.flush()
    print(f"📊 Batch completed: {total_events} events sent")
    return total_events

print(f"Connecting to Redpanda broker at {REDPANDA_BROKER}...")
time.sleep(5)

print(f"🎥 Starting realistic video streaming simulation...")
print(f"📹 {len(VIDEO_IDS)} videos available")
print(f"👥 {len(USER_IDS)} users in the system")

try:
    total_events_sent = 0
    batch_count = 0
    
    while True:
        batch_events = simulate_multiple_concurrent_users()
        total_events_sent += batch_events
        batch_count += 1
        
        if batch_count % 5 == 0:
            print(f"📈 Stats: {batch_count} batches, {total_events_sent} total events")
        
        # Délai réaliste entre les batches (nouvelles arrivées d'utilisateurs)
        time.sleep(random.uniform(5, 15))

except KeyboardInterrupt:
    print("\n🛑 Shutting down producer...")
finally:
    producer.close()
    print("✅ Producer closed.")