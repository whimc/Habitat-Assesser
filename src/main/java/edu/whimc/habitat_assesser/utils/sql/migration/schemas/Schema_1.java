package edu.whimc.habitat_assesser.utils.sql.migration.schemas;
import edu.whimc.habitat_assesser.utils.sql.migration.SchemaVersion;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

public class Schema_1 extends SchemaVersion {
    private static final String CREATE_TABLE =
            "CREATE TABLE IF NOT EXISTS `whimc_build_assessment` (" +
                    "  `rowid`       INT    AUTO_INCREMENT NOT NULL," +
                    "  `uuid`        VARCHAR(36)           NOT NULL," +
                    "  `username`    VARCHAR(16)           NOT NULL," +
                    "  `world`    VARCHAR(36)           NOT NULL," +
                    "  `x`           DOUBLE                NOT NULL," +
                    "  `y`           DOUBLE                NOT NULL," +
                    "  `z`           DOUBLE                NOT NULL," +
                    "  `time`    BIGINT           NOT NULL," +
                    "  `feedback_low`        VARCHAR(36)                NOT NULL," +
                    "  `feedback_high`    VARCHAR(36)           NOT NULL," +
                    "  `area`    INT           NOT NULL," +
                    "  `communications_facilities`    INT           NOT NULL," +
                    "  `food`    INT           NOT NULL," +
                    "  `gravity`    INT           NOT NULL," +
                    "  `health`    INT           NOT NULL," +
                    "  `oxygen_regulation`    INT           NOT NULL," +
                    "  `power_generation`    INT           NOT NULL," +
                    "  `radiation_protection`    INT           NOT NULL," +
                    "  `supplies`    INT           NOT NULL," +
                    "  `shape`    INT           NOT NULL," +
                    "  `transportation`    INT           NOT NULL," +
                    "  PRIMARY KEY    (`rowid`));";


    /**
     * Constructor to specify which migrations to do
     */
    public Schema_1() {
        super(1, null);
    }
    @Override
    protected void migrateRoutine(Connection connection) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(CREATE_TABLE)) {
            statement.execute();
        }

    }
}
