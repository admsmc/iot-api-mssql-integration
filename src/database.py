"""
Database Connection and Operations Module
Handles MS SQL Server connections and operations
"""
import pyodbc
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MS SQL Server database connections and operations"""
    
    def __init__(self, server: str, database: str, username: str = None, password: str = None,
                 driver: str = "ODBC Driver 17 for SQL Server", trusted_connection: bool = False):
        """
        Initialize database connection
        
        Args:
            server: SQL Server address
            database: Database name
            username: Database username (optional if using trusted connection)
            password: Database password (optional if using trusted connection)
            driver: ODBC driver name
            trusted_connection: Use Windows authentication
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.trusted_connection = trusted_connection
        self.connection = None
        
    def connect(self) -> bool:
        """
        Establish database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.trusted_connection:
                conn_str = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"Trusted_Connection=yes;"
                )
            else:
                conn_str = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
            
            self.connection = pyodbc.connect(conn_str)
            logger.info(f"Successfully connected to database {self.database} on {self.server}")
            return True
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {e}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
            
    def upsert_channel(self, channel_data: Dict) -> bool:
        """
        Insert or update channel information
        
        Args:
            channel_data: Dictionary containing channel information
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection")
            return False
            
        try:
            cursor = self.connection.cursor()
            
            sql = """
                MERGE iot.Channels AS target
                USING (SELECT ? AS ChannelID) AS source
                ON target.ChannelID = source.ChannelID
                WHEN MATCHED THEN
                    UPDATE SET 
                        ChannelName = ?,
                        Description = ?,
                        Latitude = ?,
                        Longitude = ?,
                        Field1Name = ?,
                        Field2Name = ?,
                        Field3Name = ?,
                        Field4Name = ?,
                        Field5Name = ?,
                        Field6Name = ?,
                        Field7Name = ?,
                        Field8Name = ?,
                        UpdatedAt = GETUTCDATE()
                WHEN NOT MATCHED THEN
                    INSERT (ChannelID, ChannelName, Description, Latitude, Longitude,
                            Field1Name, Field2Name, Field3Name, Field4Name,
                            Field5Name, Field6Name, Field7Name, Field8Name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            
            params = (
                channel_data.get('id'),
                channel_data.get('name'),
                channel_data.get('description'),
                channel_data.get('latitude'),
                channel_data.get('longitude'),
                channel_data.get('field1'),
                channel_data.get('field2'),
                channel_data.get('field3'),
                channel_data.get('field4'),
                channel_data.get('field5'),
                channel_data.get('field6'),
                channel_data.get('field7'),
                channel_data.get('field8'),
                # Repeat for INSERT
                channel_data.get('id'),
                channel_data.get('name'),
                channel_data.get('description'),
                channel_data.get('latitude'),
                channel_data.get('longitude'),
                channel_data.get('field1'),
                channel_data.get('field2'),
                channel_data.get('field3'),
                channel_data.get('field4'),
                channel_data.get('field5'),
                channel_data.get('field6'),
                channel_data.get('field7'),
                channel_data.get('field8'),
            )
            
            cursor.execute(sql, params)
            self.connection.commit()
            logger.info(f"Channel {channel_data.get('id')} upserted successfully")
            return True
        except pyodbc.Error as e:
            logger.error(f"Error upserting channel: {e}")
            self.connection.rollback()
            return False
            
    def insert_sensor_readings(self, channel_id: int, feeds: List[Dict]) -> int:
        """
        Insert sensor readings in batch
        
        Args:
            channel_id: Channel ID
            feeds: List of feed entries
            
        Returns:
            Number of records inserted
        """
        if not self.connection:
            logger.error("No database connection")
            return 0
            
        try:
            cursor = self.connection.cursor()
            inserted_count = 0
            
            sql = """
                INSERT INTO iot.SensorReadings 
                (ChannelID, EntryID, CreatedAt, Field1, Field2, Field3, Field4,
                 Field5, Field6, Field7, Field8, Latitude, Longitude, Elevation, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for feed in feeds:
                try:
                    params = (
                        channel_id,
                        feed.get('entry_id'),
                        feed.get('created_at'),
                        self._safe_float(feed.get('field1')),
                        self._safe_float(feed.get('field2')),
                        self._safe_float(feed.get('field3')),
                        self._safe_float(feed.get('field4')),
                        self._safe_float(feed.get('field5')),
                        self._safe_float(feed.get('field6')),
                        self._safe_float(feed.get('field7')),
                        self._safe_float(feed.get('field8')),
                        self._safe_float(feed.get('latitude')),
                        self._safe_float(feed.get('longitude')),
                        self._safe_float(feed.get('elevation')),
                        feed.get('status')
                    )
                    
                    cursor.execute(sql, params)
                    inserted_count += 1
                except pyodbc.IntegrityError:
                    # Skip duplicate entries
                    continue
            
            self.connection.commit()
            logger.info(f"Inserted {inserted_count} sensor readings for channel {channel_id}")
            return inserted_count
        except pyodbc.Error as e:
            logger.error(f"Error inserting sensor readings: {e}")
            self.connection.rollback()
            return 0
            
    def call_stored_procedure(self, proc_name: str, params: tuple = None) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a stored procedure
        
        Args:
            proc_name: Stored procedure name
            params: Tuple of parameters
            
        Returns:
            List of result dictionaries or None if error
        """
        if not self.connection:
            logger.error("No database connection")
            return None
            
        try:
            cursor = self.connection.cursor()
            
            if params:
                placeholders = ','.join(['?' for _ in params])
                sql = f"EXEC {proc_name} {placeholders}"
                cursor.execute(sql, params)
            else:
                sql = f"EXEC {proc_name}"
                cursor.execute(sql)
            
            # Fetch results if any
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                self.connection.commit()
                logger.info(f"Executed stored procedure {proc_name}")
                return results
            else:
                self.connection.commit()
                logger.info(f"Executed stored procedure {proc_name} (no results)")
                return []
        except pyodbc.Error as e:
            logger.error(f"Error executing stored procedure {proc_name}: {e}")
            self.connection.rollback()
            return None
            
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
