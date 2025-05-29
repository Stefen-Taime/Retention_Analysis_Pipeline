from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List, Optional
import datetime
from clickhouse_driver import Client
import os

app = FastAPI(title="Video Retention Analytics API", version="1.0.0")

CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'clickhouse-server')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', 9000))
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', '')
CLICKHOUSE_DB = 'default'

def get_clickhouse_client():
    """Crée une connexion ClickHouse"""
    client = Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
        settings={'use_numpy': False}
    )
    return client

class RetentionDataPoint(BaseModel):
    video_time_sec: int
    current_viewers: Optional[int] = None
    retention_percentage: Optional[float] = None

class RetentionCurveResponse(BaseModel):
    video_id: str
    data_points: List[RetentionDataPoint]
    total_unique_viewers: Optional[int] = None

class DropOffPoint(BaseModel):
    video_time_sec: int
    current_viewers: int
    previous_viewers: int
    drop_off_count: int
    drop_off_percentage: float

class SignificantDropOffsResponse(BaseModel):
    video_id: str
    drop_offs: List[DropOffPoint]

class EngagementSummary(BaseModel):
    video_id: str
    average_watch_time_sec: Optional[float] = None
    unique_viewers: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    """Vérifier la connexion à ClickHouse au démarrage"""
    try:
        client = get_clickhouse_client()
        client.execute('SELECT 1')
        print("✅ Successfully connected to ClickHouse.")
    except Exception as e:
        print(f"❌ Failed to connect to ClickHouse on startup: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()

@app.get("/")
async def root():
    """Endpoint de base pour vérifier que l'API fonctionne"""
    return {"message": "Video Retention Analytics API", "status": "running"}

@app.get("/health")
async def health_check():
    """Endpoint de santé pour vérifier la connexion ClickHouse"""
    try:
        client = get_clickhouse_client()
        client.execute('SELECT 1')
        return {"status": "healthy", "clickhouse": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ClickHouse connection failed: {str(e)}")
    finally:
        if 'client' in locals():
            client.disconnect()

@app.get("/videos")
async def list_videos():
    """Liste toutes les vidéos disponibles avec leurs métadonnées"""
    client = get_clickhouse_client()
    try:
        query = """
        SELECT 
            video_id,
            COUNT(DISTINCT user_id) as unique_viewers,
            MIN(video_time_sec) as min_time,
            MAX(video_time_sec) as max_time,
            COUNT(*) as total_events
        FROM default.viewer_events_raw
        WHERE event_type = 'VIEW_SEGMENT_START'
        GROUP BY video_id
        ORDER BY unique_viewers DESC
        LIMIT 20
        """
        data = client.execute(query)
        
        videos = []
        for row in data:
            videos.append({
                "video_id": row[0],
                "unique_viewers": row[1],
                "duration_seconds": row[3] - row[2] + 1,
                "total_events": row[4]
            })
        
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying videos: {str(e)}")
    finally:
        client.disconnect()

@app.get("/video/{video_id}/retention_curve", response_model=RetentionCurveResponse)
async def get_retention_curve(video_id: str = Path(..., title="The ID of the video to analyze")):
    """Obtient la courbe de rétention pour une vidéo donnée"""
    client = get_clickhouse_client()
    try:
        # Requête pour le nombre total de spectateurs uniques
        query_total_viewers = """
        SELECT COUNT(DISTINCT user_id)
        FROM default.viewer_events_raw
        WHERE video_id = %(video_id)s AND event_type = 'VIEW_SEGMENT_START'
        """
        total_result = client.execute(query_total_viewers, {'video_id': video_id})
        total_unique_viewers = total_result[0][0] if total_result and total_result[0] else 0

        if total_unique_viewers == 0:
            return RetentionCurveResponse(
                video_id=video_id, 
                data_points=[], 
                total_unique_viewers=0
            )

        # Requête pour la courbe de rétention basée sur les utilisateurs uniques
        query_curve = """
        SELECT
            video_time_sec,
            COUNT(DISTINCT user_id) AS current_viewers
        FROM default.viewer_events_raw
        WHERE video_id = %(video_id)s AND event_type = 'VIEW_SEGMENT_START'
        GROUP BY video_time_sec
        ORDER BY video_time_sec
        """

        data = client.execute(query_curve, {'video_id': video_id})
       
        response_data_points = []
        for row in data:
            video_time_sec, current_viewers = row
            retention_percentage = (current_viewers * 100.0 / total_unique_viewers) if total_unique_viewers > 0 else 0
            response_data_points.append(
                RetentionDataPoint(
                    video_time_sec=video_time_sec,
                    current_viewers=current_viewers,
                    retention_percentage=retention_percentage
                )
            )
       
        return RetentionCurveResponse(
            video_id=video_id, 
            data_points=response_data_points,
            total_unique_viewers=total_unique_viewers
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying ClickHouse: {str(e)}")
    finally:
        client.disconnect()

@app.get("/video/{video_id}/significant_dropoffs", response_model=SignificantDropOffsResponse)
async def get_significant_dropoffs(
    video_id: str = Path(..., title="The ID of the video"), 
    threshold_percentage: float = 10.0
):
    """Identifie les points de chute significatifs dans la rétention"""
    client = get_clickhouse_client()
    try:
        query = """
        WITH RetentionCurve AS (
            SELECT
                video_time_sec,
                COUNT(DISTINCT user_id) AS current_viewers
            FROM default.viewer_events_raw
            WHERE video_id = %(video_id)s AND event_type = 'VIEW_SEGMENT_START'
            GROUP BY video_time_sec
            ORDER BY video_time_sec
        ),
        RetentionWithLag AS (
            SELECT
                video_time_sec,
                current_viewers,
                lagInFrame(current_viewers, 1, 0) OVER (ORDER BY video_time_sec) AS previous_viewers
            FROM RetentionCurve
            WHERE current_viewers > 0
        )
        SELECT
            video_time_sec,
            current_viewers,
            previous_viewers,
            (previous_viewers - current_viewers) AS drop_off_count,
            ((previous_viewers - current_viewers) * 100.0) / previous_viewers AS drop_off_percentage
        FROM RetentionWithLag
        WHERE previous_viewers > 0 AND drop_off_percentage > %(threshold)s
        ORDER BY video_time_sec
        """

        params = {'video_id': video_id, 'threshold': threshold_percentage}
        data = client.execute(query, params)
       
        drop_offs = [
            DropOffPoint(
                video_time_sec=row[0],
                current_viewers=row[1],
                previous_viewers=row[2],
                drop_off_count=row[3],
                drop_off_percentage=row[4]
            ) for row in data
        ]
        
        return SignificantDropOffsResponse(video_id=video_id, drop_offs=drop_offs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying ClickHouse for dropoffs: {str(e)}")
    finally:
        client.disconnect()

@app.get("/video/{video_id}/engagement_summary", response_model=EngagementSummary)
async def get_engagement_summary(video_id: str = Path(..., title="The ID of the video")):
    """Obtient un résumé de l'engagement pour une vidéo"""
    client = get_clickhouse_client()
    try:
        query = """
        WITH SessionDurations AS (
            SELECT
                video_id,
                session_id,
                user_id,
                COUNT(DISTINCT video_time_sec) AS watched_duration_sec
            FROM default.viewer_events_raw
            WHERE video_id = %(video_id)s AND event_type = 'VIEW_SEGMENT_START'
            GROUP BY video_id, session_id, user_id
        )
        SELECT
            video_id,
            AVG(watched_duration_sec) AS average_watch_time_sec,
            COUNT(DISTINCT user_id) AS unique_viewers
        FROM SessionDurations
        WHERE video_id = %(video_id)s
        GROUP BY video_id
        """

        params = {'video_id': video_id}
        result = client.execute(query, params)

        if not result:
            return EngagementSummary(video_id=video_id)

        row = result[0]
        return EngagementSummary(
            video_id=row[0],
            average_watch_time_sec=float(row[1]) if row[1] else None,
            unique_viewers=int(row[2]) if row[2] else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying ClickHouse for engagement summary: {str(e)}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)