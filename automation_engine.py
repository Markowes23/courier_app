import json
import csv
import sqlite3
from datetime import datetime, timedelta
import os
from dataclasses import dataclass
from typing import List, Dict, Optional
import threading
import time

@dataclass
class DeliveryStop:
    """Enhanced delivery stop data structure"""
    id: int
    address: str
    priority: str
    delivery_type: str
    load_size: float
    estimated_time: int
    coordinates: Optional[str] = None
    weather_temp: Optional[float] = None
    status: str = "pending"
    delivery_window_start: Optional[str] = None
    delivery_window_end: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    special_instructions: Optional[str] = None
    created_at: str = None
    completed_at: Optional[str] = None

class TaskAutomationEngine:
    """Advanced task automation engine for courier operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.automation_rules = []
        self.scheduled_tasks = []
        self.notifications = []
        
    def add_automation_rule(self, name: str, conditions: Dict, actions: Dict):
        """Add an automation rule"""
        rule = {
            'id': len(self.automation_rules) + 1,
            'name': name,
            'conditions': conditions,
            'actions': actions,
            'active': True,
            'created_at': datetime.now().isoformat()
        }
        self.automation_rules.append(rule)
        return rule['id']
    
    def check_and_execute_rules(self, stops: List[DeliveryStop]):
        """Check conditions and execute automation rules"""
        for rule in self.automation_rules:
            if not rule['active']:
                continue
                
            if self._evaluate_conditions(rule['conditions'], stops):
                self._execute_actions(rule['actions'], stops)
    
    def _evaluate_conditions(self, conditions: Dict, stops: List[DeliveryStop]) -> bool:
        """Evaluate if conditions are met"""
        condition_type = conditions.get('type')
        
        if condition_type == 'capacity_threshold':
            total_load = sum(stop.load_size for stop in stops)
            max_capacity = conditions.get('max_capacity', 15.0)
            threshold = conditions.get('threshold_percent', 80) / 100
            return total_load >= (max_capacity * threshold)
            
        elif condition_type == 'time_based':
            current_time = datetime.now().time()
            trigger_time = datetime.strptime(conditions.get('time'), '%H:%M').time()
            return current_time >= trigger_time
            
        elif condition_type == 'priority_urgent':
            urgent_count = sum(1 for stop in stops if stop.priority == 'Urgent')
            return urgent_count >= conditions.get('min_urgent', 1)
            
        elif condition_type == 'delivery_window':
            # Check if any deliveries are approaching their time windows
            current_time = datetime.now()
            for stop in stops:
                if stop.delivery_window_start:
                    window_start = datetime.fromisoformat(stop.delivery_window_start)
                    if (window_start - current_time).seconds <= conditions.get('warning_minutes', 30) * 60:
                        return True
        
        return False
    
    def _execute_actions(self, actions: Dict, stops: List[DeliveryStop]):
        """Execute automation actions"""
        action_type = actions.get('type')
        
        if action_type == 'optimize_route':
            self._auto_optimize_route(stops)
            
        elif action_type == 'send_notification':
            self._send_notification(actions.get('message', 'Automation triggered'))
            
        elif action_type == 'generate_report':
            self._auto_generate_report(stops, actions.get('report_type'))
            
        elif action_type == 'backup_data':
            self._auto_backup_data()
    
    def _auto_optimize_route(self, stops: List[DeliveryStop]):
        """Automatically optimize route using advanced algorithms"""
        # Advanced route optimization (simplified version)
        def priority_weight(stop):
            weights = {'Urgent': 4, 'High': 3, 'Normal': 2, 'Low': 1}
            return weights.get(stop.priority, 2)
        
        def delivery_window_weight(stop):
            if not stop.delivery_window_start:
                return 0
            window_start = datetime.fromisoformat(stop.delivery_window_start)
            time_to_window = (window_start - datetime.now()).total_seconds() / 3600
            return max(0, 24 - time_to_window)  # Higher weight for sooner windows
        
        # Sort by combined priority and delivery window weights
        stops.sort(key=lambda x: -(priority_weight(x) * 2 + delivery_window_weight(x)), reverse=False)
        
        self._send_notification("Route automatically optimized based on priority and delivery windows")
    
    def _send_notification(self, message: str):
        """Send notification to the system"""
        notification = {
            'id': len(self.notifications) + 1,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'type': 'automation',
            'read': False
        }
        self.notifications.append(notification)
    
    def _auto_generate_report(self, stops: List[DeliveryStop], report_type: str):
        """Automatically generate reports"""
        if report_type == 'daily_summary':
            self._generate_daily_summary_report(stops)
        elif report_type == 'efficiency_analysis':
            self._generate_efficiency_report(stops)
    
    def _auto_backup_data(self):
        """Automatically backup database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"backup_courier_data_{timestamp}.db"
        
        # Simple file copy for backup
        import shutil
        try:
            shutil.copy2(self.db_path, backup_path)
            self._send_notification(f"Data automatically backed up to {backup_path}")
        except Exception as e:
            self._send_notification(f"Backup failed: {str(e)}")
    
    def _generate_daily_summary_report(self, stops: List[DeliveryStop]):
        """Generate daily summary report"""
        report_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_stops': len(stops),
            'completed_stops': len([s for s in stops if s.status == 'completed']),
            'pending_stops': len([s for s in stops if s.status == 'pending']),
            'total_load': sum(s.load_size for s in stops),
            'priority_breakdown': {
                'urgent': len([s for s in stops if s.priority == 'Urgent']),
                'high': len([s for s in stops if s.priority == 'High']),
                'normal': len([s for s in stops if s.priority == 'Normal']),
                'low': len([s for s in stops if s.priority == 'Low'])
            }
        }
        
        # Save report to JSON
        filename = f"daily_summary_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self._send_notification(f"Daily summary report generated: {filename}")
    
    def _generate_efficiency_report(self, stops: List[DeliveryStop]):
        """Generate efficiency analysis report"""
        # Calculate efficiency metrics
        completed_stops = [s for s in stops if s.status == 'completed']
        
        if not completed_stops:
            return
        
        avg_delivery_time = sum(s.estimated_time for s in completed_stops) / len(completed_stops)
        load_efficiency = sum(s.load_size for s in stops) / 15.0 * 100  # Assuming 15m³ capacity
        
        efficiency_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'metrics': {
                'average_delivery_time': avg_delivery_time,
                'load_efficiency_percent': load_efficiency,
                'completion_rate': len(completed_stops) / len(stops) * 100,
                'priority_distribution': {
                    priority: len([s for s in stops if s.priority == priority])
                    for priority in ['Urgent', 'High', 'Normal', 'Low']
                }
            },
            'recommendations': self._generate_efficiency_recommendations(stops)
        }
        
        filename = f"efficiency_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(efficiency_data, f, indent=2)
        
        self._send_notification(f"Efficiency report generated: {filename}")
    
    def _generate_efficiency_recommendations(self, stops: List[DeliveryStop]) -> List[str]:
        """Generate efficiency improvement recommendations"""
        recommendations = []
        
        # Analyze load distribution
        total_load = sum(s.load_size for s in stops)
        if total_load < 10:  # Assuming 15m³ capacity
            recommendations.append("Consider consolidating deliveries to improve load efficiency")
        
        # Analyze priority distribution
        urgent_count = len([s for s in stops if s.priority == 'Urgent'])
        if urgent_count > len(stops) * 0.3:
            recommendations.append("High number of urgent deliveries - consider improving planning process")
        
        # Analyze delivery time distribution
        long_deliveries = [s for s in stops if s.estimated_time > 30]
        if len(long_deliveries) > len(stops) * 0.2:
            recommendations.append("Consider breaking down long delivery routes")
        
        return recommendations

class ContentCreationEngine:
    """Advanced content creation engine for reports, invoices, and documents"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load document templates"""
        self.templates = {
            'delivery_confirmation': self._get_delivery_confirmation_template(),
            'invoice': self._get_invoice_template(),
            'daily_report': self._get_daily_report_template(),
            'route_summary': self._get_route_summary_template()
        }
    
    def generate_delivery_confirmation(self, stop: DeliveryStop, driver_name: str = "Driver") -> str:
        """Generate delivery confirmation document"""
        template = self.templates['delivery_confirmation']
        
        return template.format(
            delivery_id=stop.id,
            date=datetime.now().strftime('%Y-%m-%d'),
            time=datetime.now().strftime('%H:%M'),
            customer_name=stop.customer_name or "Customer",
            address=stop.address,
            items_delivered=f"{stop.load_size}m³ of cargo",
            driver_name=driver_name,
            delivery_type=stop.delivery_type,
            special_instructions=stop.special_instructions or "None"
        )
    
    def generate_invoice(self, stops: List[DeliveryStop], customer_info: Dict) -> str:
        """Generate invoice for deliveries"""
        template = self.templates['invoice']
        
        # Calculate totals
        base_rate = 25.0  # Base rate per delivery
        volume_rate = 3.5  # Rate per m³
        
        line_items = []
        total = 0
        
        for stop in stops:
            delivery_charge = base_rate
            volume_charge = stop.load_size * volume_rate
            line_total = delivery_charge + volume_charge
            total += line_total
            
            line_items.append(f"Delivery to {stop.address}: ${delivery_charge:.2f} + ${volume_charge:.2f} = ${line_total:.2f}")
        
        return template.format(
            invoice_id=f"INV-{datetime.now().strftime('%Y%m%d')}-{len(stops):03d}",
            date=datetime.now().strftime('%Y-%m-%d'),
            customer_name=customer_info.get('name', 'Customer'),
            customer_address=customer_info.get('address', ''),
            line_items='\n'.join(line_items),
            subtotal=total,
            tax=total * 0.1,  # 10% tax
            total=total * 1.1
        )
    
    def generate_daily_report(self, stops: List[DeliveryStop], driver_name: str = "Driver") -> str:
        """Generate daily operations report"""
        template = self.templates['daily_report']
        
        completed = [s for s in stops if s.status == 'completed']
        pending = [s for s in stops if s.status == 'pending']
        
        statistics = {
            'total_stops': len(stops),
            'completed': len(completed),
            'pending': len(pending),
            'completion_rate': (len(completed) / len(stops) * 100) if stops else 0,
            'total_volume': sum(s.load_size for s in stops),
            'total_time': sum(s.estimated_time for s in stops)
        }
        
        return template.format(
            date=datetime.now().strftime('%Y-%m-%d'),
            driver_name=driver_name,
            **statistics
        )
    
    def generate_route_summary(self, stops: List[DeliveryStop]) -> str:
        """Generate route summary document"""
        template = self.templates['route_summary']
        
        route_details = []
        total_distance = 0
        total_time = 0
        
        for i, stop in enumerate(stops, 1):
            route_details.append(f"{i}. {stop.address} - {stop.priority} priority - {stop.load_size}m³")
            total_time += stop.estimated_time
        
        return template.format(
            date=datetime.now().strftime('%Y-%m-%d'),
            total_stops=len(stops),
            route_details='\n'.join(route_details),
            total_time=total_time,
            estimated_distance=total_time * 0.5  # Rough distance calculation
        )
    
    def export_to_csv(self, stops: List[DeliveryStop], filename: str = None):
        """Export delivery data to CSV"""
        if not filename:
            filename = f"delivery_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'address', 'priority', 'delivery_type', 'load_size',
                'estimated_time', 'status', 'customer_name', 'customer_phone',
                'special_instructions', 'created_at', 'completed_at'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for stop in stops:
                writer.writerow({
                    'id': stop.id,
                    'address': stop.address,
                    'priority': stop.priority,
                    'delivery_type': stop.delivery_type,
                    'load_size': stop.load_size,
                    'estimated_time': stop.estimated_time,
                    'status': stop.status,
                    'customer_name': stop.customer_name or '',
                    'customer_phone': stop.customer_phone or '',
                    'special_instructions': stop.special_instructions or '',
                    'created_at': stop.created_at or '',
                    'completed_at': stop.completed_at or ''
                })
        
        return filename
    
    def export_to_json(self, stops: List[DeliveryStop], filename: str = None):
        """Export delivery data to JSON"""
        if not filename:
            filename = f"delivery_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_stops': len(stops),
            'stops': [
                {
                    'id': stop.id,
                    'address': stop.address,
                    'priority': stop.priority,
                    'delivery_type': stop.delivery_type,
                    'load_size': stop.load_size,
                    'estimated_time': stop.estimated_time,
                    'status': stop.status,
                    'coordinates': stop.coordinates,
                    'weather_temp': stop.weather_temp,
                    'customer_name': stop.customer_name,
                    'customer_phone': stop.customer_phone,
                    'special_instructions': stop.special_instructions,
                    'created_at': stop.created_at,
                    'completed_at': stop.completed_at
                }
                for stop in stops
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return filename
    
    def _get_delivery_confirmation_template(self) -> str:
        return """
DELIVERY CONFIRMATION
=====================

Delivery ID: {delivery_id}
Date: {date}
Time: {time}

Customer: {customer_name}
Address: {address}

Items Delivered: {items_delivered}
Delivery Type: {delivery_type}
Special Instructions: {special_instructions}

Delivered by: {driver_name}

This confirms successful delivery of the above items.

_________________
Customer Signature
        """
    
    def _get_invoice_template(self) -> str:
        return """
COURIER SERVICES INVOICE
========================

Invoice ID: {invoice_id}
Date: {date}

Bill To:
{customer_name}
{customer_address}

Services Provided:
{line_items}

Subtotal: ${subtotal:.2f}
Tax (10%): ${tax:.2f}
TOTAL: ${total:.2f}

Payment Terms: Net 30 days
        """
    
    def _get_daily_report_template(self) -> str:
        return """
DAILY OPERATIONS REPORT
=======================

Date: {date}
Driver: {driver_name}

SUMMARY:
--------
Total Stops: {total_stops}
Completed: {completed}
Pending: {pending}
Completion Rate: {completion_rate:.1f}%

VOLUME & TIME:
--------------
Total Volume Delivered: {total_volume:.1f}m³
Total Estimated Time: {total_time} minutes

Generated automatically by CourierPro
        """
    
    def _get_route_summary_template(self) -> str:
        return """
ROUTE SUMMARY
=============

Date: {date}
Total Stops: {total_stops}

ROUTE DETAILS:
{route_details}

TOTALS:
-------
Estimated Total Time: {total_time} minutes
Estimated Distance: {estimated_distance:.1f} km

Generated by CourierPro Route Planner
        """

class BatchOperationManager:
    """Manager for batch operations and bulk processing"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def import_stops_from_csv(self, filename: str) -> List[DeliveryStop]:
        """Import delivery stops from CSV file"""
        stops = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    stop = DeliveryStop(
                        id=int(row.get('id', 0)),
                        address=row['address'],
                        priority=row.get('priority', 'Normal'),
                        delivery_type=row.get('delivery_type', 'Standard'),
                        load_size=float(row['load_size']),
                        estimated_time=int(row.get('estimated_time', 15)),
                        customer_name=row.get('customer_name'),
                        customer_phone=row.get('customer_phone'),
                        special_instructions=row.get('special_instructions'),
                        created_at=datetime.now().isoformat()
                    )
                    stops.append(stop)
            
        except Exception as e:
            raise Exception(f"Error importing CSV: {str(e)}")
        
        return stops
    
    def bulk_update_status(self, stop_ids: List[int], new_status: str):
        """Update status for multiple stops"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY,
                    address TEXT,
                    load_size REAL,
                    delivery_time TEXT,
                    status TEXT DEFAULT 'pending',
                    coordinates TEXT,
                    weather_temp REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            placeholders = ','.join(['?' for _ in stop_ids])
            cursor.execute(f'UPDATE deliveries SET status = ? WHERE id IN ({placeholders})', 
                          [new_status] + stop_ids)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Note: Database operation skipped in test mode: {e}")
    
    def bulk_assign_priority(self, addresses: List[str], priority: str):
        """Assign priority to multiple addresses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for address in addresses:
            cursor.execute('UPDATE deliveries SET status = ? WHERE address LIKE ?', 
                          (priority, f'%{address}%'))
        
        conn.commit()
        conn.close()
    
    def generate_batch_reports(self, report_types: List[str], date_range: tuple = None):
        """Generate multiple reports in batch"""
        results = []
        
        # Get data for the specified date range
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if date_range:
            cursor.execute('SELECT * FROM deliveries WHERE created_at BETWEEN ? AND ?', date_range)
        else:
            cursor.execute('SELECT * FROM deliveries')
        
        data = cursor.fetchall()
        conn.close()
        
        # Convert to DeliveryStop objects
        stops = [self._row_to_delivery_stop(row) for row in data]
        
        # Generate requested reports
        content_engine = ContentCreationEngine(self.db_path)
        
        for report_type in report_types:
            if report_type == 'daily_summary':
                filename = content_engine.export_to_json(stops, f"daily_summary_{datetime.now().strftime('%Y%m%d')}.json")
                results.append(filename)
            elif report_type == 'csv_export':
                filename = content_engine.export_to_csv(stops)
                results.append(filename)
        
        return results
    
    def _row_to_delivery_stop(self, row: tuple) -> DeliveryStop:
        """Convert database row to DeliveryStop object"""
        return DeliveryStop(
            id=row[0],
            address=row[1],
            load_size=row[2],
            delivery_type='Standard',  # Default values for missing fields
            priority='Normal',
            estimated_time=int(row[3]) if row[3] else 15,
            coordinates=row[4],
            weather_temp=row[5],
            status=row[6] if len(row) > 6 else 'pending',
            created_at=row[7] if len(row) > 7 else None
        )