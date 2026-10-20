package com.callme.ai.core.database

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

/**
 * Manual position of a connection on the map.
 *
 * Coordinates are normalised to the ring radius (-1..1), so a layout arranged in
 * the studio panel keeps its shape on every screen size. Rows only exist for
 * nodes the user moved; everything else keeps the default ring.
 */
@Entity(tableName = "map_pins")
data class MapPinEntity(
    @PrimaryKey val entityId: String,
    val x: Float,
    val y: Float,
)

/** Manual map position, normalised to the ring radius. */
data class MapPinRow(val entityId: String, val x: Float, val y: Float)

@Dao
interface MapPinDao {

    @Query("SELECT * FROM map_pins")
    fun observePins(): Flow<List<MapPinEntity>>

    @Query("SELECT * FROM map_pins")
    suspend fun pins(): List<MapPinEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun put(pin: MapPinEntity)

    @Query("DELETE FROM map_pins WHERE entityId = :entityId")
    suspend fun remove(entityId: String)

    @Query("DELETE FROM map_pins")
    suspend fun clear()
}
