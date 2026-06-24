package db.migration;

import org.flywaydb.core.api.migration.BaseJavaMigration;
import org.flywaydb.core.api.migration.Context;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class V47__Backfill_app_user_username extends BaseJavaMigration {

    @Override
    public void migrate(Context context) throws Exception {
        Connection connection = context.getConnection();
        boolean mysql = connection.getMetaData().getDatabaseProductName().toLowerCase(Locale.ROOT).contains("mysql");

        if (!columnExists(connection, "username")) {
            execute(connection, "alter table app_users add column username varchar(20)");
        }

        List<UserRow> users = loadUsers(connection);
        backfillUsernames(connection, users);
        backfillDisplayNames(connection, users);

        if (mysql) {
            execute(connection, "alter table app_users modify username varchar(20) not null");
            execute(connection, "alter table app_users modify display_name varchar(20) not null");
            addUniqueConstraintIfMissing(connection, "uk_app_users_username", "username");
            addUniqueConstraintIfMissing(connection, "uk_app_users_display_name", "display_name");
        }
    }

    private static List<UserRow> loadUsers(Connection connection) throws SQLException {
        List<UserRow> users = new ArrayList<>();
        try (PreparedStatement statement = connection.prepareStatement(
                "select id, username, email, display_name from app_users order by created_at, id"
        );
             ResultSet resultSet = statement.executeQuery()) {
            while (resultSet.next()) {
                users.add(new UserRow(
                        resultSet.getString("id"),
                        resultSet.getString("username"),
                        resultSet.getString("email"),
                        resultSet.getString("display_name")
                ));
            }
        }
        return users;
    }

    private static void backfillUsernames(Connection connection, List<UserRow> users) throws SQLException {
        Set<String> used = new HashSet<>();
        for (UserRow user : users) {
            if (hasText(user.username())) {
                used.add(user.username().toLowerCase(Locale.ROOT));
            }
        }

        for (UserRow user : users) {
            if (hasText(user.username())) {
                continue;
            }
            String username = uniqueUsername(candidateUsername(user), user.id(), used);
            updateColumn(connection, user.id(), "username", username);
            used.add(username.toLowerCase(Locale.ROOT));
        }
    }

    private static void backfillDisplayNames(Connection connection, List<UserRow> users) throws SQLException {
        Set<String> used = new HashSet<>();
        for (UserRow user : users) {
            String normalized = trimToLength(user.displayName(), 20);
            String candidate = normalized;
            if (!used.add(candidate.toLowerCase(Locale.ROOT))) {
                candidate = uniqueDisplayName(candidate, user.id(), used);
                used.add(candidate.toLowerCase(Locale.ROOT));
            }
            if (!candidate.equals(user.displayName())) {
                updateColumn(connection, user.id(), "display_name", candidate);
            }
        }
    }

    private static String candidateUsername(UserRow user) {
        String localPart = user.email() == null ? "" : user.email().split("@", 2)[0];
        String normalized = localPart.replaceAll("[^A-Za-z0-9]", "").toLowerCase(Locale.ROOT);
        if (normalized.length() < 4) {
            normalized = "user" + compactId(user.id()).substring(0, 16);
        }
        return trimToLength(normalized, 20);
    }

    private static String uniqueUsername(String candidate, String id, Set<String> used) {
        String value = candidate;
        if (used.contains(value.toLowerCase(Locale.ROOT))) {
            value = trimToLength(candidate, 16) + compactId(id).substring(0, 4);
        }
        return trimToLength(value, 20);
    }

    private static String uniqueDisplayName(String candidate, String id, Set<String> used) {
        String value = trimToLength(candidate, 15) + "-" + compactId(id).substring(0, 4);
        while (used.contains(value.toLowerCase(Locale.ROOT))) {
            value = trimToLength(candidate, 14) + "-" + compactId(id).substring(0, 5);
        }
        return trimToLength(value, 20);
    }

    private static String trimToLength(String value, int maxLength) {
        String trimmed = value == null ? "" : value.trim();
        if (trimmed.length() <= maxLength) {
            return trimmed;
        }
        return trimmed.substring(0, maxLength);
    }

    private static boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static String compactId(String id) {
        String compact = id == null ? "" : id.replace("-", "").toLowerCase(Locale.ROOT);
        if (compact.length() >= 16) {
            return compact;
        }
        return (compact + "0000000000000000").substring(0, 16);
    }

    private static boolean columnExists(Connection connection, String columnName) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "select count(*) from information_schema.columns where lower(table_name) = 'app_users' and lower(column_name) = ?"
        )) {
            statement.setString(1, columnName.toLowerCase(Locale.ROOT));
            try (ResultSet resultSet = statement.executeQuery()) {
                resultSet.next();
                return resultSet.getInt(1) > 0;
            }
        }
    }

    private static boolean constraintExists(Connection connection, String constraintName) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "select count(*) from information_schema.table_constraints where lower(table_name) = 'app_users' and lower(constraint_name) = ?"
        )) {
            statement.setString(1, constraintName.toLowerCase(Locale.ROOT));
            try (ResultSet resultSet = statement.executeQuery()) {
                resultSet.next();
                return resultSet.getInt(1) > 0;
            }
        }
    }

    private static void addUniqueConstraintIfMissing(
            Connection connection,
            String constraintName,
            String columnName
    ) throws SQLException {
        if (!constraintExists(connection, constraintName)) {
            execute(
                    connection,
                    "alter table app_users add constraint " + constraintName + " unique (" + columnName + ")"
            );
        }
    }

    private static void updateColumn(Connection connection, String id, String columnName, String value) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "update app_users set " + columnName + " = ? where id = ?"
        )) {
            statement.setString(1, value);
            statement.setString(2, id);
            statement.executeUpdate();
        }
    }

    private static void execute(Connection connection, String sql) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.execute(sql);
        }
    }

    private record UserRow(String id, String username, String email, String displayName) {
    }
}
