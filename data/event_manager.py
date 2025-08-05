"""
Macroeconomic Event Management System
====================================

Manages economic events, announcements, and political events that may impact
financial markets with intelligent event classification and impact assessment.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

class EventManager:
    """Manages macroeconomic and political events with impact analysis."""
    
    def __init__(self, db_path: str = "data/events.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize the events database with proper schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    impact_level INTEGER DEFAULT 2,
                    currency TEXT,
                    actual_value REAL,
                    forecast_value REAL,
                    previous_value REAL,
                    source TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
            
            conn.commit()
            conn.close()
            
            # Populate with sample events
            self._populate_sample_events()
            
            self.logger.info("Events database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing events database: {e}")
    
    def _populate_sample_events(self) -> None:
        """Populate database with sample economic events."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we already have events
        cursor.execute('SELECT COUNT(*) FROM events')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Sample events for demonstration
        sample_events = [
            ('2024-01-31', 'central_bank', 'FOMC Meeting', 'Federal Reserve policy decision', 5, 'USD'),
            ('2024-02-02', 'employment', 'Non-Farm Payrolls', 'Monthly employment report', 4, 'USD'),
            ('2024-02-13', 'inflation', 'Consumer Price Index', 'Monthly inflation data', 4, 'USD'),
            ('2024-03-20', 'central_bank', 'FOMC Meeting', 'Federal Reserve policy decision', 5, 'USD'),
            ('2024-03-28', 'gdp', 'Q4 GDP Final', 'Final Q4 GDP reading', 3, 'USD'),
            ('2024-04-25', 'central_bank', 'ECB Meeting', 'European Central Bank decision', 4, 'EUR'),
            ('2024-05-01', 'central_bank', 'FOMC Meeting', 'Federal Reserve policy decision', 5, 'USD'),
            ('2024-06-12', 'central_bank', 'FOMC Meeting', 'Federal Reserve policy decision', 5, 'USD'),
            ('2024-11-05', 'election', 'US Presidential Election', 'US general election', 5, 'USD'),
            ('2024-12-18', 'central_bank', 'FOMC Meeting', 'Federal Reserve policy decision', 5, 'USD'),
        ]
        
        for event in sample_events:
            cursor.execute('''
                INSERT INTO events (date, event_type, title, description, impact_level, currency, source)
                VALUES (?, ?, ?, ?, ?, ?, 'system')
            ''', event)
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Populated database with {len(sample_events)} sample events")
    
    def get_events_in_range(self, start_date: str, end_date: str, 
                           event_types: Optional[List[str]] = None,
                           min_impact: int = 1) -> pd.DataFrame:
        """Retrieve events within a date range with optional filtering."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT date, event_type, title, description, impact_level, currency
                FROM events 
                WHERE date >= ? AND date <= ? AND impact_level >= ?
            '''
            params = [start_date, end_date, min_impact]
            
            if event_types:
                placeholders = ','.join(['?' for _ in event_types])
                query += f' AND event_type IN ({placeholders})'
                params.extend(event_types)
            
            query += ' ORDER BY date ASC'
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving events: {e}")
            return pd.DataFrame()
    
    def get_events_for_chart(self, start_date: str, end_date: str) -> Dict:
        """Get events formatted for chart overlays with impact-based styling."""
        df = self.get_events_in_range(start_date, end_date)
        
        if df.empty:
            return {}
        
        # Color and size mapping based on impact level
        impact_styling = {
            1: {'color': '#90EE90', 'size': 6},   # Light green, small
            2: {'color': '#FFD700', 'size': 8},   # Gold, medium
            3: {'color': '#FFA500', 'size': 10},  # Orange, medium-large
            4: {'color': '#FF6347', 'size': 12},  # Tomato, large
            5: {'color': '#FF0000', 'size': 15}   # Red, extra large
        }
        
        chart_events = {
            'dates': [],
            'titles': [],
            'descriptions': [],
            'colors': [],
            'sizes': []
        }
        
        for _, event in df.iterrows():
            chart_events['dates'].append(event['date'])
            chart_events['titles'].append(event['title'])
            chart_events['descriptions'].append(event['description'])
            
            style = impact_styling.get(event['impact_level'], impact_styling[2])
            chart_events['colors'].append(style['color'])
            chart_events['sizes'].append(style['size'])
        
        return chart_events

# Global event manager instance
event_manager = EventManager()
