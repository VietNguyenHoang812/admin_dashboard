from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import csv
import io
from datetime import datetime

from app.core.database import get_db
from app.services.metric_service import get_recent_metrics

router = APIRouter()


@router.get("/export/csv")
async def export_csv(
    hostname: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    metrics = await get_recent_metrics(db, hostname, limit=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "cpu_percent", "memory_percent", "disk_percent"])
    for m in metrics:
        writer.writerow([m.timestamp, m.cpu_percent, m.memory_percent, m.disk_percent])

    output.seek(0)
    filename = f"{hostname}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
