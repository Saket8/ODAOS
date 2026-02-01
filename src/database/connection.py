"""Oracle Database Connection Manager.

Provides connection pooling and query execution for Oracle databases
using the oracledb driver with OCI integration.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional

import oracledb
from oci.config import from_file as oci_from_file
from oci.database import DatabaseClient

from ..core.config import get_settings


class OracleConnectionManager:
    """Manages Oracle database connections with async connection pooling."""
    
    def __init__(
        self,
        dsn: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        min_connections: int = 2,
        max_connections: int = 10,
    ):
        """Initialize the connection manager.
        
        Args:
            dsn: Database connection string (host:port/service).
                 If None, loads from environment.
            user: Database username. If None, loads from environment.
            password: Database password. If None, loads from environment.
            min_connections: Minimum pool connections.
            max_connections: Maximum pool connections.
        """
        settings = get_settings()
        
        self.dsn = dsn or settings.oracle_dsn
        self.user = user or settings.oracle_user
        self.password = password or (
            settings.oracle_password.get_secret_value() 
            if settings.oracle_password else None
        )
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        self._pool: Optional[oracledb.AsyncConnectionPool] = None
        self._oci_client: Optional[DatabaseClient] = None
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._pool is not None:
            return
        
        if not all([self.dsn, self.user, self.password]):
            raise ValueError(
                "Database credentials not configured. "
                "Set ORACLE_DSN, ORACLE_USER, ORACLE_PASSWORD in .env file."
            )
        
        # Using thin mode - no Oracle Instant Client needed
        # For thick mode, uncomment: oracledb.init_oracle_client()
        
        self._pool = oracledb.create_pool_async(
            user=self.user,
            password=self.password,
            dsn=self.dsn,
            min=self.min_connections,
            max=self.max_connections,
            getmode=oracledb.POOL_GETMODE_WAIT,
        )
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool as an async context manager.
        
        Usage:
            async with manager.get_connection() as conn:
                cursor = conn.cursor()
                ...
        """
        if self._pool is None:
            await self.initialize()
        
        connection = await self._pool.acquire()
        try:
            yield connection
        finally:
            await self._pool.release(connection)
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[dict] = None,
        fetch_all: bool = True,
    ) -> list[dict[str, Any]]:
        """Execute a query and return results as a list of dictionaries.
        
        Args:
            query: SQL query to execute.
            params: Optional query parameters.
            fetch_all: If True, fetch all rows. If False, return cursor.
        
        Returns:
            List of row dictionaries with column names as keys.
        """
        async with self.get_connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, params or {})
                
                if not fetch_all:
                    return []
                
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
    
    async def execute_many(
        self, 
        query: str, 
        params_list: list[dict],
    ) -> int:
        """Execute a query with multiple parameter sets.
        
        Args:
            query: SQL query to execute.
            params_list: List of parameter dictionaries.
        
        Returns:
            Number of rows affected.
        """
        async with self.get_connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.executemany(query, params_list)
                await connection.commit()
                return cursor.rowcount
    
    async def test_connection(self) -> dict[str, Any]:
        """Test database connectivity and return database info.
        
        Returns:
            Dictionary with database version and instance info.
        """
        query = """
        SELECT 
            banner AS version,
            instance_name,
            host_name,
            startup_time
        FROM v$version, v$instance
        WHERE ROWNUM = 1
        """
        
        try:
            result = await self.execute_query(query)
            return {
                "connected": True,
                "database_info": result[0] if result else {},
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }
    
    def get_oci_database_client(self) -> DatabaseClient:
        """Get OCI Database client for cloud operations.
        
        Returns:
            Configured OCI DatabaseClient instance.
        """
        if self._oci_client is None:
            settings = get_settings()
            oci_config = oci_from_file(
                file_location=str(settings.oci_config_path),
                profile_name=settings.oci_profile,
            )
            self._oci_client = DatabaseClient(oci_config)
        
        return self._oci_client


# Global connection manager instance
_connection_manager: Optional[OracleConnectionManager] = None


def get_connection_manager() -> OracleConnectionManager:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = OracleConnectionManager()
    return _connection_manager
