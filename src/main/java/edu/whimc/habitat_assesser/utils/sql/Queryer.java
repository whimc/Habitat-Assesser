package edu.whimc.habitat_assesser.utils.sql;

import edu.whimc.habitat_assesser.HabitatAssesser;
import edu.whimc.habitat_assesser.socket.AssessmentResponse;
import org.bukkit.Bukkit;
import org.bukkit.entity.Player;

import java.sql.*;

import java.util.function.Consumer;

/**
 * Handles storing agent data
 *
 * @author Sam
 */
public class Queryer {

    /**
     * Query for saving build assessment
     */
    private static final String QUERY_SAVE_BUILD_ASSESSMENT =
            "INSERT INTO whimc_build_assessment" +
                    "(uuid, username, world, x, y, z, time, feedback_high, feedback_low, area, communications_facilities," +
                    "food, gravity, health, oxygen_regulation, power_generation, radiation_protection, supplies, shape, transportation) " +
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
    private final HabitatAssesser plugin;
    private final MySQLConnection sqlConnection;

    public Queryer(HabitatAssesser plugin, Consumer<Queryer> callback) {
        this.plugin = plugin;
        this.sqlConnection = new MySQLConnection(plugin);

        Bukkit.getScheduler().runTaskAsynchronously(plugin, () -> {
            final boolean success = sqlConnection.initialize();
            Bukkit.getScheduler().runTask(plugin, () -> callback.accept(success ? this : null));
        });
    }

    /**
     * Generated a PreparedStatement for saving a new progress session.
     * @param connection MySQL Connection
     * @param assessmentResponse build assessment response
     * @return PreparedStatement
     * @throws SQLException
     */
    private PreparedStatement insertBuildAssessment(Connection connection, AssessmentResponse assessmentResponse) throws SQLException {
        PreparedStatement statement = connection.prepareStatement(QUERY_SAVE_BUILD_ASSESSMENT, Statement.RETURN_GENERATED_KEYS);
        Player player = Bukkit.getPlayer(assessmentResponse.getUser());
        statement.setString(1, player.getUniqueId().toString());
        statement.setString(2, assessmentResponse.getUser());
        statement.setString(3, player.getWorld().getName());
        statement.setDouble(4, player.getLocation().getX());
        statement.setDouble(5, player.getLocation().getY());
        statement.setDouble(6, player.getLocation().getZ());
        statement.setLong(7, System.currentTimeMillis());
        statement.setString(8, assessmentResponse.getHighestCategory());
        statement.setString(9, assessmentResponse.getLowestCategory());
        statement.setInt(10, assessmentResponse.getArea());
        statement.setInt(11, assessmentResponse.getCommunicationsFacilities());
        statement.setInt(12, assessmentResponse.getFood());
        statement.setInt(13, assessmentResponse.getGravity());
        statement.setInt(14, assessmentResponse.getHealth());
        statement.setInt(15, assessmentResponse.getOxygenRegulation());
        statement.setInt(16, assessmentResponse.getPowerGeneration());
        statement.setInt(17, assessmentResponse.getRadiationProtection());
        statement.setInt(18, assessmentResponse.getSupplies());
        statement.setInt(19, assessmentResponse.getShape());
        statement.setInt(20, assessmentResponse.getTransportation());
        return statement;
    }

    /**
     * Stores a progress command into the database and returns the obervation's ID
     * @param assessmentResponse agent assessment for their base
     * @param callback    Function to call once the observation has been saved
     */
    public void storeNewBuildAssessment(AssessmentResponse assessmentResponse, Consumer<Integer> callback) {
        async(() -> {

            try (Connection connection = this.sqlConnection.getConnection()) {
                try (PreparedStatement statement = insertBuildAssessment(connection, assessmentResponse)) {
                    statement.executeUpdate();

                    try (ResultSet idRes = statement.getGeneratedKeys()) {
                        idRes.next();
                        int id = idRes.getInt(1);

                        sync(callback, id);
                    }
                }
            } catch (SQLException e) {
                e.printStackTrace();
            }
        });
    }



    private <T> void sync(Consumer<T> cons, T val) {
        Bukkit.getScheduler().runTask(this.plugin, () -> cons.accept(val));
    }

    private void sync(Runnable runnable) {
        Bukkit.getScheduler().runTask(this.plugin, runnable);
    }

    private void async(Runnable runnable) {
        Bukkit.getScheduler().runTaskAsynchronously(this.plugin, runnable);
    }


}
