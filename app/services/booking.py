from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import select
from app.models.db import AsyncSessionLocal, Booking


class BookingService:
    """Creates and retrieves interview bookings stored in SQLite."""

    @staticmethod
    def validate_datetime(date_str: str, time_str: str) -> tuple[bool, Optional[str]]:
        """Check date (YYYY-MM-DD) and time (HH:MM) formats are valid."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date '{date_str}'. Use YYYY-MM-DD."

        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return False, f"Invalid time '{time_str}'. Use HH:MM (24-hour)."

        return True, None

    @staticmethod
    async def create_booking(name: str, email: str, date: str, time: str) -> Dict[str, Any]:
        """Validate and save a new booking. Returns success flag and booking data or error."""
        valid, error = BookingService.validate_datetime(date, time)
        if not valid:
            return {"success": False, "error": error}

        async with AsyncSessionLocal() as session:
            booking = Booking(name=name, email=email, date=date, time=time)
            session.add(booking)
            await session.commit()
            await session.refresh(booking)

            return {
                "success": True,
                "booking": {
                    "id": booking.id,
                    "name": booking.name,
                    "email": booking.email,
                    "date": booking.date,
                    "time": booking.time,
                    "created_at": booking.created_at.isoformat() if booking.created_at else None,
                },
            }

    @staticmethod
    async def get_bookings(email: Optional[str] = None) -> list:
        """Return all bookings, or filter by email if provided."""
        async with AsyncSessionLocal() as session:
            query = select(Booking).where(Booking.email == email) if email else select(Booking)
            result = await session.execute(query)
            bookings = result.scalars().all()

            return [
                {
                    "id": b.id,
                    "name": b.name,
                    "email": b.email,
                    "date": b.date,
                    "time": b.time,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                }
                for b in bookings
            ]
